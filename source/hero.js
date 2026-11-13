// Ringmast4r hero: the top hat from the brand photo (../32 Logo Library/Ringmast4r Logos/tophat-transparent.png)
// built as a real object. Black velvet crown that flares toward the top, an upturned brim, three red
// satin bands on the front, each edged with three-strand twisted gold rope and a gold skull at each
// end, and a gold fringe lying on the brim. It turns once per loop under a spotlight, lingering
// face-on, over a black circus-ring floor with red rings and dust in the beam. Proportions were
// measured from the photo: crown height 1.62 x the base radius, top radius 1.245 x, brim 1.5 x.
//
// The canvas is TRANSPARENT; render_hero.py adds the backdrop, the floor reflection and the type.
// window.renderFrame(phase, layer): 'hat' = the hat alone, 'fx' = rings and motes (the hat hides
// what is behind it). window.floorY() = the floor line on the canvas in px.

import * as THREE from 'three';

const q = new URLSearchParams(location.search);
const W = +(q.get('w') || 2400), H = +(q.get('h') || 1280);
const S = 0.84;                         // hat scale (crown base radius in world units)
const FLOOR = -0.62;                    // world height of the floor
const HAT_Y = FLOOR + 0.16;             // the hat floats a little above it
const canvas = document.getElementById('hero');

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true, premultipliedAlpha: false });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.setClearColor(0x000000, 0);
renderer.autoClear = false;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(24, W / H, 0.1, 100);
camera.position.set(0, 1.12, 7.7);
camera.lookAt(0, -0.1, 0);

// ---------- stage: dark room, a big spotlight box overhead, warm front fill, red strips ----------
function stageEnv() {
  const env = new THREE.Scene();
  env.add(new THREE.Mesh(new THREE.SphereGeometry(20, 32, 16),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(0.015, 0.012, 0.012), side: THREE.BackSide })));
  const card = (w, h, x, y, z, rgb, k) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(...rgb).multiplyScalar(k), side: THREE.DoubleSide }));
    m.position.set(x, y, z); m.lookAt(0, 0, 0); env.add(m);
  };
  card(7, 7, 0, 11, 1, [1, 0.96, 0.9], 3.4);            // the spotlight overhead
  card(9, 2.2, 0, 3.2, 12, [1, 0.93, 0.85], 2.2);       // warm box behind the camera: satin and gold faces
  card(3, 6, -8, 2, 7, [1, 0.95, 0.9], 2.0);            // soft fill, front left
  card(1.4, 12, 9, 1, 2, [0.9, 0.06, 0.06], 4.5);       // red strip, right
  card(1.4, 12, -9, 1, -2, [0.8, 0.05, 0.05], 3.0);     // red strip, left back
  card(3, 8, 3, 2, -10, [1, 1, 1], 1.4);                // cool back light for the far edges
  card(20, 6, 0, -9, 0, [0.12, 0.02, 0.02], 1);         // floor bounce, deep red
  const pm = new THREE.PMREMGenerator(renderer);
  const tex = pm.fromScene(env, 0.02).texture;
  pm.dispose();
  return tex;
}
scene.environment = stageEnv();
const key = new THREE.SpotLight(0xfff1dc, 60, 30, 0.5, 0.6, 1.2); key.position.set(0.5, 9, 3.5); key.target.position.set(0, 0.5, 0);
scene.add(key, key.target);
const rimR = new THREE.DirectionalLight(0xff2a2a, 2.2); rimR.position.set(5, 2, -4); scene.add(rimR);
const rimW = new THREE.DirectionalLight(0xe8eeff, 1.2); rimW.position.set(-5, 3, -3); scene.add(rimW);

// ---------- materials ----------
const debug = q.get('debug') === 'normals';
const M = (o) => debug ? new THREE.MeshNormalMaterial({ side: THREE.DoubleSide }) : new THREE.MeshPhysicalMaterial(o);
const feltTop = M({ color: 0x070709, roughness: 0.85, sheen: 0.5, sheenColor: 0x24222a, sheenRoughness: 0.6, envMapIntensity: 0.6, side: THREE.DoubleSide });
const felt = M({ color: 0x0b0b0e, roughness: 0.78, sheen: 1, sheenColor: 0x4a4650, sheenRoughness: 0.45, envMapIntensity: 0.9, side: THREE.DoubleSide });
const satin = M({ color: 0xb3101a, roughness: 0.3, sheen: 0.7, sheenColor: 0xff5a5a, sheenRoughness: 0.35, clearcoat: 0.25, clearcoatRoughness: 0.3,
  anisotropy: 0.75, anisotropyRotation: Math.PI / 2, envMapIntensity: 1.1 });
const gold = M({ color: 0xd9a64e, metalness: 1, roughness: 0.28, envMapIntensity: 1.25 });
const goldCord = M({ color: 0xc89a4c, metalness: 0.85, roughness: 0.45, envMapIntensity: 1.1 });
const socket = M({ color: 0x050403, roughness: 0.6 });

// ---------- the hat (crown base radius 1, brim at y = 0) ----------
const CH = 1.62, TOP = 1.245, BRIM = 1.5;
const rc = y => 1 + (TOP - 1) * Math.pow(Math.max(0, y) / CH, 1.35);

const spin = new THREE.Group(); scene.add(spin);
const hat = new THREE.Group(); hat.scale.setScalar(S); spin.add(hat);

function crown() {
  const pts = [];
  for (let i = 0; i <= 60; i++) { const y = -0.02 + (CH - 0.05 + 0.02) * i / 60; pts.push(new THREE.Vector2(rc(y), y)); }
  const f = 0.05, cx = rc(CH) - f, cy = CH - f;           // rounded top edge
  for (let i = 1; i <= 10; i++) { const a = i / 10 * Math.PI / 2; pts.push(new THREE.Vector2(cx + f * Math.cos(a), cy + f * Math.sin(a))); }
  const lid = [new THREE.Vector2(cx, CH)];                 // the top, in a duller felt so the spotlight does not grey it
  for (let i = 1; i <= 12; i++) { const r = cx * (1 - i / 12); lid.push(new THREE.Vector2(r, CH + 0.012 * Math.sin(i / 12 * Math.PI / 2))); }
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.LatheGeometry(pts, 256), felt), new THREE.Mesh(new THREE.LatheGeometry(lid, 256), feltTop));
  return g;
}
function brim() {
  const top = r => 0.16 * Math.pow((r - 0.96) / (BRIM - 0.96), 2.6);
  const pts = [];
  for (let i = 0; i <= 40; i++) { const r = 0.96 + (BRIM - 0.96) * i / 40; pts.push(new THREE.Vector2(r, top(r))); }
  const lip = 0.024, ly = top(BRIM) - lip;
  for (let i = 1; i < 12; i++) { const a = Math.PI / 2 - i / 12 * Math.PI; pts.push(new THREE.Vector2(BRIM + lip * Math.cos(a), ly + lip * Math.sin(a))); }
  for (let i = 0; i <= 40; i++) { const r = BRIM - (BRIM - 0.96) * i / 40; pts.push(new THREE.Vector2(r, top(r) - 2 * lip)); }
  pts.push(pts[0].clone());
  const m = new THREE.Mesh(new THREE.LatheGeometry(pts, 256), felt);
  m.userData.top = top;
  return m;
}

// a band: a satin cushion over [-PHI, PHI] of the crown between y0 and y1, ends rounded
const PHI = 60 * Math.PI / 180;
function bandShape(y0, y1) {
  const rr = rc((y0 + y1) / 2), Sx = PHI * rr, rcorner = Math.min(0.11, (y1 - y0) / 2);
  const clip = s => {                                          // vertical extent at arc position s
    const e = Math.abs(s) - (Sx - rcorner);
    if (e <= 0) return [y0, y1];
    const dy = rcorner - Math.sqrt(Math.max(0, rcorner * rcorner - e * e));
    return [y0 + dy, y1 - dy];
  };
  return { rr, Sx, rcorner, clip };
}
function band(y0, y1) {
  const { rr, Sx, clip } = bandShape(y0, y1);
  const NU = 220, NV = 28, P = [], UV = [], I = [];
  for (let i = 0; i <= NU; i++) {
    const s = -Sx + 2 * Sx * i / NU, phi = s / rr;
    const [a, b] = clip(s * 0.999);
    const end = Math.min(1, (Sx - Math.abs(s)) / 0.12);
    for (let j = 0; j <= NV; j++) {
      const v = j / NV, y = a + (b - a) * v;
      const r = rc(y) + 0.008 + 0.022 * Math.sin(Math.PI * v) * Math.sqrt(end);
      P.push(r * Math.sin(phi), y, r * Math.cos(phi)); UV.push(i / NU, v);
    }
  }
  for (let i = 0; i < NU; i++) for (let j = 0; j < NV; j++) {
    const a = i * (NV + 1) + j, b = a + NV + 1;
    I.push(a, b, a + 1, b, b + 1, a + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(UV, 2));
  g.setIndex(I); g.computeVertexNormals(); g.computeTangents?.();
  return new THREE.Mesh(g, satin);
}
// the rope round a band: three strands twisted round the band's outline, lying on the crown
function rope(y0, y1) {
  const { rr, Sx, rcorner, clip } = bandShape(y0, y1);
  const pad = 0.02, outline = [];
  const X = Sx + pad, Y0 = y0 - pad, Y1 = y1 + pad, R = rcorner + pad;
  const seg = (ax, ay, bx, by, n) => { for (let i = 0; i < n; i++) outline.push([ax + (bx - ax) * i / n, ay + (by - ay) * i / n]); };
  const arc = (cx, cy, a0, n) => { for (let i = 0; i < n; i++) { const a = a0 + i / n * Math.PI / 2; outline.push([cx + R * Math.cos(a), cy + R * Math.sin(a)]); } };
  seg(-X + R, Y0, X - R, Y0, 400); arc(X - R, Y0 + R, -Math.PI / 2, 40);
  seg(X, Y0 + R, X, Y1 - R, 40); arc(X - R, Y1 - R, 0, 40);
  seg(X - R, Y1, -X + R, Y1, 400); arc(-X + R, Y1 - R, Math.PI / 2, 40);
  seg(-X, Y1 - R, -X, Y0 + R, 40); arc(-X + R, Y0 + R, Math.PI, 40);
  const rho = 0.013, lift = 0.02;
  const pos = outline.map(([s, y]) => { const phi = s / rr, r = rc(y) + lift; return new THREE.Vector3(r * Math.sin(phi), y, r * Math.cos(phi)); });
  const n = pos.length, group = new THREE.Group();
  let len = 0; for (let i = 0; i < n; i++) len += pos[i].distanceTo(pos[(i + 1) % n]);
  const twists = Math.round(len / 0.055);
  for (let k = 0; k < 3; k++) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      const p = pos[i], t = pos[(i + 1) % n].clone().sub(pos[(i - 1 + n) % n]).normalize();
      const out = new THREE.Vector3(p.x, 0, p.z).normalize();
      const nrm = out.clone().sub(t.clone().multiplyScalar(out.dot(t))).normalize();
      const bin = new THREE.Vector3().crossVectors(t, nrm);
      const th = i / n * twists * Math.PI * 2 + k * Math.PI * 2 / 3;
      pts.push(p.clone().addScaledVector(nrm, rho * Math.cos(th)).addScaledVector(bin, rho * Math.sin(th)));
    }
    const curve = new THREE.CatmullRomCurve3(pts, true);
    group.add(new THREE.Mesh(new THREE.TubeGeometry(curve, n * 2, rho * 0.95, 8, true), gold));
  }
  return group;
}
function skull() {
  // a skull stud in relief, as on the hat: flat domed cranium, cheekbones, two dark round sockets,
  // a nose hole, a jaw with a row of teeth. It faces mostly forward so its face reads from the front.
  const g = new THREE.Group();
  const add = (geo, mat, x, y, z, sx = 1, sy = 1, sz = 1) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.scale.set(sx, sy, sz); g.add(m); return m; };
  const ball = new THREE.SphereGeometry(1, 32, 20), box = new THREE.BoxGeometry(1, 1, 1);
  add(ball, gold, 0, 0.012, 0, 0.05, 0.054, 0.028);            // cranium
  add(ball, gold, -0.024, -0.012, 0.01, 0.02, 0.018, 0.018);   // cheekbones
  add(ball, gold, 0.024, -0.012, 0.01, 0.02, 0.018, 0.018);
  add(box, gold, 0, -0.034, 0.006, 0.034, 0.02, 0.022);        // jaw
  add(ball, socket, -0.019, 0.002, 0.024, 0.017, 0.019, 0.01); // sockets
  add(ball, socket, 0.019, 0.002, 0.024, 0.017, 0.019, 0.01);
  add(ball, socket, 0, -0.018, 0.026, 0.007, 0.01, 0.006);     // nose
  add(box, socket, 0, -0.033, 0.0175, 0.03, 0.0028, 0.002);    // teeth line
  for (let i = -2; i <= 2; i++) add(box, socket, i * 0.0066, -0.033, 0.0175, 0.0016, 0.015, 0.002);
  return g;
}
function fringe(top) {
  const rng = mulberry32(5), P = [], N = [], I = [];
  const tubeInto = (pts, radius) => {
    const geo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, radius, 5, false);
    const base = P.length / 3, p = geo.attributes.position.array, nn = geo.attributes.normal.array;
    for (let i = 0; i < p.length; i++) { P.push(p[i]); N.push(nn[i]); }
    for (const x of geo.index.array) I.push(base + x);
  };
  for (let k = 0; k < 340; k++) {
    let phi = rng() * Math.PI * 2, r = 0.99 + rng() * 0.02;
    const L = 0.2 + rng() * 0.34, dphi = (rng() - 0.5) * 0.6, pts = [];
    for (let i = 0; i <= 6; i++) {
      const t = i / 6, rr = r + L * t, ph = phi + dphi * t * t + (rng() - 0.5) * 0.03;
      const y = top(Math.min(rr, BRIM)) + 0.012 + 0.03 * Math.sin(t * Math.PI) * rng() + (i === 0 ? 0.03 : 0);
      pts.push(new THREE.Vector3(rr * Math.sin(ph), y, rr * Math.cos(ph)));
    }
    tubeInto(pts, 0.0055 + rng() * 0.003);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
  g.setIndex(I);
  return new THREE.Mesh(g, goldCord);
}

function buildHat() {
  hat.add(crown());
  const b = brim(); hat.add(b);
  const bands = [[1.14, 1.4], [0.7, 0.96], [0.26, 0.52]];   // three bands, top to bottom, black between (as in the photo)
  for (const [y0, y1] of bands) {
    hat.add(band(y0, y1));
    hat.add(rope(y0, y1));
    const { rr, Sx } = bandShape(y0, y1), ym = (y0 + y1) / 2;
    for (const side of [-1, 1]) {
      const phi = side * (Sx - 0.15) / rr, r = rc(ym) + 0.055;
      const s = skull(); s.position.set(r * Math.sin(phi), ym, r * Math.cos(phi)); s.rotation.y = phi * 0.35; s.scale.setScalar(2.0);
      hat.add(s);
    }
  }
  hat.add(fringe(b.userData.top));
}

// ---------- fx: the ring on the floor, signal rings, dust in the beam ----------
const fx = new THREE.Group(); scene.add(fx);
const ringMat = (c, o) => { const m = new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, depthWrite: false, side: THREE.DoubleSide }); m.toneMapped = false; return m; };
const curb = new THREE.Mesh(new THREE.RingGeometry(2.55, 2.6, 256), ringMat(0xcc0000, 0.85)); curb.rotation.x = -Math.PI / 2; curb.position.y = FLOOR + 0.002; fx.add(curb);
const curb2 = new THREE.Mesh(new THREE.RingGeometry(2.7, 2.715, 256), ringMat(0xffffff, 0.25)); curb2.rotation.x = -Math.PI / 2; curb2.position.y = FLOOR + 0.002; fx.add(curb2);
const rings = [];
for (let i = 0; i < 3; i++) {
  const m = new THREE.Mesh(new THREE.RingGeometry(0.985, 1.0, 256), ringMat(0xcc0000, 0));
  m.rotation.x = -Math.PI / 2; m.position.y = FLOOR + 0.003; fx.add(m); rings.push({ m, off: i / 3 });
}
function moteSprite() {
  const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, 'rgba(255,244,225,1)'); r.addColorStop(0.3, 'rgba(255,220,180,0.5)'); r.addColorStop(1, 'rgba(255,200,160,0)');
  g.fillStyle = r; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const NM = 260, rng = mulberry32(17), base = new Float32Array(NM * 4);
for (let i = 0; i < NM; i++) { base[i * 4] = 0.3 + rng() * 2.4; base[i * 4 + 1] = rng() * Math.PI * 2; base[i * 4 + 2] = FLOOR + rng() * 3.4; base[i * 4 + 3] = rng() < 0.5 ? 1 : -1; }
const moteGeo = new THREE.BufferGeometry();
moteGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(NM * 3), 3));
moteGeo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(NM * 4).fill(1), 4));
const motes = new THREE.Points(moteGeo, new THREE.PointsMaterial({ size: 0.03, map: moteSprite(), transparent: true, depthWrite: false, opacity: 0.85, toneMapped: false, vertexColors: true }));
fx.add(motes);

function smooth(e0, e1, x) { const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t); }
function mulberry32(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

function setPhase(p) {
  const TAU = Math.PI * 2;
  const turn = TAU * p - 0.62 * Math.sin(TAU * p);           // one turn per loop, slow while face-on
  const bob = Math.sin(p * TAU * 2) * 0.02;
  spin.position.set(0, HAT_Y + bob, 0);
  spin.rotation.set(0, turn, 0);
  for (const r of rings) {
    const t = (p + r.off) % 1;
    r.m.scale.setScalar(1.55 + t * 1.6);
    r.m.material.opacity = Math.pow(1 - t, 1.5) * 0.7 * Math.min(1, t * 8);
  }
  const pos = moteGeo.attributes.position.array, col = moteGeo.attributes.color.array;
  for (let i = 0; i < NM; i++) {
    const rad = base[i * 4], a = base[i * 4 + 1] + base[i * 4 + 3] * p * TAU;
    pos[i * 3] = Math.cos(a) * rad;
    pos[i * 3 + 1] = base[i * 4 + 2] + Math.sin(a * 2 + i) * 0.05;
    pos[i * 3 + 2] = Math.sin(a) * rad * 0.6 - 0.2;
    // brightest inside the spotlight's beam, fading out at its edge
    const beam = 1 - smooth(1.1, 2.2, Math.hypot(pos[i * 3], pos[i * 3 + 2] + 0.2));
    col[i * 4 + 3] = 0.25 + 0.75 * beam;
  }
  moteGeo.attributes.position.needsUpdate = true; moteGeo.attributes.color.needsUpdate = true;
}

const depthOnly = new THREE.MeshBasicMaterial({ colorWrite: false });
window.renderFrame = (p, layer = 'hat') => {
  setPhase(p);
  renderer.clear();
  if (layer === 'hat') {
    fx.visible = false; spin.visible = true; renderer.render(scene, camera);
  } else {
    fx.visible = false; spin.visible = true; scene.overrideMaterial = depthOnly; renderer.render(scene, camera);
    scene.overrideMaterial = null; fx.visible = true; spin.visible = false; renderer.render(scene, camera);
    spin.visible = true;
  }
  return canvas.toDataURL('image/png');
};
window.floorY = () => { const v = new THREE.Vector3(0, FLOOR, 0).project(camera); return (1 - v.y) / 2 * H; };
window.glInfo = () => { const gl = renderer.getContext(); const e = gl.getExtension('WEBGL_debug_renderer_info'); return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); };

try { buildHat(); setPhase(0); renderer.clear(); renderer.render(scene, camera); document.body.dataset.ready = '1'; }
catch (e) { document.body.dataset.error = String(e && e.stack || e); }
