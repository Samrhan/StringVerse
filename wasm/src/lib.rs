mod string_physics;
mod matrix_physics;
mod calabi_yau;

use wasm_bindgen::prelude::*;

#[wasm_bindgen(start)]
pub fn init() {
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

pub use string_physics::StringSimulation;
pub use matrix_physics::MatrixSimulation;
pub use calabi_yau::CalabiYauMesh;
