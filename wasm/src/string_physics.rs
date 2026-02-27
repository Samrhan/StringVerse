use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};

const MIN_LOOP_POINTS: usize = 20;
const INTERSECTION_THRESHOLD: f64 = 0.8;
const TARGET_POINT_DENSITY: f64 = 0.5;
const MAX_LOOPS: usize = 8;

#[derive(Clone, Serialize, Deserialize)]
pub struct StringLoop {
    pub positions: Vec<[f64; 3]>,
    pub velocities: Vec<[f64; 3]>,
    pub color_id: u32,
}

impl StringLoop {
    fn new(n: usize, color_id: u32) -> Self {
        let mut positions = Vec::with_capacity(n);
        let mut velocities = Vec::with_capacity(n);
        for i in 0..n {
            let t = 2.0 * std::f64::consts::PI * i as f64 / n as f64;
            let phase = color_id as f64 * 0.7;
            positions.push([
                (t + phase).cos() * 3.0 + (t * 2.0).sin() * 0.5,
                (t + phase).sin() * 3.0 + (t * 3.0).cos() * 0.5,
                (t * 0.5 + phase).sin() * 1.5,
            ]);
            velocities.push([
                -(t + phase).sin() * 0.3,
                (t + phase).cos() * 0.3,
                (t * 0.5).cos() * 0.1,
            ]);
        }
        StringLoop { positions, velocities, color_id }
    }

    fn len(&self) -> usize {
        self.positions.len()
    }

    fn energy(&self) -> f64 {
        let n = self.len();
        let mut ke = 0.0f64;
        let mut pe = 0.0f64;
        for i in 0..n {
            let v = self.velocities[i];
            ke += 0.5 * (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
            let next = (i + 1) % n;
            let dp = [
                self.positions[next][0] - self.positions[i][0],
                self.positions[next][1] - self.positions[i][1],
                self.positions[next][2] - self.positions[i][2],
            ];
            pe += (dp[0] * dp[0] + dp[1] * dp[1] + dp[2] * dp[2]).sqrt();
        }
        ke + pe
    }

    fn resample(&self, target_n: usize) -> StringLoop {
        let n = self.len();
        if n == target_n {
            return self.clone();
        }
        let mut new_pos = Vec::with_capacity(target_n);
        let mut new_vel = Vec::with_capacity(target_n);
        for i in 0..target_n {
            let t = i as f64 / target_n as f64 * n as f64;
            let idx = t as usize % n;
            let frac = t - t.floor();
            let next = (idx + 1) % n;
            let lerp = |a: f64, b: f64| a + frac * (b - a);
            new_pos.push([
                lerp(self.positions[idx][0], self.positions[next][0]),
                lerp(self.positions[idx][1], self.positions[next][1]),
                lerp(self.positions[idx][2], self.positions[next][2]),
            ]);
            new_vel.push([
                lerp(self.velocities[idx][0], self.velocities[next][0]),
                lerp(self.velocities[idx][1], self.velocities[next][1]),
                lerp(self.velocities[idx][2], self.velocities[next][2]),
            ]);
        }
        StringLoop { positions: new_pos, velocities: new_vel, color_id: self.color_id }
    }
}

#[wasm_bindgen]
pub struct StringSimulation {
    loops: Vec<StringLoop>,
    coupling: f64,
    next_color_id: u32,
}

#[wasm_bindgen]
impl StringSimulation {
    #[wasm_bindgen(constructor)]
    pub fn new(coupling: f64) -> Self {
        let mut loops = Vec::new();
        loops.push(StringLoop::new(64, 0));
        loops.push(StringLoop::new(48, 1));
        StringSimulation {
            loops,
            coupling,
            next_color_id: 2,
        }
    }

    pub fn step(&mut self, dt: f64) {
        let dt2 = dt * dt;
        for lp in &mut self.loops {
            let n = lp.len();
            let mut forces: Vec<[f64; 3]> = vec![[0.0; 3]; n];

            // Compute Laplacian-based string forces (wave equation in conformal gauge)
            for i in 0..n {
                let prev = if i == 0 { n - 1 } else { i - 1 };
                let next = (i + 1) % n;
                for d in 0..3 {
                    let laplacian = lp.positions[prev][d] - 2.0 * lp.positions[i][d] + lp.positions[next][d];
                    forces[i][d] = lp.coupling_force(laplacian, self.coupling);
                }
            }

            // Velocity Verlet integration
            for i in 0..n {
                for d in 0..3 {
                    lp.positions[i][d] += lp.velocities[i][d] * dt + 0.5 * forces[i][d] * dt2;
                }
            }
            // Recompute forces at new positions
            let mut forces_new: Vec<[f64; 3]> = vec![[0.0; 3]; n];
            for i in 0..n {
                let prev = if i == 0 { n - 1 } else { i - 1 };
                let next = (i + 1) % n;
                for d in 0..3 {
                    let laplacian = lp.positions[prev][d] - 2.0 * lp.positions[i][d] + lp.positions[next][d];
                    forces_new[i][d] = lp.coupling_force(laplacian, self.coupling);
                }
            }
            // Update velocities
            for i in 0..n {
                for d in 0..3 {
                    lp.velocities[i][d] += 0.5 * (forces[i][d] + forces_new[i][d]) * dt;
                    // Clamp velocity for stability
                    lp.velocities[i][d] = lp.velocities[i][d].clamp(-5.0, 5.0);
                }
            }
        }

        // Check for self-intersections and split
        if self.loops.len() < MAX_LOOPS {
            self.check_intersections();
        }

        // Resample to maintain point density
        self.resample_loops();
    }

    fn check_intersections(&mut self) {
        let mut new_loops: Vec<StringLoop> = Vec::new();
        let mut to_remove: Vec<usize> = Vec::new();

        for loop_idx in 0..self.loops.len() {
            let lp = &self.loops[loop_idx];
            let n = lp.len();
            let mut split_point: Option<(usize, usize)> = None;

            'outer: for i in 0..n {
                for j in (i + 4)..n {
                    if j == n - 1 && i == 0 { continue; }
                    // Both child segments must be large enough to survive.
                    // Segment A: i..=j  → j - i + 1 points
                    // Segment B: j..n + 0..=i → (n - j) + (i + 1) points
                    let len_a = j - i + 1;
                    let len_b = (n - j) + (i + 1);
                    if len_a < MIN_LOOP_POINTS || len_b < MIN_LOOP_POINTS { continue; }
                    let dist = dist3d(lp.positions[i], lp.positions[j]);
                    if dist < INTERSECTION_THRESHOLD {
                        // Probabilistic split
                        let prob = (self.coupling * 0.3).min(0.8);
                        if js_random() < prob {
                            split_point = Some((i, j));
                            break 'outer;
                        }
                    }
                }
            }

            if let Some((i, j)) = split_point {
                to_remove.push(loop_idx);
                let (a, b) = split_loop(lp, i, j, self.next_color_id, self.next_color_id + 1);
                self.next_color_id += 2;
                if a.len() >= MIN_LOOP_POINTS { new_loops.push(a); }
                if b.len() >= MIN_LOOP_POINTS { new_loops.push(b); }
            }
        }

        for idx in to_remove.into_iter().rev() {
            self.loops.remove(idx);
        }
        self.loops.extend(new_loops);
    }

    fn resample_loops(&mut self) {
        for lp in &mut self.loops {
            let n = lp.len();
            let total_len: f64 = (0..n).map(|i| {
                let next = (i + 1) % n;
                dist3d(lp.positions[i], lp.positions[next])
            }).sum();
            let target = ((total_len / TARGET_POINT_DENSITY) as usize)
                .max(MIN_LOOP_POINTS)
                .min(256);
            if (target as i64 - n as i64).abs() > 10 {
                *lp = lp.resample(target);
            }
        }
    }

    pub fn set_coupling(&mut self, coupling: f64) {
        self.coupling = coupling;
    }

    /// Returns flat array: [loop_count, n0, x0, y0, z0, ..., n1, x0, ...]
    pub fn get_positions(&self) -> Vec<f64> {
        let mut out = vec![self.loops.len() as f64];
        for lp in &self.loops {
            out.push(lp.len() as f64);
            out.push(lp.color_id as f64);
            for p in &lp.positions {
                out.push(p[0]);
                out.push(p[1]);
                out.push(p[2]);
            }
        }
        out
    }

    /// Returns flat velocity magnitudes per point per loop (same structure as positions)
    pub fn get_velocities_mag(&self) -> Vec<f64> {
        let mut out = vec![self.loops.len() as f64];
        for lp in &self.loops {
            out.push(lp.len() as f64);
            for v in &lp.velocities {
                let mag = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt();
                out.push(mag);
            }
        }
        out
    }

    pub fn get_total_energy(&self) -> f64 {
        self.loops.iter().map(|l| l.energy()).sum()
    }

    pub fn get_loop_count(&self) -> u32 {
        self.loops.len() as u32
    }
}

impl StringLoop {
    fn coupling_force(&self, laplacian: f64, coupling: f64) -> f64 {
        coupling * laplacian
    }
}

fn dist3d(a: [f64; 3], b: [f64; 3]) -> f64 {
    let dx = a[0] - b[0];
    let dy = a[1] - b[1];
    let dz = a[2] - b[2];
    (dx * dx + dy * dy + dz * dz).sqrt()
}

fn split_loop(lp: &StringLoop, i: usize, j: usize, c1: u32, c2: u32) -> (StringLoop, StringLoop) {
    let n = lp.len();
    // Segment A: i..=j
    let pos_a: Vec<[f64; 3]> = (i..=j).map(|k| lp.positions[k % n]).collect();
    let vel_a: Vec<[f64; 3]> = (i..=j).map(|k| lp.velocities[k % n]).collect();
    // Segment B: j..n and 0..=i
    let mut pos_b: Vec<[f64; 3]> = (j..n).map(|k| lp.positions[k]).collect();
    pos_b.extend((0..=i).map(|k| lp.positions[k]));
    let mut vel_b: Vec<[f64; 3]> = (j..n).map(|k| lp.velocities[k]).collect();
    vel_b.extend((0..=i).map(|k| lp.velocities[k]));
    (
        StringLoop { positions: pos_a, velocities: vel_a, color_id: c1 },
        StringLoop { positions: pos_b, velocities: vel_b, color_id: c2 },
    )
}

fn js_random() -> f64 {
    js_sys::Math::random()
}
