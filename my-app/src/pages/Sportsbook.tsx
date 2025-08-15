import { useEffect, useMemo, useState } from "react";
import { Trophy, Sparkles, RefreshCcw, CloudOff, Download, Filter, HelpCircle, ExternalLink, HandCoins} from "lucide-react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";

// --- Types ---
interface Prediction {
  game_id: string;            // unique id for the matchup
  start_time_utc: string;     // ISO datetime
  league: string;             // e.g. "MLB"
  home_team: string;
  away_team: string;
  sportsbook?: string,
  model: string;              // e.g. "mlb_moneyline_v1"
  home_ml_prob: number;       // 0..1 probability home wins
  away_ml_prob: number;       // 0..1 probability away wins
  home_book_odds?: number;    // American odds from a book (optional)
  away_book_odds?: number;    // American odds from a book (optional)
  edge_home?: number;         // prob - implied (decimal)
  edge_away?: number;
  venue?: string;
  note?: string;              // optional model note
}

// --- Helpers ---
const americanFromProb = (p: number) => {
  if (p <= 0 || p >= 1 || Number.isNaN(p)) return NaN;
  return p > 0.5 ? -(p / (1 - p)) * 100 : ((1 - p) / p) * 100;
};
const impliedFromAmerican = (odds?: number) => {
  if (odds === undefined || odds === null || Number.isNaN(odds)) return undefined;
  if (odds > 0) return 100 / (odds + 100);
  return Math.abs(odds) / (Math.abs(odds) + 100);
};
const payoutB = (odds?: number) => {
  if (odds === undefined || odds === null || Number.isNaN(odds)) return undefined;
  return odds > 0 ? odds / 100 : 100 / Math.abs(odds); // net profit per 1 unit stake
};
// Full Kelly fraction: f* = (b*p - (1-p)) / b where b is net odds
const kellyFraction = (p: number | undefined, odds?: number) => {
  if (p === undefined || odds === undefined || Number.isNaN(p)) return undefined;
  const b = payoutB(odds);
  if (b === undefined) return undefined;
  const f = (b * p - (1 - p)) / b;
  if (!isFinite(f)) return undefined;
  return f; // may be negative
};

const fmtPct = (p: number | undefined) => (p === undefined || Number.isNaN(p) ? "—" : `${(p * 100).toFixed(1)}%`);
const fmtOdds = (o: number | undefined) => (o === undefined || Number.isNaN(o) ? "—" : (o > 0 ? `+${Math.round(o)}` : `${Math.round(o)}`));
const fmtMoney = (n: number | undefined) => (n === undefined || Number.isNaN(n) ? "—" : `$${n.toFixed(2)}`);
const toLocalTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

// --- Constants ---
const SPORTSBOOKS = ["BetUS", "BetMGM", "FanDuel", "DraftKings"] as const;

// --- Lightweight Internal Tests ---
function runInternalTests() {
  try {
    const approxEq = (a: number, b: number, eps = 0.02) => Math.abs(a - b) <= eps;

    // Prob/odds conversions
    console.assert(approxEq(impliedFromAmerican(-150)!, 0.6), "implied(-150) ≈ 0.6 failed");
    console.assert(approxEq(impliedFromAmerican(150)!, 0.4), "implied(+150) ≈ 0.4 failed");
    console.assert(Math.round(americanFromProb(0.6)) === -150, "americanFromProb(0.6) ~ -150");
    console.assert(Math.round(americanFromProb(0.4)) === 150, "americanFromProb(0.4) ~ +150");

    // Edge sanity: model 0.6 vs +100 (0.5 implied) => 0.1 (10pp)
    const edge = 0.6 - impliedFromAmerican(100)!;
    console.assert(approxEq(edge, 0.1, 0.001), "edge 0.6 vs +100 ~ 0.1");

    // Kelly fraction tests
    // +100, p=0.6 => b=1 => f = (1*0.6 - 0.4)/1 = 0.2
    console.assert(approxEq(kellyFraction(0.6, 100)!, 0.2, 1e-3), "Kelly p=0.6 @ +100 should be 0.2");
    // -150 => b=100/150=0.666..., p=0.65 => f ≈ (0.6667*0.65 - 0.35)/0.6667 ≈ 0.125
    console.assert(approxEq(kellyFraction(0.65, -150)!, 0.125, 0.01), "Kelly p=0.65 @ -150 ~ 0.125");

    // Stake capping: bankroll 1000, max bet 50, f=0.2, half Kelly => recommend 50 (cap)
    const bankroll = 1000, maxBet = 50, kMult = 0.5; // half-Kelly => 0.1 of roll => 100, capped to 50
    const stake = Math.min(bankroll * 0.2 * kMult, maxBet);
    console.assert(stake === 50, "Stake capping failed");

    console.info("✅ Internal tests passed");
  } catch (e) {
    console.error("❌ Internal tests encountered an error", e);
  }
}

// --- Component ---
export default function SportsbookHome() {
  const [data, setData] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [probViewAmerican, setProbViewAmerican] = useState(false);
  const [minEdge, setMinEdge] = useState(0.05); // probability difference
  const [sortKey, setSortKey] = useState<"start" | "edge" | "prob" | "book">("edge");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);
  const [selectedBooks, setSelectedBooks] = useState<string[]>([...SPORTSBOOKS]);

  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [history, setHistory] = useState<{ total: number; correct: number } | null>(null);

  // Bankroll / Kelly controls
  const [bankroll, setBankroll] = useState<string>(""); // keep as string for input control
  const [maxBet, setMaxBet] = useState<string>("");
  const [kellyMult, setKellyMult] = useState<number>(0.25); // 0..1 (e.g., 0.5 = half Kelly)

  useEffect(() => { runInternalTests(); }, []);

  useEffect(() => {
    const fetchPredictions = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/mlb/predictions?date=today`, { headers: { Accept: "application/json" } });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const payload = await res.json();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const preds: Prediction[] = (payload.predictions ?? []).map((p: any) => ({
          ...p,
          sportsbook: p.sportsbook ?? p.book ?? p.Sportsbook,
          home_ml_prob: p.home_ml_prob !== undefined ? Number(p.home_ml_prob) : undefined,
          away_ml_prob: p.away_ml_prob !== undefined ? Number(p.away_ml_prob) : undefined,
          home_book_odds: p.home_book_odds !== undefined ? Number(p.home_book_odds) : undefined,
          away_book_odds: p.away_book_odds !== undefined ? Number(p.away_book_odds) : undefined,
          edge_home: p.edge_home !== undefined ? Number(p.edge_home) : undefined,
          edge_away: p.edge_away !== undefined ? Number(p.edge_away) : undefined,
        }));
        setData(preds);
        setLastUpdated(payload.last_updated ?? null);
      } catch (err) {
        console.error(err);
        setError("Could not load today's MLB predictions.");
      } finally {
        setLoading(false);
      }
    };
    fetchPredictions();
  }, []);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/api/mlb/history', { headers: { Accept: 'application/json' } });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const payload = await res.json();
        setHistory(payload);
      } catch (err) {
        console.error(err);
      }
    };
    fetchHistory();
  }, []);

  const bankrollNum = useMemo(() => Number(bankroll), [bankroll]);
  const maxBetNum = useMemo(() => Number(maxBet), [maxBet]);

  const handleSort = (key: "start" | "edge" | "prob" | "book") => {
    if (sortKey === key) {
      setSortDir((d) => (d === 1 ? -1 : 1));
    } else {
      setSortKey(key);
      setSortDir(-1);
    }
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return data
      .filter((g) => selectedBooks.includes(g.sportsbook || ""))
      .filter((g) => q === "" ? true : [g.home_team, g.away_team, g.venue].some((s) => (s || "").toLowerCase().includes(q)))
      .filter((g) => {
        const homeImp = impliedFromAmerican(g.home_book_odds);
        const awayImp = impliedFromAmerican(g.away_book_odds);
        const edgeH = g.edge_home ?? (homeImp !== undefined ? (g.home_ml_prob - homeImp) : -Infinity);
        const edgeA = g.edge_away ?? (awayImp !== undefined ? (g.away_ml_prob - awayImp) : -Infinity);
        const bestEdge = Math.max(edgeH, edgeA);
        return bestEdge >= minEdge;
      });
  }, [data, query, minEdge, selectedBooks]);

  const withKelly = useMemo(() => {
    return filtered.map((g) => {
      // Kelly for each side
      const fHome = kellyFraction(g.home_ml_prob, g.home_book_odds);
      const fAway = kellyFraction(g.away_ml_prob, g.away_book_odds);
      const fHomeAdj = fHome !== undefined ? Math.max(0, fHome * kellyMult) : undefined;
      const fAwayAdj = fAway !== undefined ? Math.max(0, fAway * kellyMult) : undefined;

      const bank = isFinite(bankrollNum) && bankrollNum > 0 ? bankrollNum : undefined;
      const cap = isFinite(maxBetNum) && maxBetNum > 0 ? maxBetNum : undefined;

      const stakeHome = bank && fHomeAdj !== undefined ? Math.max(0, bank * fHomeAdj) : undefined;
      const stakeAway = bank && fAwayAdj !== undefined ? Math.max(0, bank * fAwayAdj) : undefined;

      const stakeHomeCapped = cap !== undefined && stakeHome !== undefined ? Math.min(stakeHome, cap) : stakeHome;
      const stakeAwayCapped = cap !== undefined && stakeAway !== undefined ? Math.min(stakeAway, cap) : stakeAway;

      let recSide: "HOME" | "AWAY" | undefined;
      let recStake: number | undefined;
      let recFrac: number | undefined;

      if ((stakeHomeCapped ?? -1) >= (stakeAwayCapped ?? -1) && stakeHomeCapped !== undefined && stakeHomeCapped > 0) {
        recSide = "HOME";
        recStake = stakeHomeCapped;
        recFrac = fHomeAdj;
      } else if (stakeAwayCapped !== undefined && stakeAwayCapped > 0) {
        recSide = "AWAY";
        recStake = stakeAwayCapped;
        recFrac = fAwayAdj;
      }

      return { ...g, recSide, recStake, recFrac } as Prediction & { recSide?: "HOME"|"AWAY"; recStake?: number; recFrac?: number };
    });
  }, [filtered, bankrollNum, maxBetNum, kellyMult]);

  const sorted = useMemo(() => {
    const arr = [...withKelly];
    arr.sort((a, b) => {
      const key = sortKey; const dir = sortDir;
      if (key === "start") {
        return dir * (new Date(a.start_time_utc).getTime() - new Date(b.start_time_utc).getTime());
      }
      if (key === "book") {
        const as = (a.sportsbook || "").toLowerCase();
        const bs = (b.sportsbook || "").toLowerCase();
        return dir * (as > bs ? 1 : as < bs ? -1 : 0);
      }
      const aHomeImp = impliedFromAmerican(a.home_book_odds);
      const aAwayImp = impliedFromAmerican(a.away_book_odds);
      const bHomeImp = impliedFromAmerican(b.home_book_odds);
      const bAwayImp = impliedFromAmerican(b.away_book_odds);
      const aEdge = Math.max(
        (a.edge_home ?? (aHomeImp !== undefined ? (a.home_ml_prob - aHomeImp) : -Infinity)),
        (a.edge_away ?? (aAwayImp !== undefined ? (a.away_ml_prob - aAwayImp) : -Infinity))
      );
      const bEdge = Math.max(
        (b.edge_home ?? (bHomeImp !== undefined ? (b.home_ml_prob - bHomeImp) : -Infinity)),
        (b.edge_away ?? (bAwayImp !== undefined ? (b.away_ml_prob - bAwayImp) : -Infinity))
      );
      if (key === "edge") return dir * (bEdge - aEdge);
      const aProb = Math.max(a.home_ml_prob, a.away_ml_prob);
      const bProb = Math.max(b.home_ml_prob, b.away_ml_prob);
      return dir * (bProb - aProb);
    });
    return arr;
  }, [withKelly, sortKey, sortDir]);

  const downloadCsv = () => {
    const rows = [
      [
        "game_id","start_time_local","away_team","home_team","sportsbook","home_prob","away_prob","home_model_odds","away_model_odds","home_book_odds","away_book_odds","edge_home","edge_away",
      ],
      ...sorted.map((g) => {
        const homeModelOdds = americanFromProb(g.home_ml_prob);
        const awayModelOdds = americanFromProb(g.away_ml_prob);
        const homeImp = impliedFromAmerican(g.home_book_odds);
        const awayImp = impliedFromAmerican(g.away_book_odds);
        const edgeH = g.edge_home ?? (homeImp !== undefined ? (g.home_ml_prob - homeImp) : undefined);
        const edgeA = g.edge_away ?? (awayImp !== undefined ? (g.away_ml_prob - awayImp) : undefined);
        return [
          g.game_id,
          toLocalTime(g.start_time_utc),
          g.away_team,
          g.home_team,
          g.sportsbook || "",
          g.home_ml_prob,
          g.away_ml_prob,
          isFinite(homeModelOdds) ? Math.round(homeModelOdds) : "",
          isFinite(awayModelOdds) ? Math.round(awayModelOdds) : "",
          g.home_book_odds ?? "",
          g.away_book_odds ?? "",
          edgeH !== undefined ? (edgeH * 100).toFixed(2) : "",
          edgeA !== undefined ? (edgeA * 100).toFixed(2) : "",
        ];
      })
    ];
    const csv = rows.map(r => r.map((v) => typeof v === "string" ? `"${v.replaceAll('"','""')}"` : String(v)).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mlb_predictions_today.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const Header = () => (
    <header className="sticky top-0 z-30 backdrop-blur bg-white/70 dark:bg-neutral-900/70 border-b border-neutral-200 dark:border-neutral-800">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-2xl bg-gradient-to-br from-indigo-500 via-sky-500 to-emerald-500 text-white shadow-md">
            <HandCoins className="w-5 h-5" />
          </div>
          <span className="text-xl font-semibold tracking-tight">UpperHand</span>
          <Badge variant="secondary" className="ml-1">Beta</Badge>
        </div>
        <nav className="ml-auto flex items-center gap-1">
          <Button variant="ghost" className="gap-2" disabled>
            <Sparkles className="w-4 h-4" /> NFL <span className="opacity-50">(soon)</span>
          </Button>
          <Button variant="ghost" className="gap-2" disabled>
            NBA <span className="opacity-50">(soon)</span>
          </Button>
          <Button variant="ghost" className="gap-2 text-indigo-500">
            <Trophy className="w-4 h-4" /> MLB
          </Button>
          <Button asChild variant="ghost" className="gap-2">
            <a href="/about"><HelpCircle className="w-4 h-4"/> About</a>
          </Button>
        </nav>
      </div>
    </header>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 via-white to-emerald-50 dark:from-neutral-900 dark:via-neutral-950 dark:to-neutral-900 text-neutral-900 dark:text-neutral-100">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Hero */}
        <section className="grid lg:grid-cols-3 gap-6 items-start mb-8">
          <div className="lg:col-span-2">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-3">MLB Predictions</h1>
            <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
              Transparent, data-driven picks from machine learning models to estimate results and gain the upper hand on sportsbooks. 
              Model includes 100+ features and data from games across the 2023, 2024, and 2025 seasons. Filter and sort for specific results and export your board.
            </p>
            <br></br>
            <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
              The Kelly Criterion is a bankroll management strategy that helps you decide how much to wager based on your edge over the sportsbook’s odds. 
              It aims to maximize long-term growth while reducing the risk of going broke. The formula uses the estimated win probability from the ML model,
              sportsbooks' odds, and your current bankroll. The Kelly Criterion helps you avoid betting too much when your edge is small and bet more when your advantage is big.
              Our system automatically applies this method to give you a recommended bet size so you can bet smarter, not just bigger.
            </p>
            <br></br>
            <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
              Edge is used to calculate the expected value (EV) of a wager. The Kelly Bet is the suggested bet based on your bankroll and Kelly multiplier.
              Increase the Minimum Edge to be more conservative on bets. Changing Kelly Multiplier adjusts percentage of Bankroll that is used for bet.
            </p>
            <div className="flex flex-wrap gap-3 mt-4">
              <Button onClick={downloadCsv} className="gap-2"><Download className="w-4 h-4"/> Export CSV</Button>
              <Button variant="secondary" onClick={() => window.location.reload()} className="gap-2"><RefreshCcw className="w-4 h-4"/> Refresh</Button>
              <a href="/methodology" className="inline-flex items-center gap-2 text-indigo-500 hover:underline">
                Methodology <ExternalLink className="w-4 h-4"/>
              </a>
            </div>
            {lastUpdated && (
              <p className="text-sm mt-2 text-neutral-600 dark:text-neutral-400">Last updated: {new Date(lastUpdated).toLocaleString()}</p>
            )}
          </div>

          {/* Kelly Controls */}
          <div>
            <Card className="rounded-2xl shadow-md border-neutral-200/70 dark:border-neutral-800/70">
              <CardContent className="p-4 grid gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4"/>
                  <span className="font-medium">Filters & Betting Controls</span>
                </div>
                <Input placeholder="Search team" value={query} onChange={(e) => setQuery(e.target.value)} />
                <div>
                  <label className="text-xs text-neutral-500">Sportsbooks</label>
                  <div className="mt-1 grid grid-cols-2 gap-1">
                    {SPORTSBOOKS.map((b) => (
                      <label key={b} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={selectedBooks.includes(b)}
                          onChange={(e) =>
                            setSelectedBooks((prev) =>
                              e.target.checked
                                ? [...prev, b]
                                : prev.filter((sb) => sb !== b)
                            )
                          }
                          className="rounded border-neutral-300 text-indigo-600 shadow-sm focus:ring-indigo-500 dark:bg-neutral-800 dark:border-neutral-700"
                        />
                        {b}
                      </label>
                    ))}
                    </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2 text-sm">
                    <span>Minimum Edge</span>
                    <span className="text-neutral-500">(Recommended: 0.04-0.06)</span>
                    <span className="font-semibold">{minEdge.toFixed(2)}</span>
                  </div>
                  <Slider className="my-slider accent-white" value={[minEdge]} min={0} max={0.2} step={0.01} onValueChange={(v) => setMinEdge(v[0])} />
                </div>
                <div className="flex items-center gap-3">
                  <Switch checked={probViewAmerican} onCheckedChange={setProbViewAmerican} id="view-odds" />
                  <label htmlFor="view-odds" className="text-sm select-none">Show model odds as American</label>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-neutral-500">Bankroll ($)</label>
                    <Input inputMode="decimal" value={bankroll} onChange={(e) => setBankroll(e.target.value.replace(/[^0-9.]/g, ''))} placeholder="e.g. 1000" />
                  </div>
                  <div>
                    <label className="text-xs text-neutral-500">Max Bet ($)</label>
                    <Input inputMode="decimal" value={maxBet} onChange={(e) => setMaxBet(e.target.value.replace(/[^0-9.]/g, ''))} placeholder="optional" />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2 text-sm">
                    <span>Kelly Multiplier</span>
                    <span className="font-semibold">{(kellyMult * 100).toFixed(0)}%</span>
                  </div>
                  <Slider value={[kellyMult]} min={0} max={1} step={0.05} onValueChange={(v) => setKellyMult(v[0])} />
                  <p className="text-xs text-neutral-500 mt-1">0% = no bet, 100% = full Kelly. Default 25%.</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Table */}
        <section>
        {history && history.total > 0 && (
            <div className="mb-4">
              <div className="text-sm mb-1 font-medium">
                All-time Model Prediction Record: {history.correct}/{history.total} ({((history.correct / history.total) * 100).toFixed(1)}%)
              </div>
              <div className="w-full bg-neutral-200 dark:bg-neutral-800 rounded-full h-2 overflow-hidden">
                <div className="bg-green-600 h-full" style={{ width: `${(history.correct / history.total) * 100}%` }}></div>
              </div>
            </div>
          )}
          <div className="overflow-hidden rounded-2xl border border-neutral-200/70 dark:border-neutral-800/70 shadow-sm bg-white/70 dark:bg-neutral-900/70">
            <div className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Trophy className="w-4 h-4"/>
                <h2 className="font-semibold">Today's MLB Moneyline Predictions</h2>
                <Badge variant="secondary">Model v1</Badge>
              </div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400">
                {isFinite(bankrollNum) && bankrollNum > 0 ? `Bankroll: $${bankrollNum.toFixed(2)}` : "Set bankroll to see bet sizing"}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-neutral-100/60 dark:bg-neutral-800/60">
                  <tr className="text-left">
                    <th className="px-4 py-3 cursor-pointer" onClick={() => handleSort('start')}>
                      Time {sortKey === 'start' ? (sortDir === 1 ? '▲' : '▼') : '–'}
                    </th>
                    <th className="px-4 py-3">Matchup</th>
                    <th className="px-4 py-3 cursor-pointer" onClick={() => handleSort('book')}>
                      Sportsbook {sortKey === 'book' ? (sortDir === 1 ? '▲' : '▼') : '–'}
                    </th>
                    <th className="px-4 py-3 cursor-pointer" onClick={() => handleSort('prob')}>
                      Model Prediction {sortKey === 'prob' ? (sortDir === 1 ? '▲' : '▼') : '–'}
                    </th>
                    <th className="px-4 py-3">Book Odds</th>
                    <th className="px-4 py-3 cursor-pointer" onClick={() => handleSort('edge')}>
                      Edge {sortKey === 'edge' ? (sortDir === 1 ? '▲' : '▼') : '–'}
                    </th>
                    <th className="px-4 py-3">Kelly Bet</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={7} className="px-4 py-10 text-center text-neutral-500">Loading predictions…</td>
                    </tr>
                  )}
                  {!loading && error && (
                    <tr>
                      <td colSpan={7} className="px-4 py-8">
                        <div className="flex items-center justify-center gap-2 text-neutral-600 dark:text-neutral-300">
                          <CloudOff className="w-4 h-4"/>
                          <span>{error} Try refresh. If this persists, verify your Flask endpoint at <code className="px-1 rounded bg-neutral-100 dark:bg-neutral-800">/api/mlb/predictions?date=today</code>.</span>
                        </div>
                      </td>
                    </tr>
                  )}

                  {!loading && !error && sorted.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-10 text-center text-neutral-500">No games match your filters.</td>
                    </tr>
                  )}

                  {!loading && !error && sorted.map((g) => {
                    const homeModelOdds = americanFromProb(g.home_ml_prob);
                    const awayModelOdds = americanFromProb(g.away_ml_prob);
                    const homeImp = impliedFromAmerican(g.home_book_odds);
                    const awayImp = impliedFromAmerican(g.away_book_odds);
                    const edgeH = g.edge_home ?? (homeImp !== undefined ? (g.home_ml_prob - homeImp) : undefined);
                    const edgeA = g.edge_away ?? (awayImp !== undefined ? (g.away_ml_prob - awayImp) : undefined);

                    const favIsHome = g.home_ml_prob >= g.away_ml_prob;
                    const favTeam = favIsHome ? g.home_team : g.away_team;
                    const favProb = favIsHome ? g.home_ml_prob : g.away_ml_prob;
                    const favOdds = favIsHome ? homeModelOdds : awayModelOdds;

                    const bestEdgeVal = [edgeH, edgeA]
                      .filter((v): v is number => v !== undefined)
                      .sort((a, b) => b - a)[0];
                    const negativeEdge = bestEdgeVal !== undefined && bestEdgeVal < 0;

                    return (
                      <tr key={`${g.game_id}-${g.sportsbook}`} className="border-t border-neutral-200/60 dark:border-neutral-800/60">
                        <td className="px-4 py-3 align-top whitespace-nowrap">{toLocalTime(g.start_time_utc)}</td>
                        <td className="px-4 py-3 align-top">
                          <div className="font-medium">{g.away_team} <span className="opacity-60">@</span> {g.home_team}</div>
                        </td>

                        <td className="px-4 py-3 align-top whitespace-nowrap">{g.sportsbook || "—"}</td>
                        <td className="px-4 py-3 align-top">
                          <div className="flex flex-col gap-1">
                            <div className="text-xs uppercase tracking-wide text-neutral-500">Favored</div>
                            <div className="flex items-center gap-2">
                              <Badge className="bg-green-600">{favTeam}</Badge>
                              <span className="text-sm">
                                {probViewAmerican ? fmtOdds(favOdds) : fmtPct(favProb)}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 align-top">
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <div className="text-xs text-neutral-500">{g.home_team}</div>
                              <div className="font-mono">{fmtOdds(g.home_book_odds)}</div>
                              <div className="text-xs text-neutral-500">Imp {fmtPct(homeImp)}</div>
                            </div>
                            <div>
                              <div className="text-xs text-neutral-500">{g.away_team}</div>
                              <div className="font-mono">{fmtOdds(g.away_book_odds)}</div>
                              <div className="text-xs text-neutral-500">Imp {fmtPct(awayImp)}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 align-top">
                          <div className={`text-sm font-semibold ${bestEdgeVal !== undefined ? 'text-green-600' : ''}`}>{bestEdgeVal !== undefined ? `${(bestEdgeVal * 100).toFixed(1)} pp` : "—"}</div>
                          <div className="text-xs text-neutral-500">vs book implied</div>
                        </td>
                        <td className="px-4 py-3 align-top text-sm">
                          {negativeEdge ? (
                            <div className="space-y-1">
                              <div className="font-medium">None</div>
                              <div className="text-neutral-600 dark:text-neutral-300">0</div>
                            </div>
                          ) : g.recSide ? (
                            <div className="space-y-1">
                              <div className="font-medium">{g.recSide === 'HOME' ? g.home_team : g.away_team}</div>
                              <div className="text-neutral-600 dark:text-neutral-300">{fmtMoney(g.recStake)} <span className="text-xs">({fmtPct(g.recFrac)})</span></div>
                            </div>
                          ) : (
                            <span className="text-neutral-500">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 align-top text-sm text-neutral-700 dark:text-neutral-300">{g.note || ""}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="mt-10 pb-10 text-sm text-neutral-600 dark:text-neutral-400">
          <p>
            These model outputs are informational and not financial advice. Edges and odds are computed from model probabilities and optional bookmaker lines when provided.
          </p>
        </footer>
      </main>
    </div>
  );
}
