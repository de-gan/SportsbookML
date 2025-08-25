import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const { error } = await supabase.auth.signUp({ email, password });
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
              Sign Up
            </Button>
            <Button asChild variant="secondary" className="w-full">
              <a href="/login">Back to Login</a>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
