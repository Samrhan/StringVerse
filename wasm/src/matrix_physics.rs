use wasm_bindgen::prelude::*;

/// BFSS Matrix Model (D0-Branes)
/// Bosonic Hamiltonian: H = Tr(0.5*P^2 - 0.25*[Xi,Xj]^2 + 0.5*m^2*Xi^2)
#[wasm_bindgen]
pub struct MatrixSimulation {
    n: usize,
    // 3 Hermitian matrices X1, X2, X3 stored as flat real arrays (n*n each)
    x: Vec<Vec<f64>>,
    // Conjugate momenta
    p: Vec<Vec<f64>>,
    mass: f64,
    coupling: f64,
    damping: f64,
}

#[wasm_bindgen]
impl MatrixSimulation {
    #[wasm_bindgen(constructor)]
    pub fn new(n: u32, coupling: f64, mass: f64) -> Self {
        let n = n as usize;
        let mut x = vec![vec![0.0f64; n * n]; 3];
        let p = vec![vec![0.0f64; n * n]; 3];

        // Initialize with small random Hermitian matrices
        for i in 0..3 {
            for a in 0..n {
                for b in a..n {
                    let val = (js_random() - 0.5) * 0.5;
                    x[i][a * n + b] = val;
                    x[i][b * n + a] = val; // symmetric (real Hermitian)
                }
            }
        }

        MatrixSimulation { n, x, p, mass, coupling, damping: 0.01 }
    }

    pub fn step(&mut self, dt: f64) {
        let n = self.n;
        let dt2 = dt * dt;

        // Compute forces F_i = [X_j, [X_j, X_i]] - m^2 * X_i  (summed over j≠i)
        let forces = self.compute_forces();

        // Velocity Verlet: update positions
        for i in 0..3 {
            for idx in 0..(n * n) {
                self.x[i][idx] += self.p[i][idx] * dt + 0.5 * forces[i][idx] * dt2;
            }
        }

        let forces_new = self.compute_forces();

        // Update momenta with damping
        let damp = 1.0 - self.damping * dt;
        for i in 0..3 {
            for idx in 0..(n * n) {
                self.p[i][idx] = damp * (self.p[i][idx] + 0.5 * (forces[i][idx] + forces_new[i][idx]) * dt);
                self.p[i][idx] = self.p[i][idx].clamp(-10.0, 10.0);
            }
        }

        // Re-symmetrize to maintain Hermiticity
        for i in 0..3 {
            for a in 0..n {
                for b in (a + 1)..n {
                    let avg = 0.5 * (self.x[i][a * n + b] + self.x[i][b * n + a]);
                    self.x[i][a * n + b] = avg;
                    self.x[i][b * n + a] = avg;
                }
            }
        }
    }

    fn compute_forces(&self) -> Vec<Vec<f64>> {
        let n = self.n;
        let mut forces = vec![vec![0.0f64; n * n]; 3];

        for i in 0..3 {
            for j in 0..3 {
                if i == j { continue; }
                // f_i += [X_j, [X_j, X_i]] * coupling^2
                let comm_ji = commutator(&self.x[j], &self.x[i], n);
                let double_comm = commutator(&self.x[j], &comm_ji, n);
                for idx in 0..(n * n) {
                    forces[i][idx] += self.coupling * self.coupling * double_comm[idx];
                }
            }
            // Mass term: f_i -= m^2 * X_i
            for idx in 0..(n * n) {
                forces[i][idx] -= self.mass * self.mass * self.x[i][idx];
            }
        }
        forces
    }

    /// Poke: add random momentum kick
    pub fn poke(&mut self, strength: f64) {
        for i in 0..3 {
            for idx in 0..(self.n * self.n) {
                self.p[i][idx] += (js_random() - 0.5) * strength * 2.0;
            }
        }
    }

    pub fn set_coupling(&mut self, coupling: f64) {
        self.coupling = coupling;
    }

    pub fn set_mass(&mut self, mass: f64) {
        self.mass = mass;
    }

    /// Returns eigenvalues (D0-brane positions) as flat [n * 3] array
    /// We approximate eigenvalues via diagonal elements (true eigendecomp is expensive in WASM)
    pub fn get_eigenvalues(&self) -> Vec<f64> {
        let n = self.n;
        let mut out = Vec::with_capacity(n * 3);
        // Extract diagonal of each matrix as proxy for eigenvalues
        for a in 0..n {
            for i in 0..3 {
                out.push(self.x[i][a * n + a]);
            }
        }
        out
    }

    /// Returns connection strengths between branes: flat [n*n] upper-triangle values
    pub fn get_connections(&self) -> Vec<f64> {
        let n = self.n;
        let mut out = Vec::new();
        for a in 0..n {
            for b in (a + 1)..n {
                // Off-diagonal magnitude in all 3 matrices
                let mut strength = 0.0f64;
                for i in 0..3 {
                    let v = self.x[i][a * n + b];
                    strength += v * v;
                }
                out.push(a as f64);
                out.push(b as f64);
                out.push(strength.sqrt());
            }
        }
        out
    }

    pub fn get_energy(&self) -> f64 {
        let n = self.n;
        let mut ke = 0.0f64;
        let mut potential = 0.0f64;

        for i in 0..3 {
            for idx in 0..(n * n) {
                ke += 0.5 * self.p[i][idx] * self.p[i][idx];
                potential += 0.5 * self.mass * self.mass * self.x[i][idx] * self.x[i][idx];
            }
        }

        for i in 0..3 {
            for j in (i + 1)..3 {
                let comm = commutator(&self.x[i], &self.x[j], n);
                for idx in 0..(n * n) {
                    potential -= 0.25 * self.coupling * self.coupling * comm[idx] * comm[idx];
                }
            }
        }

        ke + potential
    }
}

/// Compute commutator [A, B] = AB - BA for n×n real matrices stored as flat arrays
fn commutator(a: &[f64], b: &[f64], n: usize) -> Vec<f64> {
    let mut result = vec![0.0f64; n * n];
    for i in 0..n {
        for j in 0..n {
            let mut ab = 0.0f64;
            let mut ba = 0.0f64;
            for k in 0..n {
                ab += a[i * n + k] * b[k * n + j];
                ba += b[i * n + k] * a[k * n + j];
            }
            result[i * n + j] = ab - ba;
        }
    }
    result
}

fn js_random() -> f64 {
    js_sys::Math::random()
}
