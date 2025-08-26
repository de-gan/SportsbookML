const SUPABASE_URL =
  process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_KEY =
  process.env.SUPABASE_KEY ||
  process.env.VITE_SUPABASE_ANON_KEY;

/**
 * Vercel serverless function to delete the authenticated user's account.
 */
module.exports = async (req, res) => {
  const send = (status, payload) => {
    res.statusCode = status;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(payload));
  };

  if (req.method !== 'DELETE') {
    res.setHeader('Allow', 'DELETE');
    return send(405, { error: 'Method not allowed' });
  }

  const authHeader = req.headers.authorization || '';
  const token = authHeader.split(' ')[1];
  if (!token) {
    return send(401, { error: 'Unauthorized' });
  }

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error('Missing Supabase configuration');
    return send(500, { error: 'Server misconfiguration' });
  }

  try {
    const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
        apikey: SUPABASE_KEY,
      },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message =
        body.error_description || body.error || 'Failed to delete account.';
      return send(response.status, { error: message });
    }

    return send(200, { success: true });
  } catch (err) {
    console.error(err);
    return send(500, { error: 'Failed to delete account.' });
  }
};