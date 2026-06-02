# DocQA Assistant — React Frontend

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Prerequisites

- Node.js 20+
- Backend running at http://localhost:8001

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server on port 3000 |
| `npm run build` | Production build to dist/ |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run format` | Format with Prettier |

## Architecture

Three-panel layout: Documents (left) | Chat (center) | Citations (right)

### Key Technologies
- React 19 + TypeScript
- Vite 6 (build tool)
- Tailwind CSS v4 (styling)
- TanStack Query v5 (server state)
- Zustand (client state)
- Axios (HTTP client)
