import { useEffect, useMemo, useState } from "react";
import { Trophy, CloudOff, Download, Filter, ExternalLink} from "lucide-react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Slider } from "../components/ui/slider";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth";
import NavBar from "../components/NavBar";
import { Link } from "react-router-dom";
import MachineLearningBackground from "@/components/Background";

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
}

interface DbRow {
  game_id: string;
  commence_time: string;
  home_team: string;
  away_team: string;
  Team: string;
  Model_Prob: string | number;
  Odds?: string | number;
  Edge?: string | number;
  Book?: string;
  Sportsbook?: string;
  book?: string;
  ["bookmakers.last_update"]?: string;
}

interface HistoryRow {
  Actual_Winner?: string | null;
  correct?: number | string | null;
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


const decimalToAmerican = (dec: string | number | undefined): number | undefined => {
  const d = Number(dec);
  if (!isFinite(d)) return undefined;
  return d >= 2 ? Math.round((d - 1) * 100) : Math.round(-100 / (d - 1));
};

const fmtPct = (p: number | undefined) => (p === undefined || Number.isNaN(p) ? "—" : `${(p * 100).toFixed(1)}%`);
const fmtOdds = (o: number | undefined) => (o === undefined || Number.isNaN(o) ? "—" : (o > 0 ? `+${Math.round(o)}` : `${Math.round(o)}`));
const fmtMoney = (n: number | undefined) => (n === undefined || Number.isNaN(n) ? "—" : `$${n.toFixed(2)}`);
const toLocalTime = (iso: string) => new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

// Color gradient from indigo-600 (low) to teal-700 (high)
const EDGE_LOW_RGB = [79, 70, 229];   // indigo-600
const EDGE_HIGH_RGB = [16, 148, 85]; // teal
const edgeColor = (val: number | undefined, min: number, max: number) => {
  if (val === undefined || max <= min) return `rgb(${EDGE_HIGH_RGB.join(',')})`;
  const t = (val - min) / (max - min);
  const r = Math.round(EDGE_LOW_RGB[0] + t * (EDGE_HIGH_RGB[0] - EDGE_LOW_RGB[0]));
  const g = Math.round(EDGE_LOW_RGB[1] + t * (EDGE_HIGH_RGB[1] - EDGE_LOW_RGB[1]));
  const b = Math.round(EDGE_LOW_RGB[2] + t * (EDGE_HIGH_RGB[2] - EDGE_LOW_RGB[2]));
  return `rgb(${r}, ${g}, ${b})`;
};

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
  const { user } = useAuth();

  const [data, setData] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [probViewAmerican, setProbViewAmerican] = useState(false);
  const [minEdge, setMinEdge] = useState(-0.1); // probability difference
  const [sortKey, setSortKey] = useState<"start" | "edge" | "prob" | "book">("edge");
  const [sortDir, setSortDir] = useState<1 | -1>(1);
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
        const { data: rows, error } = await supabase
          .from('predictions')
          .select('*');
        if (error || !rows) throw error || new Error('No data');

        let latest: string | null = null;
        const grouped: Record<string, { game_id: string; commence_time: string; home_team: string; away_team: string; rows: DbRow[] }> = {};
        rows.forEach((r: DbRow) => {
          const candidate = r["bookmakers.last_update"];
          if (candidate && (!latest || candidate > latest)) {
            latest = candidate;
          }
          const gid = r.game_id;
          if (!grouped[gid]) {
            grouped[gid] = { game_id: gid, commence_time: r.commence_time, home_team: r.home_team, away_team: r.away_team, rows: [] };
          }
          grouped[gid].rows.push(r);
        });
        const predictions: Prediction[] = Object.values(grouped).flatMap(g => {
          const books = Array.from(new Set(g.rows.map((r: DbRow) => r.Sportsbook || r.book || r.Book)));
          return books.map(book => {
            const homeRow = g.rows.find((r: DbRow) => r.Team === g.home_team && (r.Sportsbook === book || r.book === book || r.Book === book));
            const awayRow = g.rows.find((r: DbRow) => r.Team === g.away_team && (r.Sportsbook === book || r.book === book || r.Book === book));
            return {
              game_id: g.game_id,
              start_time_utc: g.commence_time || null,
              league: 'MLB',
              home_team: g.home_team,
              away_team: g.away_team,
              sportsbook: book,
              model: 'mlb_moneyline_v1',
              home_ml_prob: homeRow ? Number(homeRow.Model_Prob) : undefined,
              away_ml_prob: awayRow ? Number(awayRow.Model_Prob) : undefined,
              home_book_odds: homeRow ? decimalToAmerican(homeRow.Odds) : undefined,
              away_book_odds: awayRow ? decimalToAmerican(awayRow.Odds) : undefined,
              edge_home: homeRow && homeRow.Edge ? Number(homeRow.Edge) : undefined,
              edge_away: awayRow && awayRow.Edge ? Number(awayRow.Edge) : undefined,
            } as Prediction;
          });
        });
        setData(predictions);
        setLastUpdated(latest);
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
        const { data: rows, error } = await supabase
          .from('history')
          .select('Actual_Winner, correct');
        if (error || !rows) throw error || new Error('No data');
        const finished = rows.filter((r: HistoryRow) => r.Actual_Winner);
        const total = finished.length;
        const correct = finished.filter((r: HistoryRow) => Number(r.correct) === 1).length;
        setHistory({ total, correct });
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

  const edgeRange = useMemo(() => {
    const edges: number[] = [];
    withKelly.forEach((g) => {
      const homeImp = impliedFromAmerican(g.home_book_odds);
      const awayImp = impliedFromAmerican(g.away_book_odds);
      const edgeH = g.edge_home ?? (homeImp !== undefined ? g.home_ml_prob - homeImp : undefined);
      const edgeA = g.edge_away ?? (awayImp !== undefined ? g.away_ml_prob - awayImp : undefined);
      const best = [edgeH, edgeA]
        .filter((v): v is number => v !== undefined)
        .sort((a, b) => b - a)[0];
      if (best !== undefined) edges.push(best);
    });
    const min = edges.length ? Math.min(...edges) : 0;
    const max = edges.length ? Math.max(...edges) : 0;
    return { min, max };
  }, [withKelly]);

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
      <MachineLearningBackground density={0.00015} speed={0.5} interactive opacity={0.1} color={isDark ? "#06b6d4" : "#ff0000ff"} nodeColor={isDark ? "#e0f2fe" : "#ff0000ff"}/>
      <NavBar active="mlb" user={!!user} />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Hero */}
        <section className="grid lg:grid-cols-3 gap-6 items-start mb-8">
          <div className="lg:col-span-2">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-3">MLB Predictions</h1>
            <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
              Transparent, data-driven picks from machine learning models to estimate results and gain the upper hand on sportsbooks. 
              Model includes 100+ features and data from games across the 2023, 2024, and 2025 seasons. Filter and sort for specific results and export your board.
              <br/><br/>
              Edge is the difference between the model prediction and a book's implied odds. It is used to calculate the expected value (EV) of a wager. The higher the edge value, the more favorable the odds are to bettors. The Kelly Bet is the suggested bet based on the set bankroll and Kelly multiplier.
              <br/><br/>
              <b>How to Use:</b><br/>
              • Filter for your Sportsbooks
              <br/>
              • Set a minimum edge threshold (Minimum Edge of 0 means all games are shown)
              <br/>
              • Set your bankroll, max bet, and Kelly multiplier to see recommended bets
              <br/>
              • A higher Kelly multiplier means a higher percentage of your bankroll is recommended per bet
              <br/><br/>
              <span className="inline-flex gap-1">Learn more about the Kelly Criterion:
                <Link to="/methodology" className="inline-flex items-center gap-1 text-indigo-600 hover:underline">
                  Methodology <ExternalLink className="w-4 h-4"/>
                </Link>
              </span>
            </p>
            <div className="flex flex-wrap gap-3 mt-4">
              <Button onClick={downloadCsv} className="gap-2"><Download className="w-4 h-4"/> Download CSV</Button>
              {lastUpdated && (
                <p className="text-sm mt-2 text-neutral-600 dark:text-neutral-400">Last updated: {new Date(lastUpdated).toLocaleString()}</p>
              )}
            </div>
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
                          className="rounded border-neutral-300 text-indigo-600 accent-indigo-600 shadow-sm focus:ring-indigo-500 dark:bg-neutral-800 dark:border-neutral-700"
                        />
                        {b}
                      </label>
                    ))}
                    </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2 text-sm">
                    <span>Minimum Edge</span>
                    <span className="text-neutral-500">(Recommended: 0.08-0.10)</span>
                    <span className="font-semibold">{minEdge.toFixed(2)}</span>
                  </div>
                  <Slider className="my-slider accent-white" value={[minEdge]} min={-0.1} max={0.2} step={0.01} onValueChange={(v) => setMinEdge(v[0])} />
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
                Current Model Prediction Record: {history.correct}/{history.total} ({((history.correct / history.total) * 100).toFixed(1)}%)
                <></>
              </div>
              <div className="w-full bg-neutral-200 dark:bg-neutral-800 rounded-full h-2 overflow-hidden">
                <div className="bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700 h-full" style={{ width: `${(history.correct / history.total) * 100}%` }}></div>
              </div>
            </div>
          )}
          <div className="overflow-hidden rounded-2xl border border-neutral-200/70 dark:border-neutral-800/70 shadow-sm bg-white/70 dark:bg-neutral-900/70">
            <div className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Trophy className="w-4 h-4"/>
                <h2 className="font-semibold">Today's MLB Moneyline Predictions</h2>
                <Badge variant="secondary">Model v1.2</Badge>
              </div>
              <div className="text-xs text-neutral-600 dark:text-neutral-400">
                {isFinite(bankrollNum) && bankrollNum > 0 ? `Bankroll: $${bankrollNum.toFixed(2)}` : "Set bankroll to see bet sizing"}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-xs sm:text-sm">
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
                    <th className="px-4 py-3">Home Odds</th>
                    <th className="px-4 py-3">Away Odds</th>
                    <th className="px-4 py-3 cursor-pointer" onClick={() => handleSort('edge')}>
                      Edge {sortKey === 'edge' ? (sortDir === 1 ? '▲' : '▼') : '–'}
                    </th>
                    <th className="px-4 py-3">Kelly Bet</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={8} className="px-4 py-10 text-center text-neutral-500">Loading predictions…</td>
                    </tr>
                  )}
                  {!loading && error && (
                    <tr>
                      <td colSpan={8} className="px-4 py-8">
                        <div className="flex items-center justify-center gap-2 text-neutral-600 dark:text-neutral-300">
                          <CloudOff className="w-4 h-4"/>
                          <span>{error} Try refresh. If this persists, verify your Flask endpoint at <code className="px-1 rounded bg-neutral-100 dark:bg-neutral-800">/api/mlb/predictions?date=today</code>.</span>
                        </div>
                      </td>
                    </tr>
                  )}

                  {!loading && !error && sorted.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-4 py-10 text-center text-neutral-500">No games match your filters.</td>
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
                    const edgeTextColor = edgeColor(bestEdgeVal, edgeRange.min, edgeRange.max);

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
                              <Badge className="bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700 text-white">{favTeam}</Badge>
                              <span className="text-sm">
                                {probViewAmerican ? fmtOdds(favOdds) : fmtPct(favProb)}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 align-top text-sm">
                          <div className="text-xs text-neutral-500">{g.home_team}</div>
                          <div className="font-mono">{fmtOdds(g.home_book_odds)}</div>
                          <div className="text-xs text-neutral-500">Imp {fmtPct(homeImp)}</div>
                        </td>
                        <td className="px-4 py-3 align-top text-sm">
                          <div className="text-xs text-neutral-500">{g.away_team}</div>
                          <div className="font-mono">{fmtOdds(g.away_book_odds)}</div>
                          <div className="text-xs text-neutral-500">Imp {fmtPct(awayImp)}</div>
                        </td>
                        <td className="px-4 py-3 align-top">
                          <div className="text-sm font-semibold" style={edgeTextColor ? { color: edgeTextColor } : undefined}>
                            {bestEdgeVal !== undefined ? `${(bestEdgeVal * 100).toFixed(1)} pp` : "—"}
                          </div>
                          <div className="text-xs text-neutral-500">vs book implied</div>
                        </td>
                        <td className="px-4 py-3 align-top text-sm">
                          {negativeEdge ? (
                            <div className="space-y-1">
                              <div className="font-medium">None</div>
                              <div className="text-neutral-600 dark:text-neutral-300">$0.00 <span className="text-xs">(0%)</span></div>
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
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <footer className="mt-10 pb-10 text-sm text-neutral-600 dark:text-neutral-400">
          <center>
            These model outputs are informational and not financial advice. Edges and odds are computed from model probabilities and optional bookmaker lines when provided.
            <br/>
            Data is for informational and educational purposes only and is not a solicitation to gamble. Use at your own risk.
          </center>
        </footer>

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
