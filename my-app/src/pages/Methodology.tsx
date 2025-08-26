import { Card, CardContent } from "../components/ui/card";
import { ExternalLink } from "lucide-react";
import NavBar from "../components/NavBar";

export default function Methodology() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 via-white to-emerald-50 dark:from-neutral-900 dark:via-neutral-950 dark:to-neutral-900 text-neutral-900 dark:text-neutral-100">
      {/* Top nav */}
      <NavBar showAuthButton={false} />

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Model Methodology</h1>
        <Card className="rounded-2xl border-border/70 shadow-sm">
          <CardContent className="p-6 space-y-4">
            <p>
              Our MLB moneyline predictions come from a LightGBM model trained on multiple seasons (2023-present) of historical data.
            </p>
            <p>The model considers a wide range of features before each matchup, including:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li>Recent team form such as run differentials, ranks, and win streaks.</li>
              <li>Starting pitcher metrics (ERA, WAR, K/9, BB/9, WHIP, hard-hit rate).</li>
              <li>Offensive indicators from FanGraphs like wRC+, wOBA, and plate discipline stats.</li>
              <li>Bullpen strength via reliever WAR, FIP, WPA, and leverage metrics.</li>
              <li>Opponent equivalents for all team, pitcher, and bullpen features.</li>
              <li>Context like home/away and day/night splits.</li>
            </ul>
            <p>
              We compare predicted win probabilities to sportsbook lines to compute edges and recommend stakes using the Kelly Criterion.
            </p>
          </CardContent>
        </Card>

        {/* Footer */}
        <footer className="mt-12 pb-10 text-sm text-neutral-600 dark:text-neutral-400 flex flex-wrap items-center gap-2">
          <span>© {new Date().getFullYear()} UpperHand</span>
          <span className="opacity-50">•</span>
          <a href="/about" className="inline-flex items-center gap-1 hover:underline">About <ExternalLink className="w-3.5 h-3.5"/></a>
          <span className="opacity-50">•</span>
          <a href="/methodology" className="inline-flex items-center gap-1 hover:underline">Methodology <ExternalLink className="w-3.5 h-3.5"/></a>
        </footer>
      </main>
    </div>
  );
}

