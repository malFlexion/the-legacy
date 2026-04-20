# Frontend Deployment Walkthrough

Two-part deployment:
1. **Static frontend** — served from GitHub Pages at `docs/` (vanilla HTML/JS/CSS, no build step)
2. **FastAPI backend** — Dockerized and deployed to Fly.io, proxies browser requests into the SageMaker endpoint

The browser can't call SageMaker directly (AWS Signature V4 auth can't be safely exposed in JavaScript), so the Fly-hosted FastAPI server holds the AWS credentials and forwards requests.

```
Browser (GitHub Pages) ─HTTPS─> FastAPI on Fly.io ─IAM─> SageMaker endpoint
```

## Prerequisites

- SageMaker endpoint deployed and `InService` (see [sagemaker-deployment.md](sagemaker-deployment.md))
- AWS access key + secret with `sagemaker:InvokeEndpoint` permission
- Fly.io account — install `flyctl` from [fly.io/docs/hands-on/install-flyctl](https://fly.io/docs/hands-on/install-flyctl/)
- Docker installed locally (Fly builds remotely but some checks run local)

## 1. Deploy the backend to Fly.io

From the repo root:

```
fly auth signup   # or fly auth login
fly launch --no-deploy
```

`fly launch` reads the committed `fly.toml` and `Dockerfile`. Accept the defaults. It'll create a Fly app named `the-legacy-api` (or whatever you pick — update `app = "..."` in fly.toml if the name is taken).

Set secrets:

```
fly secrets set INFERENCE_BACKEND=sagemaker
fly secrets set SAGEMAKER_ENDPOINT=the-legacy-llm
fly secrets set AWS_REGION=us-east-1
fly secrets set AWS_ACCESS_KEY_ID=AKIA...
fly secrets set AWS_SECRET_ACCESS_KEY=...
```

Deploy:

```
fly deploy
```

First deploy builds the Docker image (~2-3 minutes) and rolls it out. You'll see a URL like `https://the-legacy-api.fly.dev`.

Verify:

```
curl https://the-legacy-api.fly.dev/health
```

Should return `{"status": "ok", "model": "the-legacy-llm", ...}`.

Scale-to-zero is enabled in `fly.toml` — the instance stops after a few minutes of idle and cold-starts on the next request (~5-10s to wake up). Free tier handles light demo traffic without charge.

## 2. Point the frontend at it

Edit `docs/config.js`:

```javascript
window.API_BASE = "https://the-legacy-api.fly.dev";
```

Commit and push.

## 3. Enable GitHub Pages

1. On GitHub: repo Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: `master`, folder: `/docs`
4. Save

Within 1-2 minutes the site is live at `https://malFlexion.github.io/the-legacy/`.

## 4. Verify end-to-end

Open the site in a browser:
- Top-right should show `API: https://the-legacy-api.fly.dev — ✓ ok (the-legacy-llm)`
- Chat tab: ask "What's the best deck in Legacy?" and confirm you get a domain-aware response (mentions Dimir Tempo etc.)
- Budget tab: paste a decklist, confirm tier columns render with prices
- Goldfish tab: draw a hand, confirm card images render
- Import tab: paste a decklist or Moxfield URL, confirm parsed grid renders

## Troubleshooting

### `✗ Failed to fetch` in the API status
CORS or mixed-content (http/https) issue. The FastAPI server has `allow_origins=["*"]` so CORS should be open. Double-check:
- The Fly URL in `config.js` uses `https://` (not `http://`)
- `fly status` shows the app as "running"
- `fly logs` for any startup errors

### `✗ 502/503` errors
App is cold-starting. First request after idle takes 5-10s. Subsequent requests should be fast.

### `✗ 500` errors on chat / goldfish
Likely SageMaker endpoint isn't live. Check:
```
python scripts/deploy_sagemaker.py --status
```
Start the endpoint if it's `OutOfService` or missing.

### Deploy fails with "App name already taken"
Edit `fly.toml` and change `app = "the-legacy-api"` to something unique (e.g., `the-legacy-api-malflexion`). Re-run `fly launch --no-deploy`, then `fly deploy`.

### Docker image too large / build timeout
The image is ~1GB with chromadb + sentence-transformers. If builds time out, remove those from the Dockerfile — RAG will silently disable itself at runtime (the server already handles missing vectordb gracefully).

## Cost

- **GitHub Pages:** free
- **Fly.io:** free tier fits a scale-to-zero proxy. Usage is charged per second the machine is running — at `shared-cpu-1x` with 512MB RAM it's ~$0.0000022/sec. An hour of active usage costs a few cents.
- **SageMaker:** this is the expensive part (~$1.41/hr). Delete when idle via `python scripts/deploy_sagemaker.py --delete`.

Total cost for an hour of demo: ~$1.50, almost entirely SageMaker.
