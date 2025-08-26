import { useState, useEffect } from "react";
import NavBar from "@/components/NavBar";
import ThemeToggle from "@/components/ThemeToggle";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth";
import MachineLearningBackground from "@/components/Background";

export default function Settings() {
  const { user } = useAuth();
  const [displayName, setDisplayName] = useState(() => {
    const metadata = user?.user_metadata as {
      display_name?: string;
      full_name?: string;
      name?: string;
    };
    return (
      metadata?.display_name ||
      metadata?.full_name ||
      metadata?.name ||
      ""
    );
  });
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDark, setIsDark] = useState(
      () => document.documentElement.classList.contains("dark")
    );
  
    useEffect(() => {
      const observer = new MutationObserver(() =>
        setIsDark(document.documentElement.classList.contains("dark"))
      );
      observer.observe(document.documentElement, { attributes: true });
      return () => observer.disconnect();
    }, []);

  const updateDisplayName = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus(null);
    setError(null);
    const { error } = await supabase.auth.updateUser({
      data: { display_name: displayName },
    });
    if (error) {
      setError(error.message);
    } else {
      setStatus("Display name updated.");
    }
  };

  const resetPassword = async () => {
    if (!user?.email) return;
    setStatus(null);
    setError(null);
    const redirectTo =
      (import.meta.env.VITE_SITE_URL as string) || window.location.origin;
    const { error } = await supabase.auth.resetPasswordForEmail(user.email, {
      redirectTo,
    });
    if (error) {
      setError(error.message);
    } else {
      setStatus("Password reset email sent.");
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen text-neutral-900 dark:text-neutral-100">
        <NavBar />
        <main className="max-w-xl mx-auto p-4">
          <p>Please log in to view settings.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen text-neutral-900 dark:text-neutral-100">
      <MachineLearningBackground density={0.00015} speed={0.5} interactive opacity={0.2} color={isDark ? "#06b6d4" : "#ff0000ff"} nodeColor={isDark ? "#e0f2fe" : "#ff0000ff"}/>
      <NavBar user={!!user} />
      <main className="max-w-xl mx-auto p-4 space-y-6">
        <Card className="rounded-2xl border-border/70 shadow-sm">
          <CardContent className="p-6 space-y-4">
            <h1 className="text-2xl font-bold">User Settings</h1>

            <div className="flex items-center justify-between">
              <span className="font-medium">Dark Mode</span>
              <ThemeToggle />
            </div>

            <form onSubmit={updateDisplayName} className="space-y-2">
              <label className="text-sm font-medium" htmlFor="display-name">
                Display Name
              </label>
              <Input
                id="display-name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter display name"
              />
              <Button type="submit" className="w-full">
                Save
              </Button>
            </form>

            <div className="space-y-1">
              <div className="text-sm font-medium">Email</div>
              <div className="text-sm opacity-80">{user.email}</div>
            </div>

            <Button variant="secondary" onClick={resetPassword} className="w-full">
              Reset Password
            </Button>

            {status && <div className="text-sm text-green-500">{status}</div>}
            {error && <div className="text-sm text-red-500">{error}</div>}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}