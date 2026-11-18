import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Move3d } from "lucide-react";

const Batter3D = lazy(() => import("@/components/Batter3D"));
const Ball3DLazy = lazy(() => import("@/components/Ball3D"));
const Player3DLazy = lazy(() => import("@/components/Player3D"));

export const Ball3D = (p) => { const [ok] = useState(webgl); return ok ? <Suspense fallback={null}><Ball3DLazy {...p} /></Suspense> : null; };
export const Player3D = (p) => { const [ok] = useState(webgl); return ok ? <Suspense fallback={null}><Player3DLazy {...p} /></Suspense> : <div className="absolute inset-0 grid place-items-center text-slate-500 text-sm">3D needs WebGL</div>; };
function webgl() { return _webgl(); }
const _webgl = () => { try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch { return false; } };

// Interactive 3D batter (loaded after first paint so the page text appears instantly).
export const HeroBatter = () => {
  const [on, setOn] = useState(false);
  const hud = useRef({});
  useEffect(() => {
    if (!webgl()) return;
    const go = () => setOn(true);
    const id = "requestIdleCallback" in window ? window.requestIdleCallback(go, { timeout: 900 }) : setTimeout(go, 300);
    return () => ("cancelIdleCallback" in window ? window.cancelIdleCallback(id) : clearTimeout(id));
  }, []);
  const set = (k) => (el) => { hud.current[k] = el; };
  return (
    <div className="relative rounded-3xl border border-white/10 overflow-hidden bg-[radial-gradient(ellipse_at_50%_35%,rgba(0,180,216,0.22),rgba(11,19,43,0.9)_60%)]" data-testid="hero-batter-3d">
      <div className="relative z-10 sm:absolute sm:top-4 sm:left-4 m-3 sm:m-0 glass rounded-xl px-4 py-2.5 sm:py-3 pointer-events-none flex sm:block items-center justify-between gap-3" data-testid="hero-hud">
        <div><div className="eyebrow !text-[10px]">Live sample analysis</div>
        <div className="font-display font-bold text-base sm:text-lg mt-0.5" ref={set("phase")} data-testid="hero-hud-phase">Stance</div></div>
        <div className="text-[10px] text-slate-500">Illustrative 3D model</div>
      </div>
      <div className="relative h-[300px] sm:h-[520px]">
        {on ? <Suspense fallback={null}><Batter3D hud={hud} /></Suspense> : <div className="absolute inset-0 grid place-items-center text-slate-500 text-sm">Loading 3D player…</div>}
        <div className="absolute top-2 right-3 sm:top-4 sm:right-4 text-[11px] text-slate-400 flex items-center gap-1 pointer-events-none"><Move3d size={14} />Drag to rotate</div>
      </div>
      <div className="relative z-10 sm:absolute sm:bottom-4 sm:left-4 sm:right-4 m-3 sm:m-0 glass rounded-xl p-3 sm:p-4 grid grid-cols-3 gap-3 pointer-events-none text-xs" data-testid="hero-metrics">
        <div><div className="text-slate-400">Front knee</div><div className="font-mono text-base font-semibold text-[#5fd7ef]" ref={set("knee")}>—</div></div>
        <div><div className="text-slate-400">Weight on front foot</div><div className="font-mono text-base font-semibold text-[#10B981]" ref={set("wt")}>—</div>
          <div className="h-1 bg-white/10 rounded mt-1"><div className="h-full bg-[#10B981] rounded transition-[width] duration-200" ref={set("wtBar")} style={{ width: 0 }} /></div></div>
        <div><div className="text-slate-400">Head vs front foot</div><div className="font-mono text-base font-semibold text-amber-300" ref={set("head")}>—</div></div>
      </div>
      <div className="orbit-chip right-6 top-24 glass rounded-full px-3 py-1.5 text-[11px] font-mono text-[#5fd7ef] hidden sm:block">17 joints tracked</div>
      <div className="orbit-chip right-10 top-[52%] glass rounded-full px-3 py-1.5 text-[11px] font-mono text-amber-300 hidden sm:block" style={{ animationDelay: "-3s" }}>ball tracked ●</div>

    </div>
  );
};

// Pointer-driven 3D tilt for cards.
export const Tilt = ({ children, className = "", max = 9, ...p }) => {
  const r = useRef(null);
  const move = (e) => {
    const el = r.current;
    if (!el || window.matchMedia("(pointer: coarse)").matches) return;
    const b = el.getBoundingClientRect();
    const x = (e.clientX - b.left) / b.width - 0.5, y = (e.clientY - b.top) / b.height - 0.5;
    el.style.transform = `perspective(900px) rotateX(${-y * max}deg) rotateY(${x * max}deg) translateZ(6px)`;
    el.style.setProperty("--gx", `${(x + 0.5) * 100}%`);
    el.style.setProperty("--gy", `${(y + 0.5) * 100}%`);
  };
  const leave = () => { if (r.current) r.current.style.transform = ""; };
  return <div ref={r} onPointerMove={move} onPointerLeave={leave} className={`tilt-3d ${className}`} {...p}>{children}</div>;
};

export const CountUp = ({ to, ms = 1400 }) => {
  const [v, setV] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      const t0 = performance.now();
      const step = (t) => { const f = Math.min(1, (t - t0) / ms); setV(Math.round(to * (1 - (1 - f) ** 3))); if (f < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    });
    io.observe(ref.current);
    return () => io.disconnect();
  }, [to, ms]);
  return <span ref={ref}>{v}</span>;
};
