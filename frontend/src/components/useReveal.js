import { useEffect } from "react";
import { useLocation } from "react-router-dom";

// Adds .in to .reveal-3d elements as they scroll into view.
export const useReveal = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" });
    const scan = () => document.querySelectorAll(".reveal-3d:not(.in), .plan-pop:not(.in)").forEach((el) => io.observe(el));
    scan();
    const mo = new MutationObserver(scan);
    mo.observe(document.body, { childList: true, subtree: true });
    return () => { io.disconnect(); mo.disconnect(); };
  }, [pathname]);
};

// Sets --p (0 → 1) on every [data-s3d] element as it travels through the viewport; CSS turns it into 3D motion.
export const useScroll3D = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      raf = 0;
      const vh = window.innerHeight;
      document.documentElement.style.setProperty("--sp", (window.scrollY / Math.max(1, document.documentElement.scrollHeight - vh)).toFixed(4));
      document.querySelectorAll("[data-s3d]").forEach((el) => {
        const r = el.getBoundingClientRect();
        const pinned = el.dataset.s3d === "pin";
        const p = pinned ? -r.top / Math.max(1, r.height - vh) : (vh - r.top) / (vh + r.height);
        el.style.setProperty("--p", Math.max(0, Math.min(1, p)).toFixed(4));
      });
    };
    const on = () => { if (!raf) raf = requestAnimationFrame(tick); };
    tick();
    window.addEventListener("scroll", on, { passive: true });
    window.addEventListener("resize", on);
    return () => { window.removeEventListener("scroll", on); window.removeEventListener("resize", on); cancelAnimationFrame(raf); };
  }, [pathname]);
};
