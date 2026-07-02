# Spec: Unified Dark Workspace Redesign

## Objective

Rebuild the authenticated workspace UI so all post-auth pages share one coherent dark-mode design system while preserving the existing feature flows, API calls, navigation behavior, and page responsibilities.

The target experience is a professional financial research workspace: dense where data matters, calmer where learning or reading matters, and operational where admin tasks matter.

## Confirmed Scope

Apply the redesign to the full post-auth workspace:

- `global_terminal`, `news`, `news_economic_calendar`
- `guided_investing`, `financial_statement_simulator`, `assignments`
- `insights`
- `learning`
- `community`
- `pro_lab`, `backtest_studio`
- `content_ops_admin`, `community_moderation`, `pro_lab_admin`, `trust_safety_admin`, `analytics_admin`
- `onboarding` when reached as an authenticated workspace flow

Keep public/auth flows functionally intact:

- `auth_login`
- `auth_register`
- public `home` entry behavior

## Non-Goals

- Do not change backend behavior.
- Do not change authentication/session semantics.
- Do not rewrite data-fetching flows unless a visual refactor exposes a clear bug.
- Do not introduce Three.js/WebGL by default.
- Do not make marketing-style landing pages inside the workspace.
- Do not add heavy animation that competes with data reading.

## Design Direction

Name: **Midnight Trading Desk**

The interface should feel like a calm financial terminal and research lab:

- dark by default after authentication
- compact but readable
- chart/table friendly
- precise status and market colors
- restrained motion
- one coherent component language across all workspace pages

DFII score: **13/15**

- Aesthetic impact: 4
- Context fit: 5
- Implementation feasibility: 5
- Performance safety: 4
- Consistency risk: controlled through shared shell/tokens/primitives

## Design System Snapshot

### Color

Use the existing CSS custom property system as the foundation, but make dark mode the authenticated default.

Recommended palette direction:

- Base: near-black/navy workspace backgrounds
- Surface: layered dark panels with visible borders
- Primary action/trust: blue
- Finance/attention: amber
- Market movement: green/red
- Rare emphasis: violet

Avoid:

- one-note purple dashboards
- low-contrast gray text
- decorative gradient blobs
- hardcoded page-local colors that bypass tokens

### Typography

The app currently uses `Inter` and system fallbacks. For implementation safety, keep the current font stack initially, but tune the typographic rhythm:

- compact page titles
- tabular numerals for all market/stat/table values
- smaller section headings in dense panels
- no hero-scale typography inside dashboards

Future optional direction: evaluate `Fira Sans` / `Fira Code` for a stronger data-terminal feel.

### Spacing And Geometry

- Keep cards at `8px` or less unless existing components require otherwise.
- Use stable grid dimensions for charts, tables, metric strips, toolbars, and navigation.
- Prefer dense, organized workspace layouts over decorative card stacks.
- Mobile tables must use horizontal scroll wrappers or card transformations.
- Touch targets should be at least `44px`.

### Motion

Use motion sparingly:

- page entry: short panel stagger
- active nav indicator: quick slide
- data refresh: subtle opacity/translate update
- hover/focus: color, border, and shadow changes only

Rules:

- use transform/opacity only
- 150-300ms for UI interactions
- no infinite decorative motion
- respect `prefers-reduced-motion`

Anime.js can be used later for bespoke staggered page choreography, but the first implementation should remain CSS-first unless the existing stack already includes the dependency.

## Architecture

### Layer 1: Shell And Theme

Files:

- `frontend/src/app/AppShell.jsx`
- `frontend/src/app/NavBar.jsx`
- `frontend/src/shared/navigation/ConnectedWorkspaceNav.jsx`
- `frontend/src/styles/tokens.css`
- `frontend/src/styles/base-elements.css`
- `frontend/src/styles/app-shell.css`

Responsibilities:

- authenticated workspace defaults to `data-theme="dark"`
- shell gives every workspace page the same background, nav density, content width, and transition behavior
- public/auth surfaces can stay visually separate
- navigation remains functionally identical

### Layer 2: Shared Workspace Primitives

Create shared CSS primitives, preferably in a new imported stylesheet such as:

- `frontend/src/styles/workspace-primitives.css`

Core classes:

- `workspace-page`
- `workspace-header`
- `workspace-kicker`
- `workspace-title`
- `workspace-subtitle`
- `workspace-grid`
- `workspace-card`
- `workspace-panel`
- `workspace-toolbar`
- `workspace-table-wrap`
- `workspace-metric-strip`
- `workspace-metric`
- `workspace-status-chip`
- `workspace-chart-shell`
- `workspace-empty-state`
- `workspace-loading-state`
- `workspace-error-state`

The primitives should reduce duplicated page CSS while allowing page-specific workbench layouts.

### Layer 3: Page Workbenches

Each page group keeps its own feature flow but adopts the shared primitives.

#### Global Terminal / News

Dense terminal layout:

- top market/action rail
- market summary strip
- chart-first panels
- watchlist/news/calendar modules
- mobile-safe data tables

Visual priority: numbers, charts, and live context.

#### Insights

Research desk layout:

- readable main research column
- supporting evidence/sidebar
- compact insight summaries
- calm density, less terminal-like than charts pages

Visual priority: reading, comparing, and tracing rationale.

#### Guided Investing

Step-based analysis workbench:

- progress zones
- checklist/cards
- BCTC analysis modules
- obvious next-action surfaces

Visual priority: guided decision flow.

#### Learning

Academy cockpit:

- continue-learning surface
- paths/modules
- lesson focus
- practice/review actions
- admin entry visually separated

Visual priority: learner orientation and momentum.

#### Pro Lab / Backtest Studio

Research cockpit:

- experiment/session/blueprint panels
- metric strips
- validation results
- journal/report workspace
- high-density technical controls

Visual priority: experiment iteration and result confidence.

#### Community

Dark discussion workspace:

- space selector
- discussion cards
- contribution CTA
- moderation entry

Visual priority: human conversation without social-feed noise.

#### Admin

Operational console:

- dense tables
- filters
- action bars
- bulk action affordances when available
- clear warning/danger states

Visual priority: scanning, triage, and repeat operations.

## Accessibility And Responsiveness

Requirements:

- normal text contrast at least 4.5:1
- visible focus states
- icon-only buttons require `aria-label`
- no horizontal viewport overflow on mobile
- tables wrap in scroll containers or switch to cards
- reserve layout space for async content
- respect reduced motion

Viewport checks:

- 375px
- 768px
- 1024px
- 1440px

## Performance

- Avoid adding dependencies unless the payoff is clear.
- Keep page transitions light.
- Do not render large invisible DOM lists.
- Consider virtualization for long lists over 100 rows/items if performance becomes a measured problem.
- Do not add autoplay media loops.

## Implementation Plan

1. Update theme behavior so all authenticated workspace views use dark mode by default.
2. Add shared workspace primitives stylesheet and import it from `frontend/src/index.css`.
3. Refine app shell and connected navigation for a compact dark workspace.
4. Update page group CSS incrementally:
   - global terminal/news
   - pro lab/backtest studio
   - insights/guided investing
   - learning/community
   - admin pages
5. Run build/lint.
6. Start dev server and visually inspect representative routes.

## Testing Strategy

Automated:

- `cd frontend && npm run build`
- `cd frontend && npm run lint`

Manual:

- login flow still routes to the same authenticated landing
- each post-auth route renders without breaking feature controls
- nav active state remains correct
- no mobile horizontal page overflow
- charts/tables keep readable dimensions
- admin actions remain discoverable
- reduced motion path is acceptable

## Decision Log

1. Scope is the full authenticated workspace.
   - Alternative: only redesign a few priority pages.
   - Reason: user requested the entire workspace, with feature flows preserved.

2. Use a unified shell plus page-specific workbenches.
   - Alternative: redesign every page independently.
   - Reason: this keeps consistency and lowers maintenance risk.

3. Dark mode becomes the default authenticated experience.
   - Alternative: keep mixed light/dark per route.
   - Reason: mixed route themes are the main consistency problem.

4. Preserve existing feature flows.
   - Alternative: rewrite page flows while redesigning.
   - Reason: the request is UI/UX rebuilding, not product behavior changes.

5. Do not use Three.js by default.
   - Alternative: add 3D visual effects to the workspace.
   - Reason: 3D is not needed for the current dashboard/workbench task and could reduce performance/readability.

6. Use restrained motion.
   - Alternative: heavily animated workspace.
   - Reason: financial data interfaces need calm, fast feedback.

## Open Risks

- Existing page CSS is spread across many files, so style conflicts are likely.
- Some components may hardcode colors instead of tokens.
- Admin pages may need extra table/form polish after first pass.
- Full visual validation will require running the app and checking multiple routes.

## Exit Criteria

- Authenticated workspace pages share one dark theme.
- Major workspace page groups use compatible spacing, typography, and surface patterns.
- Feature flows remain intact.
- Build passes.
- Lint either passes or any pre-existing lint issues are clearly reported.
- Manual visual inspection covers representative routes.
