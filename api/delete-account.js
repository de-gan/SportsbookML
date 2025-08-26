const { createClient } = require('@supabase/supabase-js');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

/**
 * Vercel serverless function to delete the authenticated user's account.
 */
module.exports = async (req, res) => {
  if (req.method !== 'DELETE') {
    res.setHeader('Allow', 'DELETE');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const authHeader = req.headers.authorization || '';
  const token = authHeader.split(' ')[1];
  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const { data, error: userError } = await supabase.auth.getUser(token);
    if (userError || !data?.user) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    const { error: deleteError } = await supabase.auth.admin.deleteUser(data.user.id);
    if (deleteError) throw deleteError;

    return res.status(200).json({ success: true });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Failed to delete account.' });
  }
};