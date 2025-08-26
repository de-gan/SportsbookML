import { useMemo, useState } from "react";
import { useAuth } from "../lib/auth";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  Brain,
  BarChart3,
  Sparkles,
  LineChart,
  Wallet,
  Info,
  ExternalLink,
  BadgeDollarSign,
  CircleStar,
} from "lucide-react";
import { BiBaseball } from "react-icons/bi";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import NavBar from "../components/NavBar";
import MachineLearningBackground from "@/components/Background";

// --- small helpers for the demo calculator ---
const impliedFromAmerican = (odds?: number) => {
  if (odds === undefined || odds === null || Number.isNaN(odds)) return undefined;
  if (odds > 0) return 100 / (odds + 100);
  return Math.abs(odds) / (Math.abs(odds) + 100);
};
const payoutB = (odds?: number) => {
  if (odds === undefined || odds === null || Number.isNaN(odds)) return undefined;
  return odds > 0 ? odds / 100 : 100 / Math.abs(odds); // net profit per 1 unit stake
};
const kellyFraction = (p: number | undefined, odds?: number) => {
  if (p === undefined || odds === undefined || Number.isNaN(p)) return undefined;
  const b = payoutB(odds);
  if (b === undefined) return undefined;
  const f = (b * p - (1 - p)) / b;
  if (!isFinite(f)) return undefined;
  return Math.max(0, f); // clip negatives for display
};
const fmtMoney = (n: number | undefined) => (n === undefined || Number.isNaN(n) ? "—" : `$${n.toFixed(2)}`);

export default function HomeLanding() {
  // Check auth state
  const { user } = useAuth();

  // Demo Kelly widget state
  const [bankroll, setBankroll] = useState<string>("1000");
  const [prob, setProb] = useState<string>("0.60"); // 0..1
  const [odds, setOdds] = useState<string>("-110"); // american
  const [mult, setMult] = useState<string>("0.5"); // 0..1

  const kelly = useMemo(() => {
    const p = Number(prob);
    const o = Number(odds);
    const f = kellyFraction(isFinite(p) ? p : undefined, isFinite(o) ? o : undefined);
    return f;
  }, [prob, odds]);
  const rec = useMemo(() => {
    const br = Number(bankroll);
    const m = Number(mult);
    if (!isFinite(br) || br <= 0 || !isFinite(m)) return { frac: kelly, stake: undefined };
    const fAdj = kelly !== undefined ? kelly * m : undefined;
    const stake = fAdj !== undefined ? Math.max(0, br * fAdj) : undefined;
    return { frac: fAdj, stake };
  }, [bankroll, mult, kelly]);

  return (
    <div className="min-h-screen text-neutral-900 dark:text-neutral-100">
      <MachineLearningBackground density={0.0001} speed={0.5} interactive opacity={0.2} />
      {/* Top nav */}
      <NavBar active="home" user={!!user}/>

      <main className="max-w-7xl mx-auto px-4 py-10">
        {/* Hero */}
        <section className="grid lg:grid-cols-2 gap-8 items-center">
          <motion.div initial={{opacity:0, y:8}} animate={{opacity:1, y:0}} transition={{duration:0.45}}>
            <h1 className="text-3xl md:text-5xl font-bold tracking-tight mb-4">
              Bet smarter with <span className="bg-gradient-to-r from-cyan-700 via-indigo-600 to-teal-700 bg-clip-text text-transparent">machine learning</span>
            </h1>
            <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed text-lg">
              UpperHand turns data into decisions. Explore transparent, model-driven predictions—starting with
              <span className="font-semibold"> MLB moneylines</span>—and see recommended bet sizes using Kelly staking.
            </p>
            <div className="flex flex-wrap gap-3 mt-5">
              <Button asChild size="lg" className="gap-2">
                {user ? (
                  <Link to="/mlb"><BiBaseball className="w-4 h-4"/> Explore Today’s MLB Picks</Link>
                ) : (
                  <Link to="/signup"><CircleStar className="w-4 h-4"/>Register Now!</Link>
                )}
              </Button>
              <Button asChild variant="secondary" size="lg" className="gap-2">
                <Link to="/methodology"><Brain className="w-4 h-4"/> Methodology</Link>
              </Button>
            </div>
            <div className="mt-4 text-sm text-neutral-600 dark:text-neutral-400">Realtime slate, sortable edges, CSV export, and more.</div>
          </motion.div>

          {/* Demo Kelly widget */}
          <motion.div initial={{opacity:0, scale:0.98}} animate={{opacity:1, scale:1}} transition={{duration:0.45}}>
            <Card className="rounded-2xl shadow-md border-border/70">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Wallet className="w-4 h-4"/>
                  <span className="font-medium">Kelly Bet Sizing — Try it</span>
                  <Badge variant="secondary" className="ml-auto">Interactive</Badge>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <label className="text-xs text-neutral-500">Bankroll ($)
                    <Input inputMode="decimal" value={bankroll} onChange={(e)=>setBankroll(e.target.value.replace(/[^0-9.]/g, ''))} placeholder="1000" className="mt-1"/>
                  </label>
                  <label className="text-xs text-neutral-500">Book Odds (±)
                    <Input inputMode="numeric" value={odds} onChange={(e)=>setOdds(e.target.value.replace(/[^0-9-]/g, ''))} placeholder="-110" className="mt-1"/>
                  </label>
                  <label className="text-xs text-neutral-500">Win Probability (0–1)
                    <Input inputMode="decimal" value={prob} onChange={(e)=>setProb(e.target.value.replace(/[^0-9.]/g, ''))} placeholder="0.60" className="mt-1"/>
                  </label>
                  <label className="text-xs text-neutral-500">Kelly Multiplier (0–1)
                    <Input inputMode="decimal" value={mult} onChange={(e)=>setMult(e.target.value.replace(/[^0-9.]/g, ''))} placeholder="0.50" className="mt-1"/>
                  </label>
                </div>
                <div className="mt-4 grid sm:grid-cols-3 gap-3">
                  <div className="rounded-xl border border-border/70 p-3 text-sm">
                    <div className="text-xs text-neutral-500">Implied (book)</div>
                    <div className="font-semibold">{(() => { const p = impliedFromAmerican(Number(odds)); return p !== undefined ? `${(p*100).toFixed(1)}%` : "—"; })()}</div>
                  </div>
                  <div className="rounded-xl border border-border/70 p-3 text-sm">
                    <div className="text-xs text-neutral-500">Kelly Fraction</div>
                    <div className="font-semibold">{kelly !== undefined ? `${(kelly*100).toFixed(1)}%` : "—"}</div>
                  </div>
                  <div className="rounded-xl border border-border/70 p-3 text-sm">
                    <div className="text-xs text-neutral-500">Suggested Stake</div>
                    <div className="font-semibold">{fmtMoney(rec.stake)}</div>
                  </div>
                </div>
                <div className="mt-3 text-xs text-neutral-500">
                  Kelly = max(0, (b·p − (1−p)) / b). We use your probability and the book’s odds; multiplier lets you run half‑Kelly or custom.
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </section>

        {/* Value props */}
        <section className="mt-12 grid md:grid-cols-3 gap-6">
          {[
            { icon: <BarChart3 className="w-5 h-5"/>, title: "Model‑Driven Picks", desc: "Transparent probabilities and edges, updated daily for MLB." },
            { icon: <LineChart className="w-5 h-5"/>, title: "Edges at a Glance", desc: "Sort and filter to surface the best discrepancies vs. book lines." },
            { icon: <BadgeDollarSign className="w-5 h-5"/>, title: "Bankroll‑Aware", desc: "Kelly staking guidance so sizing matches your risk tolerance." },
          ].map((f, i) => (
            <motion.div key={f.title} initial={{opacity:0, y:8}} whileInView={{opacity:1, y:0}} viewport={{once:true}} transition={{duration:0.35, delay:i*0.05}}>
              <Card className="rounded-2xl border-border/70 shadow-sm hover:shadow md:hover:shadow-md transition-shadow">
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="p-2 rounded-xl bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200">{f.icon}</span>
                    <h3 className="font-semibold">{f.title}</h3>
                  </div>
                  <p className="text-sm text-neutral-600 dark:text-neutral-300">{f.desc}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </section>

        {/* Roadmap / CTA */}
        <section className="mt-12 grid lg:grid-cols-3 gap-6">
          <motion.div initial={{opacity:0, y:8}} whileInView={{opacity:1, y:0}} viewport={{once:true}} transition={{duration:0.4}} className="lg:col-span-2">
            <Card className="rounded-2xl border-border/70">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4"/>
                  <h3 className="font-semibold">What’s next</h3>
                </div>
                <ul className="grid sm:grid-cols-2 gap-2 text-sm list-disc pl-5">
                  <li>NBA & NFL moneylines, spreads, and O/Us</li>
                  <li>Pricing EV calculators & portfolio view</li>
                  <li>Line movement & model versioning</li>
                  <li>CSV/API access for power users</li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{opacity:0, y:8}} whileInView={{opacity:1, y:0}} viewport={{once:true}} transition={{duration:0.45}}>
            <Card className="rounded-2xl border-border/70 bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700">
              <CardContent className="p-5">
                <h3 className="font-semibold text-white mb-2">Jump in</h3>
                <p className="text-sm/relaxed text-white/90 mb-4">See today’s projections and recommended stakes right now.</p>
                <Button asChild size="lg" variant="secondary" className="w-full bg-white/15 hover:bg-white/25 text-white border-white/30">
                  {user ? (
                    <Link to="/mlb"><BiBaseball className="w-4 h-4"/> Go to MLB Predictions</Link>
                  ) : (
                    <Link to="/login"><BiBaseball className="w-4 h-4"/> Go to MLB Predictions</Link>
                  )}
                </Button>
                <div className="text-xs text-white/80 mt-3 flex items-center gap-1">
                  <Info className="w-3.5 h-3.5"/> Not financial advice. For informational use only.
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </section>

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
