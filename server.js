require("dotenv").config();
const http = require('http');
const { createClient } = require('@supabase/supabase-js');
const deleteAccountHandler = require('./api/delete-account');

const PORT = process.env.PORT || 3001;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;
const SUPABASE_BUCKET = process.env.SUPABASE_BUCKET || 'mlb-data';

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

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

async function handlePredictions(req, res) {
  try {
    const { data, error } = await supabase
      .storage
      .from(SUPABASE_BUCKET)
      .download('games_today.csv');
    if (error || !data) throw error || new Error('No data');
    const csv = await data.text();
    const rows = parseCsv(csv);
    const grouped = {};
    rows.forEach(r => {
      const gid = r.game_id;
      if (!grouped[gid]) {
        grouped[gid] = { game_id: gid, commence_time: r.commence_time, home_team: r.home_team, away_team: r.away_team, rows: [] };
      }
      grouped[gid].rows.push(r);
    });
    // Build a prediction entry for every sportsbook represented in the rows
    const predictions = Object.values(grouped).flatMap(g => {
      const books = Array.from(new Set(g.rows.map(r => r.Sportsbook || r.book || r.Book)));
      return books.map(book => {
        const homeRow = g.rows.find(r => r.Team === g.home_team && (r.Sportsbook === book || r.book === book || r.Book === book));
        const awayRow = g.rows.find(r => r.Team === g.away_team && (r.Sportsbook === book || r.book === book || r.Book === book));
        return {
          game_id: g.game_id,
          start_time_utc: g.commence_time || null,
          league: 'MLB',
          home_team: g.home_team,
          away_team: g.away_team,
          sportsbook: book,
          model: 'mlb_moneyline_v1',
          home_ml_prob: homeRow ? Number(homeRow.Model_Prob) : undefined,
          away_ml_prob: awayRow ? Number(awayRow.Model_Prob) : undefined,
          home_book_odds: homeRow ? decimalToAmerican(homeRow.Odds) : undefined,
          away_book_odds: awayRow ? decimalToAmerican(awayRow.Odds) : undefined,
          edge_home: homeRow && homeRow.Edge ? Number(homeRow.Edge) : undefined,
          edge_away: awayRow && awayRow.Edge ? Number(awayRow.Edge) : undefined,
          note: null,
        };
      });
    });
    const body = JSON.stringify({ predictions, last_updated: new Date().toISOString() });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(body);
  } catch (err) {
    console.error(err);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Failed to load predictions' }));
  }
}

async function handleHistory(req, res) {
  try {
    const { data, error } = await supabase
      .storage
      .from(SUPABASE_BUCKET)
      .download('pred_history.csv');
    if (error || !data) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ total: 0, correct: 0 }));
      return;
    }
    const csv = await data.text();
    const rows = parseCsv(csv);
    const finished = rows.filter(r => r.Actual_Winner);
    const correct = finished.filter(r => Number(r.correct) === 1).length;
    const total = finished.length;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ total, correct }));
  } catch (err) {
    console.error(err);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Failed to load history' }));
  }
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'GET' && req.url && req.url.startsWith('/api/mlb/predictions')) {
    await handlePredictions(req, res);
  } else if (req.method === 'GET' && req.url && req.url.startsWith('/api/mlb/history')) {
    await handleHistory(req, res);
  } else if (req.method === 'DELETE' && req.url && req.url.startsWith('/api/delete-account')) {
    await deleteAccountHandler(req, res);
  } else {
    res.statusCode = 404;
    res.end('Not found');
  }
});

server.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});