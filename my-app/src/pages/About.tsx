import { Card, CardContent } from "../components/ui/card";
import { ArrowLeft } from "lucide-react";

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 via-white to-emerald-50 dark:from-neutral-900 dark:via-neutral-950 dark:to-neutral-900 text-neutral-900 dark:text-neutral-100">
      <header className="sticky top-0 z-30 backdrop-blur bg-white/70 dark:bg-neutral-900/70 border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center">
          <a href="/mlb" className="inline-flex items-center gap-2 text-sm text-indigo-500 hover:underline">
            <ArrowLeft className="w-4 h-4" />
            Back
          </a>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        <h1 className="text-3xl font-bold">About</h1>
        <Card className="rounded-2xl border-border/70 shadow-sm">
          <CardContent className="p-6 space-y-4 text-sm leading-relaxed">
            <p>
              EdgeFinder is a personal project that applies machine learning to sports betting markets. It currently focuses on MLB moneylines and is in beta.
            </p>
            <p>
              The goal is to surface value by comparing model probabilities with sportsbook odds and to suggest bet sizes using Kelly staking.
            </p>
            <p>
              This site is for informational and educational purposes only and is not a solicitation to gamble. Use at your own risk.
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}