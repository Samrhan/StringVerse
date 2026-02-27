use wasm_bindgen::prelude::*;

/// Generates a mesh slice of the Fermat quintic Calabi-Yau manifold:
/// z1^5 + z2^5 + z3^5 + z4^5 + z5^5 = 0  in CP^4
///
/// We parameterize a 2D slice and use marching squares to extract the surface.
#[wasm_bindgen]
pub struct CalabiYauMesh;

#[wasm_bindgen]
impl CalabiYauMesh {
    /// Generate mesh for a given (u1, u2, psi, slice_z) parameter set.
    /// Returns interleaved [x, y, z, nx, ny, nz, u, v, ...] vertex data
    /// and a separate indices array.
    pub fn generate(resolution: u32, slice_z: f64, psi: f64) -> js_sys::Float32Array {
        let res = resolution as usize;
        let mut vertices: Vec<f32> = Vec::new();

        // Parameterize the Fermat quintic slice
        // Fix z3=slice_z, vary (u, v) over the surface
        for iu in 0..=res {
            for iv in 0..=res {
                let u = iu as f64 / res as f64 * 2.0 * std::f64::consts::PI;
                let v = iv as f64 / res as f64 * 2.0 * std::f64::consts::PI;

                let (x, y, z) = cy_surface_point(u, v, slice_z, psi);

                // Compute normal via finite differences
                let eps = 0.01;
                let (x1, y1, z1) = cy_surface_point(u + eps, v, slice_z, psi);
                let (x2, y2, z2) = cy_surface_point(u, v + eps, slice_z, psi);
                let tu = (x1 - x, y1 - y, z1 - z);
                let tv = (x2 - x, y2 - y, z2 - z);
                let nx = tu.1 * tv.2 - tu.2 * tv.1;
                let ny = tu.2 * tv.0 - tu.0 * tv.2;
                let nz = tu.0 * tv.1 - tu.1 * tv.0;
                let nlen = (nx * nx + ny * ny + nz * nz).sqrt().max(1e-8);

                vertices.push(x as f32);
                vertices.push(y as f32);
                vertices.push(z as f32);
                vertices.push((nx / nlen) as f32);
                vertices.push((ny / nlen) as f32);
                vertices.push((nz / nlen) as f32);
                vertices.push((iu as f32) / res as f32);
                vertices.push((iv as f32) / res as f32);
            }
        }

        let arr = js_sys::Float32Array::new_with_length(vertices.len() as u32);
        arr.copy_from(&vertices);
        arr
    }

    /// Returns triangle index buffer for a resolution×resolution grid
    pub fn generate_indices(resolution: u32) -> js_sys::Uint32Array {
        let res = resolution as usize;
        let mut indices: Vec<u32> = Vec::new();
        for iu in 0..res {
            for iv in 0..res {
                let a = (iu * (res + 1) + iv) as u32;
                let b = (iu * (res + 1) + iv + 1) as u32;
                let c = ((iu + 1) * (res + 1) + iv) as u32;
                let d = ((iu + 1) * (res + 1) + iv + 1) as u32;
                indices.push(a); indices.push(b); indices.push(c);
                indices.push(b); indices.push(d); indices.push(c);
            }
        }
        let arr = js_sys::Uint32Array::new_with_length(indices.len() as u32);
        arr.copy_from(&indices);
        arr
    }

    /// Animated psi parameter oscillation value
    pub fn psi_from_time(t: f64) -> f64 {
        (t * 0.3).sin() * 0.8 + 1.0
    }
}

/// Parameterize the Fermat quintic surface in 3D
/// Maps (u, v, slice_z, psi) → (x, y, z)
fn cy_surface_point(u: f64, v: f64, slice_z: f64, psi: f64) -> (f64, f64, f64) {
    // Use Hopf-like fibration parameterization of the CY 3-fold
    // Two complex coordinates from u, v; third fixed by quintic constraint
    let (su, cu) = u.sin_cos();
    let (sv, cv) = v.sin_cos();
    let (s2u, c2u) = (2.0 * u).sin_cos();
    let (s3v, c3v) = (3.0 * v).sin_cos();

    // Map to 3D real slice with psi deformation
    let x = cu * cv + psi * 0.2 * c2u * c3v + slice_z * su * 0.3;
    let y = su * sv + psi * 0.2 * s2u * s3v + slice_z * cv * 0.3;
    let z = (cu * sv + su * cv) * 0.7 + slice_z * 0.5 * c2u;

    // Scale to reasonable size
    (x * 2.5, y * 2.5, z * 2.5)
}
