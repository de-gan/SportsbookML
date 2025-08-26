const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

module.exports = async function handler(req, res) {
  if (req.method !== 'DELETE') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const authHeader = req.headers.authorization || '';
  const token = authHeader.replace('Bearer', '').trim();
  if (!token) {
    res.status(401).json({ error: 'Unauthorized' });
    return;
  }

  try {
    const { data, error: userError } = await supabase.auth.getUser(token);
    if (userError || !data?.user) {
      res.status(401).json({ error: 'Invalid token' });
      return;
    }

    const { error: deleteError } = await supabase.auth.admin.deleteUser(data.user.id);
    if (deleteError) throw deleteError;

    res.status(200).json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to delete account.' });
  }
};