from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
import numpy.typing as npt

# Type Alias for clarity
Vector3D = npt.NDArray[np.float64]  # Shape (N, 3)

@dataclass(slots=True)
class SimulationConfig:
    """Immutable configuration for a simulation."""
    time_step: float = 0.01
    resolution: int = 100  # Number of points or matrix size N
    coupling_constant: float = 1.0  # g_s or tension

@dataclass(slots=True)
class StringState:
    """Instantaneous state of a Nambu-Goto string."""
    positions: Vector3D  # (N, 3)
    velocities: Vector3D # (N, 3)
    energy: float

@dataclass(slots=True)
class MatrixState:
    """Instantaneous state of the BFSS model (D0-branes)."""
    # 9 bosonic matrices X_I of size (N, N)
    matrices: List[npt.NDArray[np.complex128]] 
    eigenvalues: Vector3D # For rendering (point cloud)
    # Off-diagonal coupling strengths for emergent geometry
    # Shape (N, N) - connection_strength[i,j] = how strongly brane i and j are connected
    connection_strengths: Optional[npt.NDArray[np.float64]] = None
