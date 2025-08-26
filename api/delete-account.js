const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_KEY; // optional: for admin fallback

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
    // --- 1) Try self-delete with the user's access token
    const selfDelete = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
        apikey: SUPABASE_ANON_KEY,
      },
    });

    if (selfDelete.ok) {
      return res.status(200).json({ success: true, mode: "self" });
    }

    // Read body for diagnostics (don’t throw if not JSON)
    const body = await selfDelete.json().catch(() => ({}));
    const message =
      body.error_description || body.error || `Self-delete failed with ${selfDelete.status}`;
    console.warn("Self-delete failed:", message);

    // --- 2) Optional admin fallback (requires service role key)
    if (SUPABASE_SERVICE_ROLE_KEY) {
      // First get the current user to learn their ID
      const whoami = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          apikey: SUPABASE_ANON_KEY,
        },
      });

      if (!whoami.ok) {
        const wbody = await whoami.json().catch(() => ({}));
        const wmsg = wbody.error_description || wbody.error || `whoami failed ${whoami.status}`;
        console.error("Admin fallback: failed to fetch user:", wmsg);
        return res.status(selfDelete.status).json({ error: message });
      }

      const user = await whoami.json().catch(() => null);
      const userId = user?.id;
      if (!userId) {
        console.error("Admin fallback: user id missing in whoami response");
        return res.status(selfDelete.status).json({ error: message });
      }

      // Admin delete
      const adminDelete = await fetch(`${SUPABASE_URL}/auth/v1/admin/users/${userId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
          apikey: SUPABASE_ANON_KEY,
        },
      });

      if (adminDelete.ok) {
        return res.status(200).json({ success: true, mode: "admin" });
      } else {
        const abody = await adminDelete.json().catch(() => ({}));
        const amsg =
          abody.error_description || abody.error || `Admin delete failed ${adminDelete.status}`;
        console.error("Admin delete failed:", amsg);
        return res.status(500).json({ error: "Failed to delete account." });
      }
    }

    // No admin fallback configured → bubble up self-delete failure
    return res.status(selfDelete.status).json({ error: message });
  } catch (err) {
    console.error("Unhandled error in delete-account:", err);
    return res.status(500).json({ error: "Failed to delete account." });
  }
};