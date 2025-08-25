import { Button } from "./ui/button";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth";

export default function AuthButton() {
  const { user } = useAuth();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    window.location.href = "/";
  };

  if (user) {
    return (
      <Button variant="ghost" onClick={handleSignOut} className="gap-2">
        Logout
      </Button>
    );
  }

  return (
    <Button asChild variant="ghost" className="gap-2">
      <a href="/login">Login</a>
    </Button>
  );
}

