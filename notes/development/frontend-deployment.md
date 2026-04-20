# Frontend Deployment Walkthrough

Single-deploy architecture: the FastAPI backend on Fly.io serves both the JSON API and the static frontend. One URL, no CORS concerns, no separate GitHub Pages setup.

```
Browser ─HTTPS─> Fly.io (FastAPI + static docs/) ─IAM─> SageMaker endpoint
```

The browser can't call SageMaker directly (AWS Signature V4 auth can't be safely exposed in JavaScript), so the Fly-hosted FastAPI server holds the AWS credentials and forwards inference requests. All the deterministic endpoints (budget tiers, goldfish, card lookup) run in the same process.

## Prerequisites

- SageMaker endpoint deployed and `InService` (see [sagemaker-deployment.md](sagemaker-deployment.md))
- AWS access key + secret with `sagemaker:InvokeEndpoint` permission
- Fly.io account — install `flyctl` from [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl/)

## 1. Launch the Fly app

From the repo root:

```
fly auth signup   # or fly auth login
fly launch --no-deploy
```

`fly launch` reads the committed `fly.toml` and `Dockerfile`. Accept the defaults. It'll register a Fly app named `the-legacy-api` (or whatever you pick — update `app = "..."` in fly.toml if the name is taken).

## 2. Set secrets

```
fly secrets set INFERENCE_BACKEND=sagemaker
fly secrets set SAGEMAKER_ENDPOINT=the-legacy-llm
fly secrets set AWS_REGION=us-east-1
fly secrets set AWS_ACCESS_KEY_ID=AKIA...
fly secrets set AWS_SECRET_ACCESS_KEY=...
```

## 3. Deploy

```
fly deploy
```

First deploy builds the Docker image (~2-3 minutes) and rolls it out. Fly prints the URL when it's done, e.g. `https://the-legacy-api.fly.dev`.

### Optional: enable continuous deployment on push

`.github/workflows/fly-deploy.yml` runs `flyctl deploy` whenever you push commits that change code, Docker config, or vectordb to `master`. Wire it up once:

```
fly tokens create deploy -a the-legacy-api
```

Copy the token, then in your GitHub repo:

1. Settings → Secrets and variables → Actions → New repository secret
2. Name: `FLY_API_TOKEN`
3. Value: paste the token
4. Save

The next `git push` triggers an automatic deploy. You can watch it in the Actions tab, or trigger manually via "Run workflow" on the Fly Deploy action. The workflow skips deploys for doc-only / training-data commits so you don't burn build minutes on every README tweak.

## 4. Verify end-to-end

Open `https://the-legacy-api.fly.dev/` in a browser — the UI should load immediately. In the header you should see something like:

```
API: (same origin) — ✓ ok (the-legacy-llm)
```

Smoke test each tab:
- **Chat**: ask "What's the best deck in Legacy?" and confirm a domain-aware response
- **Import & Analyze**: paste a decklist or Moxfield URL, confirm the card grid renders
- **Goldfish**: draw an opening hand and confirm images load
- **Budget Tiers**: paste a decklist, confirm three tier columns with prices

You can also hit the raw API:
```
curl https://the-legacy-api.fly.dev/health
curl https://the-legacy-api.fly.dev/card/Brainstorm
```

## How it fits together

- `Dockerfile` copies `src/`, `data/card_index.pkl`, and `docs/` into the image
- FastAPI serves `/chat`, `/goldfish/*`, `/budget-tiers`, etc. as JSON endpoints
- After all API routes are registered, the server mounts `docs/` at `/` via `StaticFiles(html=True)` so `GET /` returns `index.html`
- `docs/config.js` sets `window.API_BASE = ""` — the frontend makes same-origin fetch calls like `/chat`, which Fly routes back to the same container

## Troubleshooting

### `✗ Failed to fetch` in the API status
Check `fly logs` — the app may have crashed on startup. Common causes:
- Missing AWS secrets → `invoke_endpoint` fails on every request
- Wrong `SAGEMAKER_ENDPOINT` name
- SageMaker endpoint `OutOfService`

### `✗ 502/503` errors
Fly is cold-starting the machine. First request after idle takes 5-10s. Retry.

### `✗ 500` errors on chat / goldfish
Usually the SageMaker endpoint isn't running. Check:
```
python scripts/deploy_sagemaker.py --status
```
Start the endpoint if it's missing or failed.

### Deploy fails with "app name already taken"
Edit `fly.toml` and change `app = "the-legacy-api"` to something unique (e.g., `the-legacy-api-malflexion`). Re-run `fly launch --no-deploy`, then `fly deploy`.

### Image too large / build timeout
The image is ~1.5GB with `chromadb`, `sentence-transformers`, the pre-downloaded embedding model (~80MB), and the vectordb snapshot (~13MB). If builds time out on a constrained CI runner, you can disable RAG by:
1. Removing the `RUN python -c "...SentenceTransformer..."` warm-up line from `Dockerfile`
2. Removing `COPY vectordb/` from `Dockerfile`
3. Adding `vectordb/` back to `.dockerignore`

The server handles missing vectordb gracefully — RAG just disables itself. The finetuned model still knows most of the rules (Round 2 rules_knowledge scored 83%), so you lose some recall but nothing catastrophic.

### RAG not retrieving anything / empty context
Check the health endpoint:
```
curl https://the-legacy-api.fly.dev/health
```
`vector_db: true` and `vector_chunks > 0` confirms RAG loaded. If `vector_chunks: 0`, the `vectordb/` directory was copied empty — rebuild with `python src/build_vectordb.py` locally, then redeploy.

## Cost

- **Fly.io**: free tier fits this workload when scale-to-zero is enabled (configured in `fly.toml`). The machine stops after a few minutes of idle and cold-starts on the next request. Continuous usage on `shared-cpu-1x` at 512MB is ~$0.008/hour.
- **SageMaker**: this is the expensive part (~$1.41/hour). Delete when idle via `python scripts/deploy_sagemaker.py --delete`.

An hour of active demo costs ~$1.50, almost entirely SageMaker.

## Local dev

To run the same setup locally without Fly:

```
export INFERENCE_BACKEND=sagemaker SAGEMAKER_ENDPOINT=the-legacy-llm AWS_REGION=us-east-1
uvicorn src.server:app --reload --port 8000
```

Then open `http://localhost:8000/` — the frontend is served by the same process, hitting `/chat` and friends on the same origin.

For local dev against a different port (e.g. backend on 8000, frontend opened via file://), set `window.API_BASE = "http://localhost:8000"` in `docs/config.js`.
