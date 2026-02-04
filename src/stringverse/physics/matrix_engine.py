import numpy as np
import numpy.typing as npt
from typing import List
from stringverse.core.models import SimulationConfig, MatrixState
from stringverse.core.interfaces import PhysicsEngine

class BFSSMatrixModel(PhysicsEngine):
    """
    Simulates the Bosonic part of the BFSS Matrix Model (or a simplified Yang-Mills quantum mechanics).
    Hamiltonian: H = Tr( 0.5 * P_I^2 - 0.25 * [X_I, X_J]^2 + 0.5 * m^2 * X_I^2 )
    We simulate 3 matrices (X, Y, Z) for 3D visualization.
    """

    def __init__(self) -> None:
        self.config: SimulationConfig | None = None
        self.matrices: npt.NDArray[np.complex128] | None = None # Shape (3, N, N)
        self.velocities: npt.NDArray[np.complex128] | None = None # Shape (3, N, N)
        self.n_size: int = 0
        self.mass: float = 1.0 # Confinement mass term
        self.damping: float = 0.01 # Damping to prevent runaway
        self.base_damping: float = 0.01 # Store base value for after-burn
        self.afterburn_damping: float = 0.15 # High damping after explosion
        self.afterburn_timer: float = 0.0 # Countdown for after-burn effect
        self.max_value: float = 50.0 # Clamp matrices to prevent overflow

    def initialize(self, config: SimulationConfig) -> None:
        self.config = config
        self.n_size = min(config.resolution, 32) # Limit N for performance
        
        # Initialize random Hermitian matrices
        # X = A + A_dagger
        self.matrices = np.zeros((3, self.n_size, self.n_size), dtype=np.complex128)
        self.velocities = np.zeros((3, self.n_size, self.n_size), dtype=np.complex128)
        
        for i in range(3):
            A = np.random.randn(self.n_size, self.n_size) + 1j * np.random.randn(self.n_size, self.n_size)
            self.matrices[i] = (A + A.conj().T) * 0.1 # Small initial values to prevent overflow
            
            # Initial random velocities (Temperature)
            V = np.random.randn(self.n_size, self.n_size) + 1j * np.random.randn(self.n_size, self.n_size)
            self.velocities[i] = (V + V.conj().T) * 0.01

    def _compute_forces(self, X: npt.NDArray[np.complex128]) -> npt.NDArray[np.complex128]:
        """
        Compute forces: F_i = - dV/dX_i
        V = -1/4 Tr([X_i, X_j]^2) + 0.5 * m^2 * X_i^2
        F_i = sum_j [X_j, [X_i, X_j]] - m^2 * X_i
        """
        forces = np.zeros_like(X)
        coupling = self.config.coupling_constant
        
        # Commutator term: sum_j [X_j, [X_i, X_j]]
        # We iterate over the 3 matrices
        for i in range(3):
            comm_term = np.zeros((self.n_size, self.n_size), dtype=np.complex128)
            for j in range(3):
                if i == j: continue
                
                # [X_i, X_j]
                comm_ij = X[i] @ X[j] - X[j] @ X[i]
                
                # [X_j, [X_i, X_j]]
                # term = X_j @ comm_ij - comm_ij @ X_j
                term = X[j] @ comm_ij - comm_ij @ X[j]
                
                comm_term += term
            
            # Force = Coupling * Commutator_Term - Mass * X_i
            # High coupling constant usually means stronger interaction -> "Tight" geometry?
            # Or is coupling 1/g^2? 
            # In standard convention g is in front of commutator.
            # Let's assume coupling_constant scales the commutator interaction.
            forces[i] = coupling * comm_term - self.mass * X[i]
            
        return forces

    def step(self, dt: float) -> None:
        if self.matrices is None or self.velocities is None:
            return
        
        # After-burn effect: gradually reduce damping back to normal
        if self.afterburn_timer > 0:
            self.afterburn_timer -= dt
            # Smooth exponential decay from afterburn_damping to base_damping
            t = max(0, self.afterburn_timer) / 2.0  # 2 second decay
            self.damping = self.base_damping + (self.afterburn_damping - self.base_damping) * t
        else:
            self.damping = self.base_damping

        # Velocity Verlet with damping
        forces = self._compute_forces(self.matrices)
        self.velocities += 0.5 * forces * dt
        self.velocities *= (1.0 - self.damping)  # Apply damping
        self.matrices += self.velocities * dt
        
        # Clamp matrices to prevent overflow
        self.matrices = np.clip(self.matrices, -self.max_value, self.max_value)
        
        forces_new = self._compute_forces(self.matrices)
        self.velocities += 0.5 * forces_new * dt
        self.velocities *= (1.0 - self.damping)  # Apply damping again

    def poke(self, strength: float = 5.0) -> None:
        """
        Apply an explosive perturbation to the D0-branes.
        Simulates injecting energy into the system.
        Activates after-burn effect for organic settling.
        """
        if self.velocities is None:
            return
        
        # Add random velocities (explosion)
        for i in range(3):
            V = np.random.randn(self.n_size, self.n_size) + 1j * np.random.randn(self.n_size, self.n_size)
            self.velocities[i] += (V + V.conj().T) * strength
        
        # Activate after-burn effect
        self.afterburn_timer = 2.0  # 2 seconds of high damping
        self.damping = self.afterburn_damping

    def get_state(self) -> MatrixState:
        if self.matrices is None:
             raise RuntimeError("Physics engine not initialized")
        
        # Extract positions using eigenvalues of each matrix
        # This gives physically meaningful D0-brane positions
        # Eigenvalues of Hermitian matrices are real
        
        try:
            x_eig = np.real(np.linalg.eigvalsh(self.matrices[0]))
            y_eig = np.real(np.linalg.eigvalsh(self.matrices[1]))
            z_eig = np.real(np.linalg.eigvalsh(self.matrices[2]))
        except np.linalg.LinAlgError:
            # Fallback to diagonal if eigenvalue fails
            x_eig = np.real(np.diagonal(self.matrices[0]))
            y_eig = np.real(np.diagonal(self.matrices[1]))
            z_eig = np.real(np.diagonal(self.matrices[2]))
        
        # Sort eigenvalues for consistent pairing
        x_eig = np.sort(x_eig)
        y_eig = np.sort(y_eig)
        z_eig = np.sort(z_eig)
        
        points = np.column_stack((x_eig, y_eig, z_eig))
        
        # Compute connection strengths from OFF-DIAGONAL elements
        # Large off-diagonal elements mean branes are "connected" by strings
        # Sum |X_ij|^2 over all 3 matrices
        connection_strengths = np.zeros((self.n_size, self.n_size), dtype=np.float64)
        for k in range(3):
            connection_strengths += np.abs(self.matrices[k]) ** 2
        
        # Zero out diagonal (self-connections don't count)
        np.fill_diagonal(connection_strengths, 0)
        
        # Normalize to [0, 1]
        max_strength = np.max(connection_strengths)
        if max_strength > 0:
            connection_strengths /= max_strength
        
        return MatrixState(
            matrices=[m.copy() for m in self.matrices],
            eigenvalues=points,
            connection_strengths=connection_strengths
        )
