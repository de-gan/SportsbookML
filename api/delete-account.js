const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;

const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*"; // set to your site origin in prod

function setCORS(res) {
  res.setHeader("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
  res.setHeader("Access-Control-Allow-Methods", "DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");
}

module.exports = async (req, res) => {
  setCORS(res);

  // Handle preflight
  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  if (req.method !== "DELETE") {
    res.setHeader("Allow", "DELETE, OPTIONS");
    return res.status(405).json({ error: "Method not allowed" });
  }

  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    console.error("Missing Supabase configuration: SUPABASE_URL or SUPABASE_ANON_KEY");
    return res.status(500).json({ error: "Server misconfiguration" });
  }

  // Expect "Authorization: Bearer <access_token>"
  const authHeader = req.headers.authorization || "";
  const [, token] = authHeader.split(" ");
  if (!token) {
    return res.status(401).json({ error: "Unauthorized: missing Bearer token" });
  }

  try {
    const edgeRes = await fetch(`${SUPABASE_URL}/functions/v1/delete-user`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        apikey: SUPABASE_ANON_KEY,
      },
    });

    const body = await edgeRes.json().catch(() => ({}));

    if (edgeRes.ok) {
      return res.status(200).json({ success: true });
    }

    const message = body.error || body.message || `Delete failed with ${edgeRes.status}`;
    console.error("Edge self-delete failed:", message);
    return res.status(edgeRes.status).json({ error: message });
  } catch (err) {
    console.error("Unhandled error in delete-account:", err);
    return res.status(500).json({ error: "Failed to delete account." });
  }
};