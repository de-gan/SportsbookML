# SportsbookML

SportsbookML is a prototype pipeline and web application for generating
Major League Baseball moneyline predictions and comparing them against
available sportsbook odds.

## Repository layout

- `backend/` &ndash; Python scripts for collecting statistics, engineering
  features and training the prediction model. Running
  `python backend/mlb_pred_pipeline.py` produces a
  `data/processed/games_today.csv` file with the latest model
  probabilities and edges and can optionally upload them to a Supabase table.
- `server.js` &ndash; a small Node HTTP server that exposes the predictions
  as JSON at `/api/mlb/predictions` by reading the
  `data/processed/games_today.csv` file.
- `my-app/` &ndash; a Vite + React frontend (TypeScript and Tailwind) that
  displays the predictions in a dashboard.

## Getting started

1. **Generate predictions**

   The pipeline writes predictions to `data/processed/games_today.csv` and, if
   the `SUPABASE_URL` and `SUPABASE_KEY` environment variables are set, also
   publishes the results to a Supabase table for the frontend to consume. When
   `SUPABASE_STORAGE_BUCKET` is set, required CSV inputs such as player IDs and
   team schedules will be downloaded from that storage bucket instead of being
   committed to the repository.

   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_KEY="service_role_key"
   export SUPABASE_STORAGE_BUCKET="mlb-data"
   python backend/mlb_pred_pipeline.py
   ```

2. **Start the API server**

   ```bash
   npm start
   ```

   The server listens on <http://localhost:3001>.

3. **Run the frontend**

   ```bash
   cd my-app
   npm run dev
   ```

   The development server runs on <http://localhost:5173>.

## Deployment

The frontend can be deployed to Vercel and backed by a Supabase project for
storage.

1. Create a Supabase project and note the project URL and anon key. Add them to
   `my-app/.env` based on the provided `.env.example` file.
2. Commit your changes and push to a Vercel-connected repository. Vercel reads
   the `vercel.json` file and builds the Vite project in `my-app/`.
3. Configure the `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` environment
   variables in your Vercel project settings.

After deployment, the site will fetch predictions and history directly from
Supabase tables (`predictions` and `history`).

## Goals

- Provide win/loss probability estimates for each game.
- Compare model probabilities to sportsbook odds to surface positive edges.
- Track return on investment (ROI) and maintain a rolling bankroll.

## Models

The current implementation includes a classification model for win/loss
predictions. Regression models for total runs and probability calibration
are planned but not yet active.

