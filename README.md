# VALT (Valgus Analysis & Landing Tracker)

**A web application that analyzes smartphone videos of jump landings and measures
biomechanical movement patterns associated with ACL injury risk in the sports-science
literature — built for female adolescent athletes, who face a substantially higher
burden of non-contact ACL injury than their male peers.**

> ⚠️ **Important scope statement.** VALT does **not** diagnose ACL injuries or
> any medical condition. It *measures* movement mechanics (knee flexion, dynamic knee
> valgus, trunk lean, left/right asymmetry) that injury-prevention research associates
> with risk. It is an educational and screening-support tool, not a medical device, and
> every score or factor it surfaces links back to a real, checkable citation — never an
> invented formula or an unverified claim.

---

## What it does

1. **Guided capture.** The athlete records themselves (front view, then optionally the
   side view too) following the real LESS box-jump protocol: step onto a ~12in box,
   jump forward, land, and immediately rebound into a second jump. The app measures the
   athlete's own box height and landing distance from the video itself — using their
   self-reported height as the only manual input, no tape measure required — and
   reports how closely the actual setup matched the protocol.
2. **A real, cited LESS score.** A direct implementation of the published 17-item
   Landing Error Scoring System (Padua et al., 2009) — not an "inspired-by" subset —
   scoring whichever items the available camera view(s) can actually measure, and
   clearly labeling the few items that require self-report instead.
3. **A plain-language Landing Profile.** A four-category summary (knee control, landing
   depth, symmetry, trunk control) shown before any raw numbers, for an athlete who
   isn't a biomechanist.
4. **Self-reported risk factors — unscored.** Epidemiological factors (prior injury,
   sex, sport, age, activity level, fatigue) that match the literature are listed
   individually with their own citations. There is deliberately no weighted composite
   score here: the relative weight between factors as different as "prior ACL injury"
   and "reported fatigue" isn't something the evidence supports collapsing into one
   number, so this app doesn't invent one.
5. **Personalized exercise recommendations.** A transparent, points-free ranking engine
   matches the athlete's flagged movement priorities against a library of exercises
   drawn from real, cited injury-prevention programs (FIFA 11+, FIFA 11+ Kids, the PEP
   Program, Sportsmetrics) — filtered by age (a real safety constraint, not a
   preference) and, where relevant, sport.
6. **Compare.** See what changed between two recorded landings, side by side, with no
   account and no long-term tracking — just two scans and what moved.
7. **Learn / "Why this matters."** Plain-language context on ACL injury risk in female
   athletes, with every statistic linked to its source.

Every video is deleted from the server immediately after its measurements are
extracted — analyses are stored, raw footage is not.

---

## What's in this repository

This is a **monorepo** — two separate applications living in one Git repository:

| Folder      | What it is                                          | Intended to run on |
|-------------|------------------------------------------------------|--------------------|
| `frontend/` | The website users see (Next.js 14, App Router)        | Vercel             |
| `backend/`  | The server that does the analysis (FastAPI, Python)   | Render              |

They are separate on purpose: the frontend is JavaScript/React and deploys to Vercel;
the backend is Python (it needs MediaPipe/OpenCV) and deploys to Render. Keeping them
in one repo means they stay version-controlled together and never drift out of sync.

**Deployment status:** not yet deployed. Both apps currently only run locally (see
below); production Vercel/Render setup, along with the corresponding environment
variables (`NEXT_PUBLIC_API_URL`, `ALLOWED_ORIGINS`), is still outstanding.

### Backend structure (`backend/app/`)

| Folder         | What it holds |
|-----------------|----------------|
| `api/routes/`   | FastAPI endpoints (`/upload`, `/analyze`, `/report/{id}`, `/exercises`, ...) |
| `cv/`           | The computer-vision pipeline: MediaPipe pose estimation, landing detection, box-jump calibration |
| `risk/`         | The real 17-item LESS scorer, and the self-reported risk-factor logic |
| `exercises/`    | The exercise library, its citations, and the priority-detection/ranking engine |
| `reports/`      | The plain-language Landing Profile summary |
| `services/`     | Orchestration: turns pipeline output into a finished `Analysis` |
| `models/`       | The Pydantic schemas — the data contract with the frontend |
| `ml/`           | Empty on purpose — reserved for future learned models (see its own README) |

---

## Running it locally (first time)

You need **Node.js 18+** and **Python 3.12** installed. Open two terminal windows —
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

Camera capture needs HTTPS (or `localhost`) to work — testing on a real phone requires
either deploying the frontend or tunneling `localhost:3000` (e.g. with a Cloudflare
Tunnel) and adding that tunnel's origin to `backend/.env`'s `ALLOWED_ORIGINS`.

---

## Running the tests

```bash
# Backend
cd backend && source venv/bin/activate && python -m pytest -q

# Frontend
cd frontend && npx tsc --noEmit && npm run lint
```

---

## License

MIT — see [LICENSE](./LICENSE).
