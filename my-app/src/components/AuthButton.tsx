import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth";

export default function AuthButton() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const navigate = useNavigate();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate("/");
  };

  if (user) {
    const metadata = user.user_metadata as {
      display_name?: string;
      full_name?: string;
      name?: string;
    };
    const displayName =
      metadata.display_name || metadata.full_name || metadata.name || user.email;

    return (
      <div className="relative" ref={menuRef}>
        <Button
          variant="ghost"
          onClick={() => setOpen((prev) => !prev)}
          className="gap-2 hover:bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700"
        >
          {displayName}
        </Button>
        {open && (
          <div className="absolute right-0 mt-2 w-40 rounded-md border border-border bg-white dark:bg-neutral-900 shadow-md">
            <button
              className="block w-full px-4 py-2 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800"
            >
              Subscription
            </button>
            <button
              className="block w-full px-4 py-2 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800"
            >
              Settings
            </button>
            <button
              onClick={handleSignOut}
              className="block w-full px-4 py-2 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <Button asChild variant="ghost" className="gap-2">
      <Link to="/login">Login/Register</Link>
    </Button>
  );
}

