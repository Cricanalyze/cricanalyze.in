import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// Illustrative poses. Joints: head neck ls rs le re lw rw lh rh lk rk la ra
const J = ["head", "neck", "ls", "rs", "le", "re", "lw", "rw", "lh", "rh", "lk", "rk", "la", "ra"];
const POSES = {
  batting: [[0.55, 1.4, 0.02], [0.47, 1.27, 0], [0.52, 1.24, 0.08], [0.32, 1.24, -0.06], [0.6, 1.02, 0.18], [0.42, 1.0, 0.04], [0.56, 0.8, 0.2], [0.53, 0.83, 0.17], [0.34, 0.82, 0.07], [0.18, 0.82, -0.07], [0.64, 0.46, 0.12], [-0.02, 0.38, -0.1], [0.72, 0.06, 0.15], [-0.22, 0.07, -0.15]],
  bowling: [[0.25, 1.62, 0], [0.2, 1.46, 0], [0.28, 1.42, 0.12], [0.1, 1.44, -0.12], [0.42, 1.18, 0.2], [0.14, 1.78, -0.1], [0.3, 0.98, 0.22], [0.26, 2.06, -0.06], [0.12, 0.95, 0.08], [-0.02, 0.95, -0.08], [0.4, 0.52, 0.1], [-0.2, 0.58, -0.1], [0.55, 0.06, 0.12], [-0.46, 0.24, -0.1]],
};
const BONES = [["head", "neck"], ["neck", "ls"], ["neck", "rs"], ["ls", "rs"], ["ls", "le"], ["le", "lw"], ["rs", "re"], ["re", "rw"], ["ls", "lh"], ["rs", "rh"], ["lh", "rh"], ["lh", "lk"], ["lk", "la"], ["rh", "rk"], ["rk", "ra"]];
const mid = (p, a, b) => p[a].clone().add(p[b]).multiplyScalar(0.5);
const v3 = (a) => new THREE.Vector3(...a);
export const anchor = (p, key) => (key.includes("+") ? mid(p, ...key.split("+")) : p[key]);

const glowTex = () => {
  const c = document.createElement("canvas"); c.width = c.height = 64;
  const g = c.getContext("2d"), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.25, "rgba(95,215,239,0.9)"); r.addColorStop(1, "rgba(0,180,216,0)");
  g.fillStyle = r; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
};

export default function Player3D({ kind, points, active, dots, tags }) {
  const ref = useRef(null);
  const st = useRef({ kind, active });
  st.current = { kind, active };
  useEffect(() => {
    const el = ref.current;
    const w = () => el.clientWidth, h = () => el.clientHeight;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setSize(w(), h());
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(32, w() / h(), 0.1, 50);
    camera.position.set(0.8, 1.2, 4.7);
    const controls = new OrbitControls(camera, renderer.domElement);
    Object.assign(controls, { enableZoom: false, enablePan: false, enableDamping: true, autoRotate: true, autoRotateSpeed: 1.1, minPolarAngle: 0.9, maxPolarAngle: 1.6 });
    controls.target.set(0.12, 1.05, 0);
    scene.add(new THREE.HemisphereLight(0xbfe9ff, 0x0b132b, 1.2));
    const key = new THREE.DirectionalLight(0xffffff, 2); key.position.set(2, 4, 3); scene.add(key);
    const floor = new THREE.Mesh(new THREE.RingGeometry(0.9, 1.6, 64), new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.12, side: THREE.DoubleSide }));
    floor.rotation.x = -Math.PI / 2; scene.add(floor);
    const body = new THREE.MeshStandardMaterial({ color: 0x1c2541, emissive: 0x00b4d8, emissiveIntensity: 0.18, roughness: 0.35, metalness: 0.3 });
    const bone = new THREE.MeshStandardMaterial({ color: 0x10b981, emissive: 0x10b981, emissiveIntensity: 0.35, roughness: 0.4 });
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 24, 18), body); scene.add(head);
    const limb = new THREE.CapsuleGeometry(0.055, 1, 6, 12);
    const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 1, 8, 16), body); scene.add(torso);
    const bat = new THREE.Mesh(new THREE.BoxGeometry(0.11, 1, 0.04), new THREE.MeshStandardMaterial({ color: 0xd9b382, roughness: 0.6 })); scene.add(bat);
    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.05, 20, 16), new THREE.MeshStandardMaterial({ color: 0xc1121f, emissive: 0x400005, roughness: 0.35 })); scene.add(ball);
    const nodes = J.slice(1).map((j) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.062, 16, 12), bone); scene.add(m); return [j, m]; });
    const bones = BONES.map(() => { const m = new THREE.Mesh(limb, bone); scene.add(m); return m; });
    const tex = glowTex();
    const halos = points.batting.concat(points.bowling).map(() => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); scene.add(s); return s; });
    const up = new THREE.Vector3(0, 1, 0);
    const place = (m, a, b) => { const d = b.clone().sub(a); m.position.copy(a).add(b).multiplyScalar(0.5); m.scale.set(1, Math.max(0.01, d.length() - 0.11), 1); m.quaternion.setFromUnitVectors(up, d.normalize()); };
    const cur = Object.fromEntries(J.map((j, i) => [j, v3(POSES[kind][i])]));
    const tmp = new THREE.Vector3();
    let raf = 0, visible = true;
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) { cancelAnimationFrame(raf); loop(); } }, { threshold: 0.05 });
    io.observe(el);
    const loop = () => {
      if (!visible) return;
      const { kind: k, active: a } = st.current, t = performance.now() / 1000;
      J.forEach((j, i) => cur[j].lerp(tmp.set(...POSES[k][i]), 0.08));
      head.position.copy(cur.head);
      nodes.forEach(([j, m]) => m.position.copy(cur[j]));
      BONES.slice(1).forEach(([x, y], i) => place(bones[i + 1], cur[x], cur[y]));
      bones[0].visible = false;
      const nk = cur.neck.clone().lerp(cur.head, -0.1), hp = mid(cur, "lh", "rh");
      place(torso, nk, hp); torso.scale.set(1, Math.max(0.01, nk.distanceTo(hp) - 0.26), 0.75);
      const hands = mid(cur, "lw", "rw");
      bat.visible = k === "batting"; ball.visible = k === "bowling";
      if (bat.visible) { place(bat, hands, tmp.set(0.86, 0.14, 0.32)); bat.scale.set(1, hands.distanceTo(tmp), 1); }
      ball.position.copy(cur.rw).add(tmp.set(0.02, 0.06, 0));
      halos.forEach((s) => (s.visible = false));
      points[k].forEach((pt, i) => {
        const p = anchor(cur, pt.at), s = halos[i], on = i === a;
        s.visible = true; s.position.copy(p);
        const sc = (on ? 0.34 : 0.2) * (1 + 0.18 * Math.sin(t * 4 + i));
        s.scale.set(sc, sc, sc);
        const d = dots.current[i];
        if (d) { tmp.copy(p).project(camera); d.style.transform = `translate(${(tmp.x * 0.5 + 0.5) * w()}px, ${(-tmp.y * 0.5 + 0.5) * h()}px) translate(-50%, -50%)`; }
      });
      [cur.la, cur.ra, tmp.set(1.5, 0.05, 0).clone()].forEach((p, i) => {
        const d = tags.current[i];
        if (d) { tmp.copy(p).add(i < 2 ? up.clone().multiplyScalar(-0.12) : up.clone().multiplyScalar(0)).project(camera); d.style.transform = `translate(${(tmp.x * 0.5 + 0.5) * w()}px, ${(-tmp.y * 0.5 + 0.5) * h()}px) translate(-50%, 0)`; }
      });
      controls.update();
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    loop();
    const onResize = () => { camera.aspect = w() / h(); camera.updateProjectionMatrix(); renderer.setSize(w(), h()); };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf); io.disconnect(); window.removeEventListener("resize", onResize); controls.dispose();
      scene.traverse((o) => { o.geometry?.dispose(); o.material?.dispose(); }); tex.dispose();
      renderer.dispose(); el.removeChild(renderer.domElement);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return <div ref={ref} className="absolute inset-0 cursor-grab active:cursor-grabbing" data-testid="player-3d-canvas" />;
}
