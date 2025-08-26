import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import GoogleIcon from "@/assets/Google.svg"

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const localUrl = import.meta.env.VITE_SITE_URL as string

  const redirectUrl = `${
    localUrl || window.location.origin
  }`;

  const registerWithGoogle = async () => {
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: redirectUrl },
    });
    if (error) {
      setError(error.message);
    }
  };
  
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          display_name: displayName,
        },
      },
    });
    if (error) {
      setError(error.message);
    } else {
      setMessage("Check your email for a confirmation link.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <form className="space-y-4" onSubmit={handleSignUp}>
            <Input
              type="text"
              placeholder="Display Name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
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
            {message && <div className="text-sm text-green-600">{message}</div>}
            <Button type="submit" className="w-full">
              Register
            </Button>
            <Button
              type="button"
              className="w-full"
              onClick={registerWithGoogle}
            >
              <img
                src={GoogleIcon}
                alt="Google logo"
                className="h-4 w-4"
              />
              Sign up with Google
            </Button>
            <Button asChild variant="secondary" className="w-full">
              <Link to="/login">Already have an account?</Link>
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
