# MultiMind Studio

An MVP desktop studio combining Electron, React, and a FastAPI backend powered by the MultiMind SDK. It provides chat streaming, retrieval augmented generation (RAG), and a script runner with Monaco editor integration.

## Windows Setup

1. Clone the repository and open a terminal (PowerShell or Command Prompt).
2. Create a Python virtual environment and install backend dependencies:
   ```powershell
   python -m venv .venv
   .\\.venv\\Scripts\\activate
   pip install -r app/backend/requirements.txt
   ```
3. Start the FastAPI backend:
   ```powershell
   cd app/backend
   uvicorn main:app --reload --port 8765
   ```
4. In a new terminal, install frontend dependencies and start Vite dev server:
   ```powershell
   cd app/frontend
   npm install
   npm run dev
   ```
5. In another terminal, start the Electron shell:
   ```powershell
   cd electron
   npm install
   npm start
   ```

## Environment Variables

Copy `app/backend/.env.example` to `app/backend/.env` and fill in as needed:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `MISTRAL_API_KEY`
- `MODEL_NAME`
- `WORKSPACE_DIR`
- `VECTORSTORE_DIR`

Electron keeps room for secure key storage via Keytar integration in the future.

## RAG Workflow Example

1. Open the **RAG** tab.
2. Choose or enter a collection ID (defaults to `default`).
3. Upload documents (PDF, TXT, MD) — files are stored in `workspace/uploads/`.
4. Click **Rebuild Index** to create/update the Chroma collection.
5. Enter a question and press **Query**. Returned contexts and the synthesized answer will appear below.

## Script Run / Stop Flow

1. Navigate to the **Scripts** tab and select a script from the tree.
2. Edit the script in the Monaco editor and click **Save**.
3. Press **Run** to execute it; stdout/stderr stream into the console in real time.
4. Use **Stop** to terminate the subprocess if needed. Artifacts are listed via the **Artifacts** button and are stored under `workspace/<project>/artifacts/<run_id>/`.

## API Routes

- `GET /health`
- `POST /api/chat/stream`
- `GET /api/chat/models`
- `GET /api/chat/router`
- `POST /api/rag/upload`
- `POST /api/rag/index`
- `POST /api/rag/query`
- `GET /api/scripts`
- `GET /api/scripts/{id}`
- `POST /api/scripts`
- `PUT /api/scripts/{id}`
- `DELETE /api/scripts/{id}`
- `POST /api/scripts/run`
- `POST /api/scripts/stop`
- `GET /api/scripts/runs/{id}/stream`
- `GET /api/scripts/runs/{id}/artifacts`
- `GET /api/settings`
- `POST /api/settings`
- `WebSocket /ws/logs`

## Project Layout

```
multimind-studio/
├─ app/
│  ├─ backend/
│  └─ frontend/
└─ electron/
```

Backed by SQLite for app state and Chroma for vector search, this project is ready for further expansion into a full-featured desktop studio.
