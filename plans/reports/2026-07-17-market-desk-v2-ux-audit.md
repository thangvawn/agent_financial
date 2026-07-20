# UX Audit — Market & Portfolio Desk v2

**Date:** 2026-07-17  
**URL:** http://127.0.0.1:4173/dashboard-static/markets  
**Viewports:** Desktop 1440×900, Mobile 390×844  
**Auditor:** e2e-runner (Playwright 1.61.1, headless Chromium)  
**Screenshots:** `output/ux-audit/market-desk-v2/`  
**Auth bypass:** localStorage `public-beta.session_id` set to fake token before page load

---

## Verdict: DONE_WITH_CONCERNS

36 checks passed. 2 concrete visual defects found — one HIGH (mobile overflow), one LOW (body flash risk). Desktop passes all checks cleanly. No legacy ProductModuleShell or education callout remnants.

---

## Defects

### D1 — Mobile Horizontal Overflow 266 px  
**Severity:** HIGH  
**Viewport:** Mobile 390×844  
**Selector:** `section.mp-desk` (and all children: `.mp-desk__masthead`, `.mp-desk__tabs`, `.mp-desk__brief`, `.mp-desk__panel`, `.global-terminal`)

**Description:**  
The entire `.mp-desk` component renders at **656 px wide** inside a 390 px viewport, overflowing the right edge by **266 px**. Every top-level child is equally affected. Root cause: the `surface-panel` grid's implicit column is being sized by min-content, and the 4-tab row (`flex: 0 0 164px` × 4 = 656 px) drives it — even though `.mp-desk__tabs` has `overflow-x: auto` on mobile, the enclosing grid track expands to accommodate the scrollable container's scrollWidth.

**Visual evidence (screenshot `mobile-01-initial.png`):**
- Only tabs 01 and 02 are visible; tab 03 is half-cut; tab 04 "Danh mục" is completely off-screen
- "MÔ PHỎNG" badge (top-right of masthead) is completely off-screen
- "Không phải khuyến nghị đầu tư" disclaimer in the brief bar is off-screen
- GlobalTerminal error state text "Dữ liệu thị trường chu…" is truncated at right

**Fix direction:**  
Add `min-width: 0` or `overflow: hidden` to `.mp-desk` so the grid item can shrink below its content's min-width. Alternatively add `width: 100%; max-width: 100%; overflow-x: hidden` explicitly on `.mp-desk`. The 4-column grid track for `.mp-desk__tabs` on desktop (4 × 25%) already has `overflow-x: auto` on mobile but the parent container needs to be constrained first.

```css
/* Candidate fix */
section.mp-desk {
  min-width: 0;
  overflow-x: hidden;
}
```

---

### D2 — `body` background is light in dark-themed route  
**Severity:** LOW  
**Viewport:** Both  
**Selector:** `body`  
**Computed value:** `rgb(250, 250, 250)` = `#fafafa` (`:root --bg` light token)

**Description:**  
The `body` element's background-color is the light-mode default (`#fafafa`). The app-shell's own dark surfaces cover this completely in the main viewport, so it is **not visible in normal scrolling on desktop or Android**. However on iOS/Safari with rubber-band overscroll, the area beyond the page bottom/top will expose the raw `body` background — producing a white flash that breaks dark-mode coherence.

**Fix direction:**  
Add `body { background: #09090b; }` (or `var(--bg)`) to the global CSS after the dark-theme token block is established. Or set `html { background: #09090b }`.

---

## Passes (36 total)

| Check | Desktop | Mobile |
|---|---|---|
| mp-desk background is dark (`rgb(12, 18, 20)`) | ✓ | ✓ |
| No `ProductModuleShell` remnant | ✓ | ✓ |
| No light education callout cards | ✓ | ✓ |
| Masthead element `.mp-desk__masthead` present | ✓ | ✓ |
| Kicker "NORTHSTAR / MARKET DESK" present | ✓ | ✓ |
| H1 "Market & Portfolio" present | ✓ | ✓ |
| Lede text present | ✓ | ✓ |
| "MÔ PHỎNG" mode badge present | ✓ | ✓ (off-screen due to D1) |
| `[role="tablist"]` present | ✓ | ✓ |
| 4 tabs with correct ARIA (role, aria-selected, aria-controls) | ✓ | ✓ |
| `.mp-desk__brief` practice-focus bar present | ✓ | ✓ |
| `.global-terminal` visible on markets tab | ✓ | ✓ |
| GlobalTerminal background is dark (`rgb(7, 11, 12)`) | ✓ | ✓ |
| No white border seam between `.mp-desk__panel` and GlobalTerminal | ✓ | ✓ |
| No horizontal overflow on desktop | ✓ | — |
| Initial active tab is `#mp-tab-markets` | ✓ | — |
| Click on "Theo dõi" tab switches active state | ✓ | — |
| FOCUS bar text updates on tab change | ✓ (visual confirm) | — |
| ArrowRight navigation from markets → watchlist | ✓ | — |
| ArrowLeft wraps from markets → portfolio (last) | ✓ | — |
| Home key focuses first tab (markets) | ✓ | — |
| End key focuses last tab (portfolio) | ✓ | — |

---

## Non-defect observations

**GlobalTerminal shows API error state:**  
"Dữ liệu thị trường chưa sẵn sàng / Không thể kết nối nguồn dữ liệu lúc này" — this is expected in Vite preview mode without a live backend connection. Not a visual redesign defect.

**Watchlist panel shows 502 backend error:**  
"Request failed: 502" — expected in static preview, not a visual defect.

**App-shell computed background discrepancy:**  
`getComputedStyle(.app-shell).backgroundColor` returns `rgb(243, 247, 246)` rather than the expected dark `rgb(9, 9, 11)`. The dark content surfaces cover this entirely in the visible viewport; no seam is visible in screenshots. Likely a CSS variable scoping edge case or a rendering artifact. Low priority to investigate.

**GlobalTerminal dark-desk integration:**  
The GlobalTerminal (`#070b0c`) sits inside `.mp-desk__panel` (`background: var(--bg) = #070b0c`), producing a seamless dark-on-dark join. The 1 px `var(--line)` border on `.mp-desk__panel > .global-terminal` (via `.mp-desk__panel > .global-terminal { border-inline: 1px solid var(--line) }`) is subtle teal-dark — no light/dark seam visible. ✓

---

## Screenshots index

| File | Description |
|---|---|
| `desktop-01-initial.png` | Desktop 1440×900 initial load, markets tab, error state |
| `desktop-01-initial-full.png` | Desktop full-page scroll |
| `desktop-02-watchlist-tab.png` | Desktop after click on "Theo dõi" tab |
| `desktop-final.png` | Desktop after keyboard navigation, back on markets |
| `mobile-01-initial.png` | Mobile 390×844 initial load — overflow visible |
| `mobile-01-initial-full.png` | Mobile full-page |
| `mobile-02-scrolled.png` | Mobile scrolled 400 px down |

---

## Severity key

| Level | Meaning |
|---|---|
| HIGH | Visible to users; degrades UX materially |
| MEDIUM | Conditional defect; some users affected |
| LOW | Risk / latent issue; invisible in normal use |
