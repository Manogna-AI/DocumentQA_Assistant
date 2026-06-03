# DocQA Assistant Frontend

Professional React workspace for querying uploaded documents with grounded, citation-first answers. The frontend pairs a document list, chat surface, and citation inspector with the FastAPI DocQA backend.

## Highlights

- **Three-panel AI workspace**: documents on the left, chat in the center, citations on the right.
- **Responsive viewport-safe layout** with independent scrolling for documents, answers, and citations.
- **Upload workflow** for PDF, DOCX, and PPTX files with client-side size/type validation.
- **Grounded chat UX** with loading states, markdown rendering, citation pills, and source excerpts.
- **Operational visibility** through API/Ollama health indicators and user-friendly toast errors.
- **Modern frontend stack** using React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, Zustand, Axios, and Vitest.

## Prerequisites

- Node.js 20+
- npm 10+
- Backend running at `http://localhost:8001` unless overridden with `VITE_API_BASE_URL`

## Configuration

Create `frontend/.env.local` when the backend is not running on the default URL:

```env
VITE_API_BASE_URL=http://localhost:8001
```

Runtime constants such as HTTP timeouts, polling intervals, message preview length, and input limits live in `src/config/frontend.config.ts`.

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>.

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the Vite development server on port 3000. |
| `npm run build` | Run TypeScript project checks and create a production build in `dist/`. |
| `npm run preview` | Preview the production build locally. |
| `npm run typecheck` | Run TypeScript without emitting files. |
| `npm run test:run` | Execute the Vitest test suite once. |
| `npm run test` | Run Vitest in watch mode. |
| `npm run test:coverage` | Generate coverage reports. |
| `npm run format` | Format frontend source files with Prettier. |
| `npm run lint` | Run ESLint, if an ESLint configuration is present. |

## Application Structure

| Path | Purpose |
| --- | --- |
| `src/App.tsx` | Viewport shell and three-panel layout. |
| `src/components/Chat/` | Chat panel, message bubbles, input, and loading indicator. |
| `src/components/Documents/` | Document list and document cards. |
| `src/components/Citations/` | Citation inspector and excerpt cards. |
| `src/components/Layout/` | Header and status bar. |
| `src/hooks/` | TanStack Query and chat orchestration hooks. |
| `src/services/` | Axios API client and backend service wrappers. |
| `src/stores/` | Zustand application state. |
| `src/types/` | Shared TypeScript response and UI types. |
| `src/__tests__/` | Vitest + React Testing Library coverage. |

## UX Notes

- The chat, document list, and citation inspector are intentionally separate scroll containers so long answers do not push the input box or status bar off-screen.
- Long markdown tokens, URLs, code fragments, and citation snippets wrap safely to prevent horizontal overflow.
- The upload picker accepts PDF, DOCX, and PPTX by MIME type or extension because some browsers/operating systems provide an empty MIME type for local files.
- The frontend uses long API timeouts to accommodate slower local Ollama models. The health check remains short so the status bar updates quickly.

## Development Workflow

1. Start Ollama and the FastAPI backend.
2. Run `npm run dev` from `frontend/`.
3. Upload a supported document.
4. Ask a focused question or request a summary.
5. Click citation pills to populate the citation inspector.

## Troubleshooting

### Cannot connect to backend

- Confirm the backend is running on `http://localhost:8001`.
- If using a different URL, set `VITE_API_BASE_URL` in `frontend/.env.local`.
- Check the status bar for API and Ollama availability.

### Answers are slow

Local Ollama generation can take several minutes depending on the model and hardware. Try a smaller model, ask a narrower question, or reduce retrieval settings in the backend.

### Uploaded file is rejected

Supported extensions are `.pdf`, `.docx`, and `.pptx`; the default size limit is 50 MB. Backend limits must also allow the selected file.

### The answer area does not scroll

The production layout uses `h-dvh`, `min-h-0`, and dedicated `overflow-y-auto` containers. If a custom wrapper is added, ensure every flex/grid ancestor of the scroll area can shrink (`min-h-0`) and that only the intended panel owns vertical scrolling.

## Production Checklist

- [ ] Restrict CORS to deployed frontend origins.
- [ ] Add authentication and user-specific routing before exposing uploads publicly.
- [ ] Configure error monitoring and frontend analytics.
- [ ] Add end-to-end tests for upload, ask, citation selection, and delete flows.
- [ ] Confirm accessibility for keyboard navigation, focus states, and contrast in both themes.
