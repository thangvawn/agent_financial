"""Authenticated owner resolution and conservative recovery of legacy session-owned data."""
from hashlib import sha256
from fastapi import Header, HTTPException, Query, Request
from risk_dashboard.modules.auth.application.dependencies import resolve_principal
from risk_dashboard.modules.auth.schemas.principal import AuthPrincipal
from risk_dashboard.modules.market_portfolio.domain.entities import STARTING_CASH
from risk_dashboard.platform.database import open_app_state_db


def legacy_portfolios(account_id: str) -> list[dict]:
    with open_app_state_db() as conn:
        sessions = conn.execute('SELECT session_id, created_at FROM account_sessions WHERE account_id = ?', (account_id,)).fetchall()
        result = []
        for session in sessions:
            sid = session['session_id']
            positions = [dict(row) for row in conn.execute('SELECT symbol, quantity, avg_cost FROM mp_holdings WHERE user_id = ?', (sid,))]
            orders = [dict(row) for row in conn.execute('SELECT symbol, side, quantity, status, filled_price, created_at FROM mp_orders WHERE user_id = ? ORDER BY created_at', (sid,))]
            account = conn.execute('SELECT cash_balance FROM mp_paper_accounts WHERE user_id = ?', (sid,)).fetchone()
            if positions or orders or (account and account['cash_balance'] != STARTING_CASH):
                result.append({'reference': sha256(sid.encode()).hexdigest()[:16], 'created_at': session['created_at'],
                               'cash_balance': account['cash_balance'] if account else STARTING_CASH,
                               'positions': positions, 'orders': orders})
        return result


def recover_legacy_data(account_id: str) -> None:
    with open_app_state_db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        sessions = [r['session_id'] for r in conn.execute('SELECT session_id FROM account_sessions WHERE account_id = ?', (account_id,))]
        portfolios = []
        for sid in sessions:
            for item in conn.execute('SELECT * FROM mp_watchlist_items WHERE user_id = ?', (sid,)).fetchall():
                exists = conn.execute('SELECT 1 FROM mp_watchlist_items WHERE user_id = ? AND symbol = ?', (account_id, item['symbol'])).fetchone()
                if exists:
                    conn.execute('DELETE FROM mp_watchlist_items WHERE item_id = ?', (item['item_id'],))
                else:
                    conn.execute('UPDATE mp_watchlist_items SET user_id = ? WHERE item_id = ?', (account_id, item['item_id']))
            active = any(conn.execute(f'SELECT 1 FROM {table} WHERE user_id = ? LIMIT 1', (sid,)).fetchone() for table in ('mp_orders','mp_holdings'))
            cash = conn.execute('SELECT cash_balance FROM mp_paper_accounts WHERE user_id = ?', (sid,)).fetchone()
            if active or (cash and cash['cash_balance'] != STARTING_CASH):
                portfolios.append(sid)
        active = any(conn.execute(f'SELECT 1 FROM {table} WHERE user_id = ? LIMIT 1', (account_id,)).fetchone() for table in ('mp_orders','mp_holdings'))
        cash = conn.execute('SELECT cash_balance FROM mp_paper_accounts WHERE user_id = ?', (account_id,)).fetchone()
        active = active or (cash and cash['cash_balance'] != STARTING_CASH)
        # Independent portfolios each had their own starting capital. Never merge them silently.
        if not active and len(portfolios) == 1:
            sid = portfolios[0]
            conn.execute('DELETE FROM mp_paper_accounts WHERE user_id = ?', (account_id,))
            for table in ('mp_paper_accounts','mp_holdings','mp_orders'):
                conn.execute(f'UPDATE {table} SET user_id = ? WHERE user_id = ?', (account_id, sid))


async def resolve_market_principal(request: Request, authorization: str | None = Header(default=None),
                                   session_id: str | None = Query(default=None)) -> AuthPrincipal:
    if authorization is None:
        if not session_id and request.method == 'POST':
            try:
                body = await request.json()
                session_id = body.get('session_id') if isinstance(body, dict) else None
            except (ValueError, TypeError):
                session_id = None
        if not isinstance(session_id, str):
            raise HTTPException(status_code=401, detail='Vui lòng đăng nhập để dùng danh mục cá nhân.')
        authorization = f'Bearer {session_id}'
    principal = resolve_principal(authorization=authorization)
    recover_legacy_data(principal.account_id)
    return principal
