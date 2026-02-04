# StringVerse

**Visualisation Interactive de la Théorie des Cordes / Interactive String Theory Visualization**

StringVerse is a physical sandbox designed to visualize abstract concepts from string theory. The goal is to provide physical intuition and aesthetic visualization rather than absolute numerical precision ("Physical intuition over Numerical precision").

![String Visualization](https://img.shields.io/badge/Status-Active-green)

## Features

StringVerse offers three distinct interactive simulation modules:

### 1. The Relativistic String (Nambu-Goto)
Visualizes a relativistic closed string oscillating in 3D space.
- **Physics:** Solves the wave equation for a string in conformal gauge using a symplectic Velocity Verlet integrator.
- **Visualization:** Renders the string as a smooth spline where color represents local velocity (red/white indicates relativistic speeds).
- **Interaction:** Adjust the string tension (coupling constant) in real-time.

### 2. The Matrix Model (BFSS)
Simulates the mechanics of D0-branes using a simplified Bosonic BFSS matrix model.
- **Physics:** Simulates the dynamics of non-commuting Hermitian matrices with a commutator potential potential $V \sim -Tr([X_i, X_j]^2)$.
- **Visualization:** Represents the eigenvalues (D0-branes) as a dynamic point cloud of spheres.
- **Interaction:** Manipulate the "mass" (confinement) and coupling to see the transition from a dispersed gas to a compact geometry.

### 3. Calabi-Yau Manifolds
Visualizes the hidden extra dimensions of string theory.
- **Visualization:** Renders a 3D slice of the quintic Calabi-Yau manifold defined by $\sum z_i^5 = 0$.
- **Interaction:** Inspect the complex internal structure responsible for compactification.

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

   Or manually with pip:
   ```bash
   pip install numpy scipy pyvista tqdm scikit-image
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
  - `1`: Nambu-Goto String
  - `2`: BFSS Matrix Model
  - `3`: Calabi-Yau Manifold
- **Sliders:** Adjust simulation parameters (Coupling, Mass) in the UI.
- **Q:** Quit the application.

### Headless Mode (Testing)
To run the simulation without a window (useful for checking physics stability):

```bash
python -m stringverse.main --headless
```

## Architecture
The project follows a strict **MVC (Model-View-Controller)** pattern:

- **Model (`src/stringverse/physics`):** Pure Python/NumPy implementation of physical laws. Stateless steps.
- **View (`src/stringverse/visualization`):** PyVista/VTK rendering logic.
- **Controller (`src/stringverse/main.py`):** Orchestrates the simulation loop, user inputs, and module switching.

### Directory Structure
```
stringverse/
├── src/
│   └── stringverse/
│       ├── core/           # Data models and interfaces
│       ├── physics/        # Physics engines (Nambu-Goto, BFSS)
│       ├── visualization/  # Renderers (String, Matrix, CY)
│       ├── utils/          # Utilities (Mesh generators)
│       └── main.py         # Entry point
├── tests/                  # Unit tests
└── pyproject.toml          # Project configuration
```

## License
MIT
