# Spec: Dark Mode & Unified Layout (Post-Auth Pages)

## Objective

Tạo dark mode mặc định cho toàn bộ app sau khi đăng nhập, với toggle switch để user chuyển sang light mode.
Đồng thời điều chỉnh layout (flex/grid) của các pages sau Auth để thống nhất, phù hợp với app giáo dục tài chính.

Auth page (login/register) giữ nguyên light mode.

## Phạm vi (Scope)

**Pages áp dụng dark mode + layout unification:**
- `pages/home-onboarding/` — HomePage, OnboardingPage, MarketOverviewPage
- `pages/learning/` — LearningHomePage, EducationPlatformPage
- `pages/guided-investing/` — GuidedInvestingPage
- `pages/insights/` — InsightsPage
- `pages/community/` — CommunityPage
- `pages/global-terminal/` — GlobalTerminalPage, NewsPage, NewsEconCalendarPage
- `pages/pro-lab/` — ProLabPage và sub-pages

**Không thay đổi:**
- `pages/auth/` — giữ nguyên light mode
- `pages/admin/` — admin pages giữ nguyên
- Backend code

## Tech Stack

- React 18 + Vite
- CSS custom properties (tokens.css) — cơ chế dark mode đã có sẵn via `data-theme="dark"`
- localStorage để persist user preference
- Không thêm library mới

## Cơ chế Dark Mode

Dark mode hoạt động qua `data-theme="dark"` attribute trên `.app-shell` div (AppShell.jsx dòng 494).

Hiện tại `DARK_THEME_VIEWS` trong AppShell hardcode list views có dark theme:
```js
const DARK_THEME_VIEWS = new Set([
  'global_terminal', 'pro_lab', 'backtest_studio',
  'news', 'news_economic_calendar',
  'financial_statement_simulator', 'assignments',
])
```

**Thay đổi:** Bỏ hardcode list → dùng user preference từ localStorage.
Logic: `themeAttr = userPrefersDark ? 'dark' : 'light'`
Exception: auth views luôn `light`.

## Commands

```bash
# Dev
cd frontend && npm run dev

# Build & verify
cd frontend && npm run build

# Lint
cd frontend && npm run lint
```

## Project Structure

Files sẽ thay đổi:

```
frontend/src/
├── app/
│   ├── AppShell.jsx            ← Thêm theme state + toggle, bỏ DARK_THEME_VIEWS hardcode
│   └── NavBar.jsx              ← Thêm ThemeToggle button
├── shared/
│   ├── theme/                  ← NEW package
│   │   ├── useTheme.js         ← Hook: get/set/persist dark|light preference
│   │   └── ThemeToggle.jsx     ← Button toggle icon (sun/moon)
├── styles/
│   └── tokens.css              ← Không đổi (dark tokens đã có)
├── pages/
│   ├── home-onboarding/home.css      ← Đảm bảo dùng CSS vars, không hardcode màu
│   ├── learning/learning.css         ← Như trên
│   ├── guided-investing/guided-investing.css ← Như trên
│   ├── insights/insights.css         ← Như trên
│   ├── community/community.css       ← Như trên
│   └── [các CSS còn lại]
```

## Code Style

```jsx
// useTheme.js — đơn giản, không over-engineer
const STORAGE_KEY = 'nf.theme'
const DEFAULT = 'dark'  // app mặc định dark sau login

export function useTheme() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem(STORAGE_KEY) || DEFAULT
  )
  const toggle = useCallback(() => {
    setTheme(t => {
      const next = t === 'dark' ? 'light' : 'dark'
      localStorage.setItem(STORAGE_KEY, next)
      return next
    })
  }, [])
  return { theme, toggle, isDark: theme === 'dark' }
}
```

```jsx
// ThemeToggle.jsx — icon-only button, accessible
export function ThemeToggle({ isDark, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={isDark ? 'Chuyển sang light mode' : 'Chuyển sang dark mode'}
      className="theme-toggle-btn"
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  )
}
```

**Conventions:**
- CSS vars từ `tokens.css` cho màu, không hardcode hex trong component CSS
- Không dùng Tailwind inline classes cho màu (ảnh hưởng dark mode)
- `data-theme` chỉ set trên `.app-shell` root — cascade xuống toàn bộ DOM

## Testing Strategy

Manual testing (không có test framework cho UI hiện tại):
1. Login → app mặc định dark
2. Toggle → chuyển light, reload → vẫn light (persist)
3. Logout, login lại → vẫn nhớ preference
4. Auth page (login/register) → luôn light dù preference là dark
5. Mỗi page sau Auth: text readable, contrast đủ, không có màu hardcode bị vỡ

## Boundaries

**Always:**
- Dùng CSS custom properties từ `tokens.css` (`--bg`, `--surface`, `--ink`, `--accent`, v.v.)
- Auth views (`auth_login`, `auth_register`) luôn `data-theme="light"`
- Persist preference vào localStorage với key `nf.theme`
- Default dark cho user mới (chưa có preference)

**Ask first:**
- Thay đổi màu accent (hiện `--accent: #2563eb` light / `#3b82f6` dark)
- Thêm custom dark palette ngoài tokens.css
- Redesign layout của bất kỳ page cụ thể nào (spec này chỉ fix CSS vars, không redesign)

**Never:**
- Hardcode màu hex trong component CSS mới
- Dùng `!important` để override dark mode (ngoại trừ reset hiện có)
- Thêm dark mode library (prefers-color-scheme listener đủ dùng qua tokens)
- Thay đổi auth page layout

## Layout Unification

Các page CSS hiện tại có một số hardcode màu hex thay vì CSS vars. Task sẽ audit và fix.

**Unified surface pattern cho edu-finance pages:**
```css
/* Mọi page container nên dùng pattern này */
.page-surface {
  background: var(--bg);
  color: var(--ink);
  min-height: 100%;
}

.page-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.page-section-alt {
  background: var(--surface-alt);
  border-radius: var(--radius-lg);
}
```

## Success Criteria

- [ ] Sau login: app mặc định dark mode
- [ ] NavBar có ThemeToggle button (sun/moon icon)
- [ ] Toggle chuyển dark ↔ light, persist qua reload và logout/login
- [ ] Auth page luôn light
- [ ] Không có màu hardcode hex nào bị vỡ trong dark mode (contrast đọc được)
- [ ] Build không có error/warning mới
- [ ] Pro Lab và Global Terminal vẫn dark (consistent với trước)

## Open Questions

1. Font chữ heading trong edu pages: Inter hiện tại hay đổi sang serif nhẹ (ví dụ Lora) để trông "học thuật" hơn? → **Giữ Inter cho MVP, hỏi lại sau**
2. Accent color trong dark mode (`#3b82f6` blue) hay đổi sang màu khác phù hợp tài chính hơn (ví dụ teal `#14b8a6`)? → **Giữ blue, hỏi lại sau**
3. Admin pages có cần dark mode không? → **Không trong scope này**
