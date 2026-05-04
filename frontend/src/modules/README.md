Module ownership:

- `pages/` renders route-level screens.
- `modules/` owns domain logic, APIs, hooks, schemas, analytics, and reusable domain components.
- `shared/` holds cross-domain UI and helpers.

Import from each module root when wiring pages, for example:

- `../../modules/home-onboarding`
- `../../modules/learning`
- `../../modules/pro-lab`

This keeps route components thin and makes future file moves safer.
