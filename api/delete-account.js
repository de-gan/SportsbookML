const SUPABASE_URL =
  process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_KEY =
  process.env.SUPABASE_KEY ||
  process.env.VITE_SUPABASE_ANON_KEY;

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
    return res.status(401).json({ error: "Unauthorized" });
  }

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error("Missing Supabase configuration");
    return res.status(500).json({ error: "Server misconfiguration" });
  }

  try {
    const response = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
        apikey: SUPABASE_KEY,
      },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message = body.error_description || body.error || "Failed to delete account.";
      return res.status(response.status).json({ error: message });
    }

    return res.status(200).json({ success: true });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Failed to delete account.' });
  }
};