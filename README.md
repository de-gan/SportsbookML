# SportsbookML
Model to predict MLB Baseball odds (Specific types TBD)

# Objective
## Win/Loss Predictor & Odds Comparitor + ROI
1. Provide predictions and compare to varying odds across sportsbooks
2. Show greatest point efficient/bettor friendly odds
3. **Show odds descrepncies across books to hedge*
## Outputs
Predictions of:
- Win/Loss Probability
- Run Dif.
## Additional
- ROI and rolling tally of initial investment ($XXX)
- Dashboard

# Models
Regression for Run Dif
**Classification for Win/Loss*
**Regression for Total Runs*
**Regression for Probabilities*


--- CAN I GET WIN PERCENTAGE FROM BINARY WIN/LOSS TARGET VARIABLE?

# Necessary Variables
## Target:
Run Dif. & W/L
## Features: (Future -- Split data when Home v Away)
### Team data
- Win/Loss streak -- Captures momentum
- Last N games W% -- Reflects recent form
- Season W% -- Overall team quality
- Home/Away indicator -- Home field advantage
- Run differential (season & recent) -- Better than just W/L
- Avg runs scored/allowed (last N games) -- Tracks offense/defense form
- Opponent matchup record -- Psychological edge or disadvantage
- Division matchup flag	-- Divisional games tend to be tighter?
- Rest days -- More rest = better performance
### Individual & Lineup data
- Team AVG/OBP/SLG vs RHP/LHP
- Team K% and BB%
- Rating?
### Starting Pitcher & Bullpen data
- ERA, WHIP, etc
- K/BB, GB%, HR/9
- Recent 3-5 game ERA/FIP
- Splits vs opponent
- Home/Away splits
- Pitch count in last start
- RHP/LHP
### Game Data
- Date
- Weather?
- Day/Night
### Sportsbook Odds data
- Lines
- Over/Under total
- Line movement?
## schedule_and_record
- 