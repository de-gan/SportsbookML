import { motion } from "framer-motion";
import { HandCoins, Trophy, Info } from "lucide-react";
import { BiBaseball, BiBasketball } from "react-icons/bi";
import { PiFootball } from "react-icons/pi";
import { Link } from "react-router-dom";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import ThemeToggle from "./ThemeToggle";
import AuthButton from "./AuthButton";

interface NavBarProps {
  active?: "home" | "mlb" | "about";
  showAuthButton?: boolean;
  user?: boolean;
}

export default function NavBar({ active, showAuthButton = true, user = false }: NavBarProps) {
  const activeClass = "bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700";
  return (
    <header className="sticky top-0 z-30 backdrop-blur bg-white/40 dark:bg-neutral-900/40">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col sm:flex-row items-center gap-3">
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="flex items-center gap-2"
        >
          <span className="p-2 rounded-2xl bg-gradient-to-br from-cyan-700 via-indigo-600 to-teal-700 text-white shadow-md">
            <HandCoins className="w-5 h-5" />
          </span>
          <span className="text-xl font-semibold tracking-tight">UpperHand</span>
          <Badge variant="secondary" className={`ml-1 ${activeClass}`}>Beta</Badge>
        </motion.div>
        <span className="ml-6 opacity-60">Dark Mode</span>
        <ThemeToggle />
        <nav className="flex flex-wrap items-center gap-1 w-full justify-center sm:w-auto sm:justify-end sm:ml-auto">
          <Button
            asChild
            variant="ghost"
            className={`gap-2 ${active === "home" ? activeClass : ""}`}
          >
            <Link to="/">
              <Trophy className="w-4 h-4" /> Home
            </Link>
          </Button>
          <Button
            asChild
            variant="ghost"
            className={`gap-2 ${active === "mlb" ? activeClass : ""}`}
          >

            <Link to={user ? "/mlb" : "/login"}>
              <BiBaseball className="w-4 h-4" /> MLB
            </Link>
          </Button>
          <Button variant="ghost" className="gap-2" disabled>
            <BiBasketball className="w-4 h-4" /> NBA <span className="opacity-60">(soon)</span>
          </Button>
          <Button variant="ghost" className="gap-2" disabled>
            <PiFootball className="w-4 h-4" /> NFL <span className="opacity-60">(soon)</span>
          </Button>
          <Button
            asChild
            variant="ghost"
            className={`gap-2 ${active === "about" ? activeClass : ""}`}
          >
            <Link to="/about">
              <Info className="w-4 h-4" /> About
            </Link>
          </Button>
          {showAuthButton && <AuthButton />}
        </nav>
      </div>
    </header>
  );
}
