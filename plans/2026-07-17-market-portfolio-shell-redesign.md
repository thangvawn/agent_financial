# Market & Portfolio — Institutional Desk Prototype

## Goal
Replace the rejected generic education shell on Market & Portfolio with one compact, dark financial workspace that can be approved before redesigning other modules.

## Scope
- Edit `MarketPortfolioPage.jsx`
- Edit `market-portfolio-panels.css`
- Preserve APIs, state, tab ids, session behavior, and `GlobalTerminalPage`
- Do not change Home or any other product module

## Direction
- Institutional research desk
- Dense but calm; dark neutral surfaces with restrained teal
- Typography and alignment provide hierarchy, not stacked cards or decoration
- Education-first guidance appears once as a compact practice brief
- Simulation status is persistent and explicit

## Implementation
1. Remove `ProductModuleShell` and its three-column learning callout from this route.
2. Add a module masthead with product identity, concise purpose, and simulation status.
3. Render four keyboard-accessible workspace tabs with short contextual descriptions.
4. Add one compact active-tab practice brief.
5. Scope all visual rules under `.mp-desk`; reuse existing design tokens.
6. Keep child market, watchlist, order, and portfolio behavior unchanged.

## Acceptance
- Desktop: clear masthead, one tab row, one guidance row, uninterrupted data workspace.
- Mobile: title and status stack cleanly; tabs scroll horizontally; no card grid.
- No light/dark seam around `GlobalTerminalPage`.
- Build and lint pass.
- Validate `/dashboard-static/markets` visually at desktop and mobile widths.

## Risk
The existing Global Terminal owns a large internal stylesheet. Validate the boundary between it and the new shell rather than rewriting terminal internals in this prototype.
