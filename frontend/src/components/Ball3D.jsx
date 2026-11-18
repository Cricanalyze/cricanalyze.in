import { useEffect, useRef } from "react";
import * as THREE from "three";

// Spinning 3D cricket ball; spins faster while the page scrolls.
export default function Ball3D({ className = "" }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setSize(el.clientWidth, el.clientHeight);
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(30, el.clientWidth / el.clientHeight, 0.1, 20);
    camera.position.set(0, 0, 4.2);
    scene.add(new THREE.HemisphereLight(0xffe6e6, 0x0b132b, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 2.4);
    key.position.set(2, 2, 3);
    scene.add(key);
    const rim = new THREE.PointLight(0x00b4d8, 14, 10);
    rim.position.set(-2.5, 1, -1);
    scene.add(rim);
    const ball = new THREE.Group();
    ball.add(new THREE.Mesh(new THREE.SphereGeometry(1, 64, 48), new THREE.MeshStandardMaterial({ color: 0xa50f1a, roughness: 0.32, metalness: 0.1 })));
    const seamMat = new THREE.MeshStandardMaterial({ color: 0xf6ecd4, roughness: 0.6 });
    [-0.07, 0.07].forEach((z) => { const r = new THREE.Mesh(new THREE.TorusGeometry(1.002, 0.012, 8, 120), seamMat); r.position.z = z; r.scale.setScalar(Math.sqrt(1 - z * z)); ball.add(r); });
    const st = new THREE.BoxGeometry(0.012, 0.06, 0.012);
    for (let i = 0; i < 80; i++) {
      const a = (i / 80) * Math.PI * 2;
      [-0.035, 0.035].forEach((z) => { const m = new THREE.Mesh(st, seamMat); m.position.set(Math.cos(a) * 1.005, Math.sin(a) * 1.005, z); m.rotation.z = a; m.rotation.y = z > 0 ? 0.5 : -0.5; ball.add(m); });
    }
    ball.rotation.set(0.5, 0.3, 0.4);
    scene.add(ball);
    let raf = 0, boost = 0, lastY = window.scrollY, visible = true;
    const onScroll = () => { boost = Math.min(0.35, boost + Math.abs(window.scrollY - lastY) * 0.002); lastY = window.scrollY; };
    window.addEventListener("scroll", onScroll, { passive: true });
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) loop(); });
    io.observe(el);
    const loop = () => {
      if (!visible) return;
      ball.rotation.x += 0.012 + boost;
      ball.rotation.y += 0.004;
      boost *= 0.94;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    loop();
    return () => { cancelAnimationFrame(raf); io.disconnect(); window.removeEventListener("scroll", onScroll); scene.traverse((o) => { o.geometry?.dispose(); o.material?.dispose(); }); renderer.dispose(); el.removeChild(renderer.domElement); };
  }, []);
  return <div ref={ref} className={className} aria-hidden="true" data-testid="ball-3d" />;
}

