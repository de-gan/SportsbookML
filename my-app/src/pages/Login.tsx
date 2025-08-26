import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "react-router-dom";
import Google from "@/assets/GoogleLogo.png"

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const localUrl = import.meta.env.VITE_SITE_URL as string

  const redirectUrl = `${
    localUrl || window.location.origin
  }`;

  const signInWithGoogle = async () => {
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: redirectUrl },
    });
    if (error) {
      setError(error.message);
    }
  };

  const navigate = useNavigate();

  const signIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setError(error.message);
    } else {
      navigate("/mlb");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <form className="space-y-4" onSubmit={signIn}>
            <Input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && <div className="text-sm text-red-500">{error}</div>}
            <Button type="submit" className="w-full">
              Sign In
            </Button>
            <Button
              type="button"
              className="w-full"
              onClick={signInWithGoogle}
            >
              <img
                src={Google}
                alt="Google logo"
                className="h-4 w-4"
              />
              Sign in with Google
            </Button>
            <Button asChild variant="secondary" className="w-full">
              <Link to="/signup">Create Account</Link>
            </Button>
            <Button asChild variant="ghost" className="w-full">
              <Link to="/">Back to Home</Link>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

