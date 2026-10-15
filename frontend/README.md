# NIDS Security Operations frontend

This folder contains the React and TypeScript frontend for the dashboard described in `../NIDS Technical Specification (Agent Build Guide).pdf`. It is a frontend-only implementation; the specification's API and pipeline are not implemented here. Counts, metrics, model IDs, and alerts are deliberately empty until generated run artifacts exist.

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

The technical specification describes a Streamlit dashboard. This React scaffold follows the requested React component integration and mirrors the specified dashboard theme and content rules; connecting the screens to the specified FastAPI service and generated report/run files remains future work.
