# SportsbookML

SportsbookML is a prototype pipeline and web application for generating
Major League Baseball moneyline predictions and comparing them against
available sportsbook odds.

## Repository layout

- `backend/` &ndash; Python scripts for collecting statistics, engineering
  features and training the prediction model. Running
  `python backend/mlb_pred_pipeline.py` produces a
  `data/processed/games_today.csv` file with the latest model
  probabilities and edges.
- `server.js` &ndash; a small Node HTTP server that exposes the predictions
  as JSON at `/api/mlb/predictions` by reading the
  `data/processed/games_today.csv` file.
- `my-app/` &ndash; a Vite + React frontend (TypeScript and Tailwind) that
  displays the predictions in a dashboard.

## Getting started

1. **Generate predictions**

   ```bash
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

## Goals

- Provide win/loss probability estimates for each game.
- Compare model probabilities to sportsbook odds to surface positive edges.
- Track return on investment (ROI) and maintain a rolling bankroll.

## Models

The current implementation includes a classification model for win/loss
predictions. Regression models for total runs and probability calibration
are planned but not yet active.

