import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// Keyframes for a right-handed cover drive, side-on. x = towards the bowler, y = up, z = depth. Illustrative model, not a real player.
const J = ["head", "neck", "ls", "rs", "le", "re", "lw", "rw", "lh", "rh", "lk", "rk", "la", "ra", "tip"];
const K = [
  { t: 0, name: "Stance", p: [[0.05, 1.62, 0], [0.02, 1.45, 0], [0.12, 1.4, 0.06], [-0.1, 1.4, -0.06], [0.06, 1.16, 0.16], [-0.12, 1.13, 0.04], [-0.02, 0.96, 0.13], [-0.04, 0.99, 0.1], [0.08, 0.95, 0.07], [-0.08, 0.95, -0.07], [0.17, 0.52, 0.1], [-0.15, 0.52, -0.1], [0.2, 0.06, 0.15], [-0.22, 0.06, -0.15], [0.02, 0.12, 0.2]] },
  { t: 0.28, name: "Backlift", p: [[0.04, 1.62, 0], [0.01, 1.45, 0], [0.11, 1.4, 0.06], [-0.11, 1.41, -0.06], [-0.06, 1.3, 0.16], [-0.27, 1.25, -0.04], [-0.28, 1.5, 0.06], [-0.3, 1.52, 0.03], [0.07, 0.95, 0.07], [-0.09, 0.95, -0.07], [0.17, 0.53, 0.1], [-0.15, 0.52, -0.1], [0.2, 0.06, 0.15], [-0.22, 0.06, -0.15], [-0.62, 1.92, 0]] },
  { t: 0.52, name: "Stride & downswing", p: [[0.3, 1.52, 0], [0.24, 1.37, 0], [0.34, 1.33, 0.06], [0.12, 1.32, -0.06], [0.24, 1.2, 0.18], [0.02, 1.14, 0], [0.02, 1.26, 0.1], [0, 1.28, 0.07], [0.2, 0.88, 0.07], [0.04, 0.88, -0.07], [0.5, 0.5, 0.12], [-0.05, 0.45, -0.1], [0.62, 0.06, 0.15], [-0.22, 0.06, -0.15], [-0.32, 1.62, 0.05]] },
  { t: 0.68, name: "Impact", p: [[0.55, 1.4, 0.02], [0.47, 1.27, 0], [0.52, 1.24, 0.08], [0.32, 1.24, -0.06], [0.6, 1.02, 0.18], [0.42, 1.0, 0.04], [0.56, 0.8, 0.2], [0.53, 0.83, 0.17], [0.34, 0.82, 0.07], [0.18, 0.82, -0.07], [0.64, 0.46, 0.12], [-0.02, 0.38, -0.1], [0.72, 0.06, 0.15], [-0.22, 0.07, -0.15], [0.86, 0.14, 0.32]] },
  { t: 0.9, name: "Follow-through", p: [[0.5, 1.44, 0.02], [0.43, 1.3, 0], [0.5, 1.28, 0.1], [0.3, 1.26, -0.08], [0.52, 1.48, 0.2], [0.36, 1.42, 0.06], [0.32, 1.68, 0.12], [0.3, 1.66, 0.09], [0.33, 0.85, 0.07], [0.17, 0.85, -0.07], [0.63, 0.47, 0.12], [0.0, 0.42, -0.1], [0.72, 0.06, 0.15], [-0.14, 0.16, -0.15], [-0.12, 2.02, 0.05]] },
];
K.push({ ...K[0], t: 1.0001 });
const BONES = [["head", "neck"], ["neck", "ls"], ["neck", "rs"], ["ls", "rs"], ["ls", "le"], ["le", "lw"], ["rs", "re"], ["re", "rw"], ["ls", "lh"], ["rs", "rh"], ["lh", "rh"], ["lh", "lk"], ["lk", "la"], ["rh", "rk"], ["rk", "ra"]];
const LOOP = 3.6;
const ease = (x) => x * x * (3 - 2 * x);
const v = (a) => new THREE.Vector3(...a);

const pose = (u) => {
  const i = K.findIndex((k, n) => n < K.length - 1 && u >= k.t && u < K[n + 1].t);
  const a = K[i], b = K[i + 1], f = ease((u - a.t) / (b.t - a.t));
  return { name: f > 0.5 && b.t <= 1 ? b.name : a.name, p: Object.fromEntries(J.map((j, n) => [j, v(a.p[n]).lerp(v(b.p[n]), f)])) };
};
const angle = (a, b, c) => THREE.MathUtils.radToDeg(a.clone().sub(b).angleTo(c.clone().sub(b)));

export default function Batter3D({ hud }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    const w = () => el.clientWidth, h = () => el.clientHeight;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setSize(w(), h());
    renderer.shadowMap.enabled = true;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, w() / h(), 0.1, 50);
    camera.position.set(1.1, 1.35, 5.3);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0.25, 0.72, 0);
    controls.enableZoom = false;
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.6;
    controls.minPolarAngle = 0.9;
    controls.maxPolarAngle = 1.6;

    scene.add(new THREE.HemisphereLight(0xbfe9ff, 0x0b132b, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(2, 4, 3);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    scene.add(key);
    const rim = new THREE.PointLight(0x00b4d8, 12, 8);
    rim.position.set(-1.5, 2, -1.5);
    scene.add(rim);

    const floor = new THREE.Mesh(new THREE.CircleGeometry(2.2, 64), new THREE.MeshStandardMaterial({ color: 0x0f2a3d, roughness: 0.95 }));
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);
    const ring = new THREE.Mesh(new THREE.RingGeometry(2.15, 2.2, 64), new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.6 }));
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.002;
    scene.add(ring);
    const crease = new THREE.Mesh(new THREE.PlaneGeometry(0.04, 2.6), new THREE.MeshBasicMaterial({ color: 0xe2e8f0 }));
    crease.rotation.x = -Math.PI / 2;
    crease.position.set(0.45, 0.003, 0);
    scene.add(crease);
    const stumpMat = new THREE.MeshStandardMaterial({ color: 0xf3ead7, roughness: 0.5 });
    [-0.11, 0, 0.11].forEach((z) => { const s = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.71, 10), stumpMat); s.position.set(-0.55, 0.355, z); s.castShadow = true; scene.add(s); });

    const jointMat = new THREE.MeshStandardMaterial({ color: 0x5fd7ef, emissive: 0x00b4d8, emissiveIntensity: 0.9, roughness: 0.3 });
    const boneMat = new THREE.MeshStandardMaterial({ color: 0x10b981, emissive: 0x065f46, emissiveIntensity: 0.6, roughness: 0.35, metalness: 0.2 });
    const joints = Object.fromEntries(J.filter((j) => j !== "tip").map((j) => {
      const m = new THREE.Mesh(new THREE.SphereGeometry(j === "head" ? 0.11 : 0.032, 20, 16), j === "head" ? new THREE.MeshStandardMaterial({ color: 0x1c2541, emissive: 0x00b4d8, emissiveIntensity: 0.25, roughness: 0.4 }) : jointMat);
      m.castShadow = true; scene.add(m); return [j, m];
    }));
    const unitCyl = new THREE.CylinderGeometry(0.022, 0.022, 1, 10);
    const bones = BONES.map(() => { const m = new THREE.Mesh(unitCyl, boneMat); m.castShadow = true; scene.add(m); return m; });
    const bat = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1, 0.035), new THREE.MeshStandardMaterial({ color: 0xd9b382, roughness: 0.6 }));
    bat.castShadow = true;
    scene.add(bat);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.036, 20, 16), new THREE.MeshStandardMaterial({ color: 0xc1121f, roughness: 0.35, emissive: 0x400005 }));
    ball.castShadow = true;
    scene.add(ball);
    const arcMat = new THREE.LineDashedMaterial({ color: 0xf59e0b, dashSize: 0.06, gapSize: 0.04 });
    const arc = new THREE.Line(new THREE.BufferGeometry(), arcMat);
    scene.add(arc);

    const up = new THREE.Vector3(0, 1, 0);
    const place = (m, a, b, thick = 1) => {
      const d = b.clone().sub(a);
      m.position.copy(a).add(b).multiplyScalar(0.5);
      m.scale.set(thick, d.length(), thick);
      m.quaternion.setFromUnitVectors(up, d.normalize());
    };

    let raf = 0, t0 = performance.now(), last = "", frameN = 0, visible = true;
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) loop(); }, { threshold: 0.05 });
    io.observe(el);
    const loop = () => {
      if (!visible) return;
      const u = (((performance.now() - t0) / 1000) % LOOP) / LOOP;
      const { name, p } = pose(u);
      Object.entries(joints).forEach(([j, m]) => m.position.copy(p[j]));
      BONES.forEach(([a, b], i) => place(bones[i], p[a], p[b]));
      const grip = p.lw.clone().add(p.rw).multiplyScalar(0.5);
      place(bat, grip, p.tip);
      const hit = 0.68;
      if (u < hit) {
        const f = u / hit, start = new THREE.Vector3(3.2, 1.3, 0.25), bounce = new THREE.Vector3(1.4, 0.04, 0.3), end = new THREE.Vector3(0.84, 0.18, 0.32);
        ball.position.copy(f < 0.75 ? start.clone().lerp(bounce, f / 0.75) : bounce.clone().lerp(end, (f - 0.75) / 0.25));
      } else {
        const f = (u - hit) / (1 - hit);
        ball.position.set(0.84 + f * 2.6, 0.18 + Math.sin(f * Math.PI) * 0.35, 0.32 + f * 1.8);
      }
      if (frameN++ % 6 === 0) {
        arc.geometry.setFromPoints([new THREE.Vector3(3.2, 1.3, 0.25), new THREE.Vector3(1.4, 0.04, 0.3), new THREE.Vector3(0.84, 0.18, 0.32), new THREE.Vector3(3.4, 0.4, 2.1)]);
        arc.computeLineDistances();
        const knee = Math.round(angle(p.lh, p.lk, p.la));
        const hm = p.lh.clone().add(p.rh).multiplyScalar(0.5);
        const wt = Math.max(0, Math.min(100, Math.round((100 * (hm.x - p.ra.x)) / (p.la.x - p.ra.x))));
        const head = Math.abs(p.head.x - p.la.x).toFixed(2);
        if (hud?.current) {
          if (name !== last) { hud.current.phase.textContent = name; last = name; }
          hud.current.knee.textContent = `${knee}°`;
          hud.current.wt.textContent = `${wt}%`;
          hud.current.wtBar.style.width = `${wt}%`;
          hud.current.head.textContent = `${head} m`;
        }
      }
      controls.update();
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    loop();
    const onResize = () => { camera.aspect = w() / h(); camera.updateProjectionMatrix(); renderer.setSize(w(), h()); };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf); io.disconnect(); window.removeEventListener("resize", onResize); controls.dispose();
      scene.traverse((o) => { o.geometry?.dispose(); if (o.material) o.material.dispose(); });
      renderer.dispose(); el.removeChild(renderer.domElement);
    };
  }, [hud]);
  return <div ref={ref} className="absolute inset-0 cursor-grab active:cursor-grabbing" data-testid="batter-3d-canvas" />;
}
