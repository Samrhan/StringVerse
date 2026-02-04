"""
GPU-Accelerated BFSS Matrix Model Engine.

Uses CuPy for NVIDIA GPU acceleration with NumPy fallback.
Target: N=100+ at 60 FPS for visible emergent geometry.
"""
import numpy as np
import numpy.typing as npt
from typing import List
from stringverse.core.models import SimulationConfig, MatrixState
from stringverse.core.interfaces import PhysicsEngine

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    GPU_AVAILABLE = True
    print("🚀 CuPy detected! GPU acceleration enabled.")
except ImportError:
    cp = None
    GPU_AVAILABLE = False
    print("⚠️  CuPy not found. Using CPU (NumPy). Install cupy for GPU acceleration.")


class BFSSMatrixModel(PhysicsEngine):
    """
    GPU-Accelerated BFSS Matrix Model.
    
    Simulates the Bosonic part of the BFSS Matrix Model.
    Hamiltonian: H = Tr( 0.5 * P_I^2 - 0.25 * [X_I, X_J]^2 + 0.5 * m^2 * X_I^2 )
    
    With GPU: Can handle N=100+ at 60 FPS (emergent geometry visible!)
    Without GPU: Limited to N~32 for real-time performance.
    """

    def __init__(self) -> None:
        self.config: SimulationConfig | None = None
        self.n_size: int = 0
        self.mass: float = 1.0
        self.damping: float = 0.01
        self.base_damping: float = 0.01
        self.afterburn_damping: float = 0.15
        self.afterburn_timer: float = 0.0
        self.max_value: float = 50.0
        
        # GPU or CPU array library
        self.xp = cp if GPU_AVAILABLE else np
        self.use_gpu = GPU_AVAILABLE
        
        # Matrices stored on GPU (if available)
        self._matrices = None  # Shape (3, N, N)
        self._velocities = None  # Shape (3, N, N)

    def initialize(self, config: SimulationConfig) -> None:
        self.config = config
        
        # With GPU, we can handle larger N
        if self.use_gpu:
            self.n_size = min(config.resolution, 128)  # GPU can handle 128
        else:
            self.n_size = min(config.resolution, 32)   # CPU limited to 32
        
        xp = self.xp
        
        # Initialize random Hermitian matrices on GPU/CPU
        self._matrices = xp.zeros((3, self.n_size, self.n_size), dtype=xp.complex128)
        self._velocities = xp.zeros((3, self.n_size, self.n_size), dtype=xp.complex128)
        
        for i in range(3):
            # Random complex matrix
            A = xp.random.randn(self.n_size, self.n_size) + 1j * xp.random.randn(self.n_size, self.n_size)
            # Make Hermitian: X = (A + A†) / 2
            self._matrices[i] = (A + xp.conj(A.T)) * 0.1
            
            # Initial velocities (thermal)
            V = xp.random.randn(self.n_size, self.n_size) + 1j * xp.random.randn(self.n_size, self.n_size)
            self._velocities[i] = (V + xp.conj(V.T)) * 0.01
        
        print(f"{'🚀 GPU' if self.use_gpu else '🐢 CPU'} Matrix Model initialized with N={self.n_size}")

    def _compute_forces_gpu(self, X):
        """
        Vectorized force computation optimized for GPU.
        Uses batch operations instead of loops where possible.
        """
        xp = self.xp
        coupling = self.config.coupling_constant
        forces = xp.zeros_like(X)
        
        # Precompute all commutators [X_i, X_j] for i < j
        # comm[0] = [X0, X1], comm[1] = [X0, X2], comm[2] = [X1, X2]
        comm_01 = X[0] @ X[1] - X[1] @ X[0]
        comm_02 = X[0] @ X[2] - X[2] @ X[0]
        comm_12 = X[1] @ X[2] - X[2] @ X[1]
        
        # Force on X[0]: [X1, [X0,X1]] + [X2, [X0,X2]]
        forces[0] = (X[1] @ comm_01 - comm_01 @ X[1]) + (X[2] @ comm_02 - comm_02 @ X[2])
        
        # Force on X[1]: [X0, [X1,X0]] + [X2, [X1,X2]]
        # Note: [X1,X0] = -[X0,X1]
        forces[1] = (X[0] @ (-comm_01) - (-comm_01) @ X[0]) + (X[2] @ comm_12 - comm_12 @ X[2])
        
        # Force on X[2]: [X0, [X2,X0]] + [X1, [X2,X1]]
        forces[2] = (X[0] @ (-comm_02) - (-comm_02) @ X[0]) + (X[1] @ (-comm_12) - (-comm_12) @ X[1])
        
        # Apply coupling and mass term
        forces = coupling * forces - self.mass * X
        
        return forces

    def step(self, dt: float) -> None:
        if self._matrices is None or self._velocities is None:
            return
        
        xp = self.xp
        
        # After-burn effect
        if self.afterburn_timer > 0:
            self.afterburn_timer -= dt
            t = max(0, self.afterburn_timer) / 2.0
            self.damping = self.base_damping + (self.afterburn_damping - self.base_damping) * t
        else:
            self.damping = self.base_damping

        # Velocity Verlet integration (GPU-optimized)
        forces = self._compute_forces_gpu(self._matrices)
        self._velocities += 0.5 * forces * dt
        self._velocities *= (1.0 - self.damping)
        self._matrices += self._velocities * dt
        
        # Clamp to prevent overflow
        self._matrices = xp.clip(self._matrices, -self.max_value, self.max_value)
        
        forces_new = self._compute_forces_gpu(self._matrices)
        self._velocities += 0.5 * forces_new * dt
        self._velocities *= (1.0 - self.damping)

    def poke(self, strength: float = 5.0) -> None:
        """Explosive perturbation with after-burn effect."""
        if self._velocities is None:
            return
        
        xp = self.xp
        
        for i in range(3):
            V = xp.random.randn(self.n_size, self.n_size) + 1j * xp.random.randn(self.n_size, self.n_size)
            self._velocities[i] += (V + xp.conj(V.T)) * strength
        
        self.afterburn_timer = 2.0
        self.damping = self.afterburn_damping

    def get_state(self) -> MatrixState:
        """
        Extract visualization state.
        Transfers data from GPU to CPU for rendering.
        """
        if self._matrices is None:
            raise RuntimeError("Physics engine not initialized")
        
        xp = self.xp
        
        # Transfer to CPU if on GPU
        if self.use_gpu:
            matrices_cpu = cp.asnumpy(self._matrices)
        else:
            matrices_cpu = self._matrices
        
        # Eigenvalue computation (on CPU - NumPy's eigvalsh is fast enough)
        try:
            x_eig = np.real(np.linalg.eigvalsh(matrices_cpu[0]))
            y_eig = np.real(np.linalg.eigvalsh(matrices_cpu[1]))
            z_eig = np.real(np.linalg.eigvalsh(matrices_cpu[2]))
        except np.linalg.LinAlgError:
            x_eig = np.real(np.diagonal(matrices_cpu[0]))
            y_eig = np.real(np.diagonal(matrices_cpu[1]))
            z_eig = np.real(np.diagonal(matrices_cpu[2]))
        
        # Sort for consistent visualization
        x_eig = np.sort(x_eig)
        y_eig = np.sort(y_eig)
        z_eig = np.sort(z_eig)
        
        points = np.column_stack((x_eig, y_eig, z_eig))
        
        # Connection strengths from off-diagonal elements
        connection_strengths = np.zeros((self.n_size, self.n_size), dtype=np.float64)
        for k in range(3):
            connection_strengths += np.abs(matrices_cpu[k]) ** 2
        
        np.fill_diagonal(connection_strengths, 0)
        
        max_strength = np.max(connection_strengths)
        if max_strength > 0:
            connection_strengths /= max_strength
        
        return MatrixState(
            matrices=[m.copy() for m in matrices_cpu],
            eigenvalues=points,
            connection_strengths=connection_strengths
        )
    
    # Property accessors for compatibility
    @property
    def matrices(self):
        if self.use_gpu and self._matrices is not None:
            return cp.asnumpy(self._matrices)
        return self._matrices
    
    @property
    def velocities(self):
        if self.use_gpu and self._velocities is not None:
            return cp.asnumpy(self._velocities)
        return self._velocities
