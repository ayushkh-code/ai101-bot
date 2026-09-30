# AI 101 Daily bot

Posts one AI explainer carousel (5 slides) to Instagram @ai_101_daily every day at 8:00 AM IST.

- `content.json`: the 90 post content bank, in posting order. Edit or add posts here.
- `post.py`: renders the next unused post into `images/` and publishes it via the Instagram Graph API.
- `history.json`: what has been posted (created on first run). Posts listed here are skipped.
- `.github/workflows/daily.yml`: the schedule. Run it manually from the Actions tab with "Run workflow".

Secrets needed: `IG_USER_ID`, `IG_ACCESS_TOKEN` (long lived, expires about every 60 days; regenerate in the Graph API Explorer and update the secret).

Local test: `python post.py` renders the next post; `DRY_RUN=1 python post.py --publish` simulates publishing.
