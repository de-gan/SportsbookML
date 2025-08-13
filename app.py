from datetime import date

from flask import Flask, render_template

from mlb_pred_pipeline import predict_and_odds

app = Flask(__name__)


@app.route("/")
def index():
    today = date.today().isoformat()
    try:
        df = predict_and_odds(today)
    except Exception:
        df = None

    cols = ["Team", "Model_Prob", "Odds", "Edge", "EV", "Units", "Book"]
    if df is None or df.empty:
        games = []
        bets = []
    else:
        display_df = df[cols].copy()
        display_df[["Model_Prob", "Edge", "EV"]] = display_df[["Model_Prob", "Edge", "EV"]].round(3)
        display_df["Units"] = display_df["Units"].round(2)
        games = display_df.to_dict(orient="records")
        bets = display_df[display_df["Units"] > 0].to_dict(orient="records")
    return render_template("index.html", date=today, games=games, bets=bets)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
