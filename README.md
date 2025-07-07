# SportsbookML
Model to predict MLB Baseball odds (Specific types TBD)
# Data Collection
- Home vs Away
- Final scores
- Starting pitcher stats
- Bullpen ERA
- Team batting average vs LHP/RHP
- Previous 5-game trends
- Day of week, stadium, travel fatigue
## Betting Odds
- Moneyline odds → convert to implied probability
- Run line (typically ±1.5)
- Over/under total runs

# Win/Loss Predictor
Want data for Both teams individually, and then head-to-head
- Team stats
- Pitcher W/L
- Lineup BA
- Travel fatigue

# Necessary Variables
## Target: 
Win/Loss
## Features: Split when Home v Away 
- Win/Loss streak -- Captures momentum
- Last N games W% -- Reflects recent form
- Season W% -- Overall team quality
- Home/Away indicator -- Home field advantage
- Run differential (season & recent) -- Better than just W/L
- Avg runs scored/allowed (last N games) -- Tracks offense/defense form
- Opponent matchup record -- Psychological edge or disadvantage
- Division matchup flag	-- Divisional games tend to be tighter?
- Rest days -- More rest = better performance
## schedule_and_record
- 