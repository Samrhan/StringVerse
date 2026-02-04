# StringVerse

**Visualisation Interactive de la Théorie des Cordes / Interactive String Theory Visualization**

StringVerse is a physical sandbox designed to visualize abstract concepts from string theory. The goal is to provide physical intuition and aesthetic visualization rather than absolute numerical precision ("Physical intuition over Numerical precision").

![String Visualization](https://img.shields.io/badge/Status-Active-green)

## Features

StringVerse offers three distinct interactive simulation modules:

### 1. The Relativistic String (Nambu-Goto)
Visualizes a relativistic closed string oscillating in 3D space with **dynamic topology changes**.
- **Physics:** Solves the wave equation for a string in conformal gauge using a symplectic Velocity Verlet integrator.
- **Splitting:** Detects self-intersections using vectorized O(N²) collision detection and performs topological surgery to create daughter strings.
- **Multi-Loop Dynamics:** Supports up to 8 simultaneous string loops, each evolving independently with automatic resampling for numerical stability.
- **Visualization:** Renders multiple strings as smooth splines with distinct colors. Local velocity is indicated by color (red/white = relativistic speeds).
- **Interaction:** Adjust the string tension (coupling constant) in real-time. Watch strings split when they cross themselves!

### 2. The Matrix Model (BFSS)
Simulates the mechanics of D0-branes using a simplified Bosonic BFSS matrix model with **GPU acceleration**.
- **Physics:** Simulates the dynamics of non-commuting Hermitian matrices with a commutator potential $V \sim -Tr([X_i, X_j]^2)$.
- **GPU Support:** Uses CuPy for GPU-accelerated force computation (up to N=128 matrices). Falls back to NumPy for CPU mode (N=32).
- **Emergent Geometry:** Connection strengths between D0-branes are derived from off-diagonal matrix elements, revealing emergent spatial structure.
- **Visualization:** Represents the eigenvalues (D0-branes) as a dynamic point cloud with physics-based connections showing matrix correlations.
- **Interaction:** 
  - Adjust "mass" (confinement) and coupling to see phase transitions from dispersed gas to compact geometry
  - Press **SPACE** to trigger an explosive "poke" with spectacular after-burn effects
  - Real-time HUD shows GPU status and simulation parameters

### 3. Calabi-Yau Manifolds
Visualizes the hidden extra dimensions of string theory with **interactive slicing**.
- **Visualization:** Renders a 3D slice of the quintic Calabi-Yau manifold defined by $\sum z_i^5 = 0$.
- **Interactive Slicer:** Animated slice plane with real-time control to explore the manifold's internal structure.
- **Interaction:** Use the slider to navigate through different cross-sections of the compactified dimensions.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd stringverse
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Optional: GPU Acceleration (for Matrix Model)**
   ```bash
   poetry install --with gpu
   ```
   This installs CuPy for CUDA-enabled GPUs, dramatically improving performance for large N matrix simulations.

   Or manually with pip:
   ```bash
   pip install numpy scipy pyvista tqdm scikit-image
   # For GPU support:
   pip install cupy-cuda12x  # or cupy-cuda11x depending on your CUDA version
   ```

## Usage

### Interactive Mode
To start the application:

```bash
poetry run python -m stringverse.main
```

**Controls:**
- **Mouse:** Rotate, zoom, and pan the camera.
- **Keys 1, 2, 3:** Switch between modules:
  - `1`: Nambu-Goto String (watch for splits!)
  - `2`: BFSS Matrix Model (press SPACE to poke!)
  - `3`: Calabi-Yau Manifold
- **Sliders:** Adjust simulation parameters (Coupling, Mass, Slice Position) in the UI.
- **SPACE:** Trigger explosive poke in Matrix Model
- **Q:** Quit the application.

### Headless Mode (Testing)
To run the simulation without a window (useful for checking physics stability):

```bash
python -m stringverse.main --headless
```

## Architecture
The project follows a strict **MVC (Model-View-Controller)** pattern:

- **Model (`src/stringverse/physics`):** Pure Python/NumPy implementation of physical laws. Stateless steps. GPU-accelerated where applicable (CuPy).
- **View (`src/stringverse/visualization`):** PyVista/VTK rendering logic with optimized actor pools for multi-object scenes.
- **Controller (`src/stringverse/main.py`):** Orchestrates the simulation loop, user inputs, and module switching.

### Directory Structure
```
stringverse/
├── src/
│   └── stringverse/
│       ├── core/           # Data models and interfaces (StringLoop, SimulationConfig)
│       ├── physics/        # Physics engines (Nambu-Goto with splitting, BFSS with GPU)
│       ├── visualization/  # Renderers (Multi-loop string, Matrix with HUD, CY slicer)
│       ├── utils/          # Utilities (CY mesh generators)
│       └── main.py         # Entry point
├── tests/                  # Unit tests
└── pyproject.toml          # Project configuration (with optional GPU dependencies)
```

## Technical Highlights

### String Splitting Implementation
- **Collision Detection:** Vectorized distance matrix computation using SciPy's `cdist` for O(N²) self-intersection checks
- **Topological Surgery:** Array slicing to split parent loop into two daughter loops at intersection points
- **Resampling:** Cubic spline interpolation to maintain uniform point density after topology changes
- **Multi-Loop Rendering:** Pre-allocated actor pool with distinct colors for up to 8 simultaneous string loops

### GPU Acceleration
- **CuPy Integration:** Seamless NumPy→CuPy API compatibility with automatic fallback
- **Vectorized Forces:** Batched matrix operations for commutator potential computation
- **Performance:** ~10-100× speedup for N=64-128 matrix dimensions on CUDA GPUs

### Performance Optimizations
- **No Tube Regeneration:** Uses `render_lines_as_tubes=True` instead of costly `tube()` geometry creation
- **Actor Pooling:** Pre-allocated mesh actors for efficient show/hide toggling
- **Damping & Clamping:** Numerical stability for stiff systems without sacrificing physics fidelity

## License
MIT
