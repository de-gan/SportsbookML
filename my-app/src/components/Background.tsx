import { useEffect, useRef, useState } from "react";

/**
 * MachineLearningBackground
 * ------------------------------------------------------------
 * A GPU‑friendly animated background with a subtle "machine learning" vibe:
 * - Particle nodes drift in a force field and connect when close (graph edges)
 * - Occasional "signal pulses" travel along edges (like activations)
 * - Soft procedural gradient glow for depth
 * - Optional mouse gravity for interactivity
 *
 * Props:
 *  - density       : number   (default 0.00008)  // nodes per pixel (scaled by viewport area)
 *  - speed         : number   (default 1)        // global motion multiplier [0.5..2]
 *  - color         : string   (default "#22d3ee") // edge + node tint (Tailwind cyan-400)
 *  - interactive   : boolean  (default true)     // mouse influence on nearby nodes
 *  - opacity       : number   (default 0.5)      // canvas global alpha
 *  - maxConnections: number   (default 3)        // clamp edges per node for performance
 *
 * Styling: uses Tailwind utility classes for a faint radial/linear glow layer.
 */

export default function MachineLearningBackground({
  density = 0.00008,
  speed = 1,
  color = "#22d3ee",
  interactive = true,
  opacity = 0.5,
  maxConnections = 3,
  nodeColor = "#e0f2fe",
}: {
  density?: number;
  speed?: number; // 0.5..2
  color?: string;
  interactive?: boolean;
  opacity?: number;
  maxConnections?: number;
  nodeColor?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [dpr, setDpr] = useState<number>(typeof window !== "undefined" ? Math.min(window.devicePixelRatio || 1, 2) : 1);
  const mouse = useRef({ x: 0, y: 0, active: false });

  useEffect(() => {
    const handleResize = () => {
      setDpr(Math.min(window.devicePixelRatio || 1, 2));
      const canvas = canvasRef.current;
      if (!canvas) return;
      const { innerWidth: w, innerHeight: h } = window;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [dpr]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true })!;
    if (!ctx) return;

    // Init particles
    const W = canvas.width;
    const H = canvas.height;

    const area = (W / dpr) * (H / dpr);
    const count = Math.max(40, Math.floor(area * density));

    type Node = {
      x: number; y: number; vx: number; vy: number; r: number; t: number;
      links: number[]; // indices of neighbors (updated each frame)
    };

    const rand = (min: number, max: number) => Math.random() * (max - min) + min;
    const nodes: Node[] = new Array(count).fill(0).map(() => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: rand(-0.3, 0.3) * speed * dpr,
      vy: rand(-0.3, 0.3) * speed * dpr,
      r: rand(1, 2.4) * dpr,
      t: Math.random() * Math.PI * 2,
      links: [],
    }));

    const maxDist = Math.min(W, H) * 0.09; // connection threshold in device px
    const maxDist2 = maxDist * maxDist;

    // Pulses traveling along edges (store segments that animate from 0->1)
    type Pulse = { a: number; b: number; p: number; v: number };
    const pulses: Pulse[] = [];

    let raf = 0;
    let last = performance.now();

    const attractStrength = 0.02 * dpr * speed; // mouse gravity

    function step(now: number) {
      const dt = Math.min(33, now - last) / 16.67; // normalize to ~60fps
      last = now;

      // Semi-transparent clear for light trails
      ctx.clearRect(0, 0, W, H);
      ctx.globalAlpha = opacity;

      // Background gradient glow (procedural each frame for shimmer)
      const g = ctx.createRadialGradient(W * 0.75, H * 0.2, Math.min(W, H) * 0.05, W * 0.5, H * 0.5, Math.max(W, H));
      g.addColorStop(0, hexToRgba(color, 0.15));
      g.addColorStop(0.5, hexToRgba("#6366f1", 0.08)); // indigo-500
      g.addColorStop(1, hexToRgba("#14b8a6", 0.04)); // teal-500
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);

      // Update nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.t += 0.003 * dt;
        // Subtle noise wobble
        n.vx += Math.cos(n.t + i) * 0.003 * dpr * speed;
        n.vy += Math.sin(n.t * 1.3 + i) * 0.003 * dpr * speed;

        if (interactive && mouse.current.active) {
          const dx = mouse.current.x * dpr - n.x;
          const dy = mouse.current.y * dpr - n.y;
          const dist2 = dx * dx + dy * dy;
          const mRad = (Math.min(W, H) * 0.03) ** 2;
          if (dist2 < mRad) {
            const f = attractStrength * (1 - dist2 / mRad);
            n.vx += dx * f * dt;
            n.vy += dy * f * dt;
          }
        }

        n.x += n.vx * dt;
        n.y += n.vy * dt;

        // Wrap edges
        if (n.x < -10) n.x = W + 10;
        if (n.x > W + 10) n.x = -10;
        if (n.y < -10) n.y = H + 10;
        if (n.y > H + 10) n.y = -10;
        n.links.length = 0;
      }

      // Build connections (naive O(n^2), but we clamp per-node for perf)
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        let connected = 0;
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < maxDist2) {
            // Connect these two
            a.links.push(j);
            b.links.push(i);
            connected++;
            if (connected >= maxConnections) break;
          }
        }
      }

      // Draw edges with distance-based alpha
      ctx.lineWidth = 1 * dpr;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (const j of a.links) {
          if (j <= i) continue; // draw once
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          const alpha = Math.max(0, 1 - d / maxDist) * 0.5; // fade with distance
          ctx.strokeStyle = hexToRgba(color, alpha);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();

          // Occasionally spawn a pulse along this edge
          if (Math.random() < 0.0015 * dt) {
            pulses.push({ a: i, b: j, p: 0, v: 0.02 + Math.random() * 0.04 });
          }
        }
      }

      // Draw pulses (small dot animating from a->b)
      for (let k = pulses.length - 1; k >= 0; k--) {
        const pulse = pulses[k];
        pulse.p += pulse.v * dt * speed;
        const a = nodes[pulse.a];
        const b = nodes[pulse.b];
        const x = a.x + (b.x - a.x) * pulse.p;
        const y = a.y + (b.y - a.y) * pulse.p;
        const life = 1 - pulse.p;
        if (!isFinite(x) || !isFinite(y)) { pulses.splice(k, 1); continue; }
        ctx.fillStyle = hexToRgba("#ffffff", Math.max(0, life));
        ctx.beginPath();
        ctx.arc(x, y, 1.5 * dpr, 0, Math.PI * 2);
        ctx.fill();
        if (pulse.p >= 1) pulses.splice(k, 1);
      }

      // Draw nodes last so they sit atop edges
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        ctx.fillStyle = hexToRgba(nodeColor, 0.8); // sky-100
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(step);
    }

    raf = requestAnimationFrame(step);

    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.current.x = e.clientX - rect.left;
      mouse.current.y = e.clientY - rect.top;
      mouse.current.active = true;
    };
    const onLeave = () => { mouse.current.active = false; };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseleave", onLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseleave", onLeave);
    };
  }, [density, speed, color, interactive, opacity, maxConnections, dpr]);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10">
      <style>
        {`
          @keyframes auroraShift {
            0%, 100% { transform: translate(-25%, -25%); }
            50% { transform: translate(25%, 25%); }
          }
          @keyframes auroraShiftReverse {
            0%, 100% { transform: translate(25%, 25%); }
            50% { transform: translate(-25%, -25%); }
          }
        `}
      </style>
      {/* Soft aurora overlay using tailwind gradients for extra depth */}
      <div className="absolute inset-0 overflow-hidden opacity-60 mix-blend-screen z-0 pointer-events-none">
        <div
          className="absolute -top-24 left-0 h-[60vh] w-[50vw] rounded-full blur-3xl bg-gradient-to-br from-cyan-700/30 via-indigo-600/25 to-teal-700/30"
          style={{ animation: "auroraShift 60s linear infinite" }}
        />
        <div
          className="absolute bottom-0 right-0 h-[55vh] w-[45vw] rounded-full blur-3xl bg-gradient-to-tr from-indigo-500/20 via-cyan-400/20 to-emerald-500/20"
          style={{ animation: "auroraShiftReverse 60s linear infinite" }}
        />
      </div>

      {/* Animated graph canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 z-10" />

      {/* Optional scanlines shimmer for a subtle tech feel */}
      <div className="absolute inset-0 opacity-[0.08] z-20" style={{
        backgroundImage: `repeating-linear-gradient(0deg, rgba(255,255,255,0.4), rgba(255,255,255,0.4) 1px, transparent 1px, transparent 3px)`,
        maskImage: "linear-gradient(to bottom, transparent, black 20%, black 80%, transparent)",
        WebkitMaskImage: "linear-gradient(to bottom, transparent, black 20%, black 80%, transparent)",
      }} />
    </div>
  );
}

// Utilities -----------------------------------------------------
function hexToRgba(hex: string, alpha = 1): string {
  // support #rgb, #rrggbb
  const h = hex.replace("#", "");
  const bigint = h.length === 3
    ? parseInt(h.split("").map((c) => c + c).join(""), 16)
    : parseInt(h, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
