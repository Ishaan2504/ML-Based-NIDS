# NIDS Security Operations frontend

This folder contains the React and TypeScript frontend for the dashboard described in `../NIDS Technical Specification (Agent Build Guide).pdf`. The API status and active-model chip read from the local FastAPI `/health` and `/model/info` endpoints. Dashboard analytics remain empty until the data pipeline produces run and report artifacts.

## Stack and structure

- Vite + React + TypeScript
- Tailwind CSS 4 via the Vite plugin
- shadcn-compatible aliases and component layout (`src/components/ui`)
- Components: `src/components/ui`
- Global styles and Tailwind imports: `src/index.css`
- `components.json` records the shadcn CLI aliases and style configuration.

If extending an existing shadcn project, `src/components/ui` is the configured component destination. Keeping reusable primitives there lets the shadcn CLI and imports resolve generated components consistently.

## Run locally

Requires Node.js 20.19+ or 22.12+.

```powershell
cd frontend
npm install
npm run dev
```

For a full shadcn CLI-managed setup, initialize with `npx shadcn@latest init` and choose the existing `src/index.css`, `@/components`, `@/components/ui`, and `@/lib/utils` aliases. This scaffold already includes the matching configuration and Tailwind 4 integration.

## Frontend notes

The six navigation destinations follow the product spec: Security Overview, Threat Alerts, Traffic Investigation, Network Activity, Model Performance, and Traffic Analysis Lab. The overview and empty states are implemented; the other pages have their themed starting layouts. The dashboard labels the environment as offline, avoids implying live monitoring, and uses `Not yet generated. Run the pipeline.` instead of invented results. The interface uses a black grid and phosphor-green terminal theme based on the supplied reference.

The frontend checks API readiness on load and every 15 seconds. Set `VITE_API_URL` at build time to change the API address; it defaults to `http://127.0.0.1:8000`. An online API does not mean a model is available: the API can report `degraded` until a verified bundle is installed.

The technical specification describes Streamlit. This project keeps the React dashboard and mirrors the specified dashboard theme and content rules. The API status/model metadata are connected; prediction, saved-run, and report views remain future work until the inference pipeline and storage are implemented.
