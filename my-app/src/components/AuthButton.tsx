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
    const displayName =
      (user.user_metadata as { display_name?: string })?.display_name ||
      user.email;

    return (
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">
          {displayName}
        </span>
        <Button variant="ghost" onClick={handleSignOut} className="gap-2">
          Logout
        </Button>
      </div>
    );
  }

  return (
    <Button asChild variant="ghost" className="gap-2">
      <a href="/login">Login</a>
    </Button>
  );
}

