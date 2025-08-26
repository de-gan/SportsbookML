import { useState, useEffect } from "react";
import { Card, CardContent } from "../components/ui/card";
import { ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import NavBar from "../components/NavBar";
import MachineLearningBackground from "@/components/Background";

export default function About() {
  const { user } = useAuth();
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

  return (
    <div className="min-h-screen text-neutral-900 dark:text-neutral-100">
      <MachineLearningBackground density={0.00015} speed={0.5} interactive opacity={0.2} color={isDark ? "#06b6d4" : "#ff0000ff"} nodeColor={isDark ? "#e0f2fe" : "#ff0000ff"}/>
      {/* Top nav */}
      <NavBar active="about" user={!!user} />

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <h1 className="text-3xl font-bold">About</h1>
        <Card className="rounded-2xl border-border/70 shadow-sm">
          <CardContent className="p-6 space-y-4 text-sm leading-relaxed">
            <p>
              UpperHand is a personal project that applies machine learning to sports betting markets. It currently focuses on MLB moneylines and is in beta.
            </p>
            <p>
              The goal is to surface value by comparing model probabilities with sportsbook odds and to suggest bet sizes using Kelly staking.
            </p>
            <p>
              This site is for informational and educational purposes only and is not a solicitation to gamble. Use at your own risk.
            </p>
          </CardContent>
        </Card>

        {/* Footer */}
        <footer className="mt-12 pb-10 text-sm text-neutral-600 dark:text-neutral-400 flex flex-wrap items-center gap-2">
          <span>© {new Date().getFullYear()} UpperHand</span>
          <span className="opacity-50">•</span>
          <Link to="/about" className="inline-flex items-center gap-1 hover:underline">About <ExternalLink className="w-3.5 h-3.5"/></Link>
          <span className="opacity-50">•</span>
          <Link to="/methodology" className="inline-flex items-center gap-1 hover:underline">Methodology <ExternalLink className="w-3.5 h-3.5"/></Link>
        </footer>
      </main>
    </div>
  );
}