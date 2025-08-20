const { createClient } = require('@supabase/supabase-js');

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

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

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

    res.status(200).json({ predictions, last_updated: new Date().toISOString() });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to load predictions' });
  }
};