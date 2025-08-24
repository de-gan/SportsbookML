import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { motion } from "framer-motion";
import {
  HandCoins,
  Trophy,
  Info,
  ExternalLink
} from "lucide-react";
import { BiBaseball, BiBasketball } from "react-icons/bi";
import { PiFootball } from "react-icons/pi";

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 via-white to-emerald-50 dark:from-neutral-900 dark:via-neutral-950 dark:to-neutral-900 text-neutral-900 dark:text-neutral-100">
      {/* Top nav */}
      <header className="sticky top-0 z-30 backdrop-blur bg-white/70 dark:bg-neutral-900/70 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
          <motion.div initial={{opacity:0, y:-8}} animate={{opacity:1, y:0}} transition={{duration:0.35}} className="flex items-center gap-2">
            <span className="p-2 rounded-2xl bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700 text-white shadow-md">
              <HandCoins className="w-5 h-5" />
            </span>
            <span className="text-xl font-semibold tracking-tight">UpperHand</span>
            <Badge variant="secondary" className="ml-1 bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700">Beta</Badge>
          </motion.div>
          <nav className="ml-auto flex items-center gap-1">
            <Button asChild variant="ghost" className="gap-2"><a href="/"><Trophy className="w-4 h-4"/> Home</a></Button>
            <Button asChild variant="ghost" className="gap-2"><a href="/mlb"><BiBaseball className="w-4 h-4"/> MLB</a></Button>
            <Button variant="ghost" className="gap-2" disabled><BiBasketball className="w-4 h-4"/> NBA <span className="opacity-60">(soon)</span></Button>
            <Button variant="ghost" className="gap-2" disabled><PiFootball className="w-4 h-4"/> NFL <span className="opacity-60">(soon)</span></Button>
            <Button asChild variant="ghost" className="gap-2 bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700"><a href="/about"><Info className="w-4 h-4"/> About</a></Button>
          </nav>
        </div>
      </header>

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
          <a href="/about" className="inline-flex items-center gap-1 hover:underline">About <ExternalLink className="w-3.5 h-3.5"/></a>
          <span className="opacity-50">•</span>
          <a href="/methodology" className="inline-flex items-center gap-1 hover:underline">Methodology <ExternalLink className="w-3.5 h-3.5"/></a>
        </footer>
      </main>
    </div>
  );
}