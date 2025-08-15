const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3001;

function parseCsv(str) {
  const lines = str.trim().split(/\r?\n/);
  if (!lines.length) return [];
  const headers = lines[0].split(',');
  return lines.slice(1).filter(Boolean).map(line => {
    const values = line.split(',');
    const obj = {};
    headers.forEach((h, i) => { obj[h] = values[i]; });
    return obj;
  });
}

function decimalToAmerican(dec) {
  const d = Number(dec);
  if (!isFinite(d)) return undefined;
  if (d >= 2) return Math.round((d - 1) * 100);
  return Math.round(-100 / (d - 1));
}

function handlePredictions(req, res) {
  const filePath = path.join(__dirname, 'data', 'processed', 'games_today.csv');
  try {
    const csv = fs.readFileSync(filePath, 'utf8');
    const rows = parseCsv(csv);
    const grouped = {};
    rows.forEach(r => {
      const gid = r.game_id;
      if (!grouped[gid]) {
        grouped[gid] = { game_id: gid, commence_time: r.commence_time, home_team: r.home_team, away_team: r.away_team, rows: [] };
      }
      grouped[gid].rows.push(r);
    });
    const predictions = Object.values(grouped).map(g => {
      const homeRow = g.rows.find(r => r.Team === g.home_team);
      const awayRow = g.rows.find(r => r.Team === g.away_team);
      return {
        game_id: g.game_id,
        start_time_utc: g.commence_time || null,
        league: 'MLB',
        home_team: g.home_team,
        away_team: g.away_team,
        model: 'mlb_moneyline_v1',
        home_ml_prob: homeRow ? Number(homeRow.Model_Prob) : undefined,
        away_ml_prob: awayRow ? Number(awayRow.Model_Prob) : undefined,
        home_book_odds: homeRow ? decimalToAmerican(homeRow.Odds) : undefined,
        away_book_odds: awayRow ? decimalToAmerican(awayRow.Odds) : undefined,
        edge_home: homeRow && homeRow.Edge ? Number(homeRow.Edge) * 100 : undefined,
        edge_away: awayRow && awayRow.Edge ? Number(awayRow.Edge) * 100 : undefined,
        note: null,
      };
    });
    const stat = fs.statSync(filePath);
    const body = JSON.stringify({ predictions, last_updated: stat.mtime.toISOString() });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(body);
  } catch (err) {
    console.error(err);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Failed to load predictions' }));
  }
}

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url && req.url.startsWith('/api/mlb/predictions')) {
    handlePredictions(req, res);
  } else {
    res.statusCode = 404;
    res.end('Not found');
  }
});

server.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
