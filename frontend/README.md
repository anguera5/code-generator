# Frontend - Multi-Module Workspace (Vue 3 + Vite + Vuetify)

This frontend now supports hosting multiple self-contained mini-app modules ("projects") under a single shell UI with a collapsible navigation drawer.

Current modules:
1. Code Generator (`/code-generator`): Generate code, tests, and docs via LLM backend.

## Dev
1. `npm ci`
2. `npm run dev`

The dev server proxies `/api` to `http://backend:8000` in Docker. If running backend locally, change `vite.config.ts` proxy target to `http://localhost:8000`.

## Add a New Module
1. Create a folder: `src/modules/<your-module>/`
2. Add a root component file inside, e.g. `MyModuleApp.vue`.
3. Register a lazy route in `src/router.ts` (copy the code-generator pattern).
4. Add metadata in `src/modules/index.ts` to appear in the drawer & landing page.

Example snippet:
```ts
// router.ts
const MyModuleApp = () => import('./modules/my-module/MyModuleApp.vue')
routes.push({ path: '/my-module', name: 'my-module', component: MyModuleApp })

// modules/index.ts
modules.push({ path: '/my-module', title: 'My Module', description: 'Does something cool.' })
```

That's it—hot reload will expose the new module.

## Structure Overview
| Path | Purpose |
|------|---------|
| `src/App.vue` | Shell layout (drawer, app bar, `<router-view/>`). |
| `src/pages/HomePage.vue` | Landing page (lists modules). |
| `src/modules/` | Each subfolder = independent mini app. |
| `src/modules/index.ts` | Registry of module metadata. |
| `src/router.ts` | Central router with lazy-loaded module routes. |

## Notes
* Keep cross-module shared utilities in a neutral folder (e.g. `src/lib/`).
* Avoid tight coupling: modules should not import each other's internals directly.
* If you need global state, introduce Pinia stores under `src/stores/` (already dependency-installed).

## Future Ideas
* Dynamic auto-discovery of modules (Vite `import.meta.glob`).
* Per-module settings dialog.
* Breadcrumb & search across modules.

Happy hacking!
## Timeouts
- The frontend HTTP client defaults to no timeout. To set a custom timeout (ms), export `VITE_HTTP_TIMEOUT`:

```bash
export VITE_HTTP_TIMEOUT=60000
npm run dev
```
