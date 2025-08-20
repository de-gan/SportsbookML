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

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const { data, error } = await supabase
      .storage
      .from(SUPABASE_BUCKET)
      .download('pred_history.csv');
    if (error || !data) {
      res.status(200).json({ total: 0, correct: 0 });
      return;
    }
    const csv = await data.text();
    const rows = parseCsv(csv);
    const finished = rows.filter(r => r.Actual_Winner);
    const correct = finished.filter(r => Number(r.correct) === 1).length;
    const total = finished.length;
    res.status(200).json({ total, correct });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to load history' });
  }
};