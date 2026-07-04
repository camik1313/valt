# ACL MotionCheck

**A web application that analyzes smartphone videos of jump landings and measures
biomechanical movement patterns associated with ACL injury risk in the sports-science
literature.**

> ⚠️ **Important scope statement.** ACL MotionCheck does **not** diagnose ACL injuries or
> any medical condition. It *measures* movement mechanics (knee flexion, dynamic knee
> valgus, trunk lean, left/right asymmetry, hip position) that injury-prevention research
> associates with risk. It is an educational and screening-support tool, not a medical
> device.

---

## What's in this repository

This is a **monorepo** — two separate applications living in one Git repository:

| Folder      | What it is                          | Runs on            |
|-------------|-------------------------------------|--------------------|
| `frontend/` | The website users see (Next.js)     | Vercel             |
| `backend/`  | The server that does the analysis (FastAPI, Python) | Render |

They are separate on purpose: the frontend is JavaScript/React and deploys to Vercel;
the backend is Python and deploys to Render. Keeping them in one repo means they stay
version-controlled together and never drift out of sync.

---

## Running it locally (first time)

You need **Node.js 18+** and **Python 3.11** installed. Open two terminal windows —
one for the backend, one for the frontend. They run at the same time.

### 1. Start the backend

```bash
cd backend
python3 -m venv venv              # create an isolated Python environment
source venv/bin/activate          # turn it on (Mac/Linux)
pip install -r requirements.txt   # install Python packages
uvicorn app.main:app --reload     # start the server on http://localhost:8000
```

Leave this terminal running. Visit http://localhost:8000/docs to see the auto-generated
API documentation.

### 2. Start the frontend (in a second terminal)

```bash
cd frontend
cp .env.local.example .env.local  # create your local settings file
npm install                       # install JavaScript packages
npm run dev                       # start the site on http://localhost:3000
```

Open http://localhost:3000 in your browser. You should see the homepage.

---

## Project stages

This project is built in deliberate stages so each piece can be tested before the next
is added:

1. Folder structure ✅
2. Configuration & starter files ✅
3. Homepage ✅
4. Upload workflow (in progress)
5. Backend API
6. Mock computer-vision pipeline
7. Real MediaPipe + biomechanics integration (the scientific core)

---

## License

MIT — see [LICENSE](./LICENSE).
