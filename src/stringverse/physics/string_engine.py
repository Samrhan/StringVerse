import numpy as np
import numpy.typing as npt
from stringverse.core.models import SimulationConfig, StringState
from stringverse.core.interfaces import PhysicsEngine

class RelativisticString(PhysicsEngine):
    """
    Simulates a relativistic closed string (Nambu-Goto) using a discretized model.
    In the conformal gauge, the equation of motion is the wave equation:
    (d^2 X / dt^2) - (d^2 X / d_sigma^2) = 0
    """

    def __init__(self) -> None:
        self.config: SimulationConfig | None = None
        self.positions: npt.NDArray[np.float64] | None = None
        self.velocities: npt.NDArray[np.float64] | None = None
        self.num_points: int = 0

    def initialize(self, config: SimulationConfig) -> None:
        """Initialize the string as a perturbed circle with traveling waves."""
        self.config = config
        self.num_points = config.resolution
        
        # Initialize positions: A circle in XY plane
        theta = np.linspace(0, 2 * np.pi, self.num_points, endpoint=False)
        radius = 5.0
        
        self.positions = np.zeros((self.num_points, 3), dtype=np.float64)
        self.positions[:, 0] = radius * np.cos(theta)
        self.positions[:, 1] = radius * np.sin(theta)
        
        # Perturb to create interesting 3D structure
        # Multiple modes for rich dynamics
        self.positions[:, 2] = 1.5 * np.sin(2 * theta) + 0.8 * np.cos(3 * theta) + 0.5 * np.sin(5 * theta)
        
        # Add radial "breathing" perturbation
        radial_perturb = 0.3 * np.sin(4 * theta)
        self.positions[:, 0] += radial_perturb * np.cos(theta)
        self.positions[:, 1] += radial_perturb * np.sin(theta)

        # Initialize velocities: Create TRAVELING waves (not standing waves)
        # For traveling wave: v = c * dX/dsigma (velocity proportional to gradient)
        self.velocities = np.zeros((self.num_points, 3), dtype=np.float64)
        
        # Traveling wave in Z: dz/dt = c * dz/dsigma
        # This creates waves that travel around the string
        dz_dsigma = np.roll(self.positions[:, 2], -1) - np.roll(self.positions[:, 2], 1)
        self.velocities[:, 2] = 3.0 * dz_dsigma * (self.num_points / (4 * np.pi))
        
        # Add some radial pulsation velocity
        self.velocities[:, 0] = 0.5 * np.cos(theta) * np.sin(3 * theta)
        self.velocities[:, 1] = 0.5 * np.sin(theta) * np.sin(3 * theta)

    def _compute_acceleration(self, x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """
        Compute acceleration (force) based on tension (Laplacian).
        a = T * d^2x / d_sigma^2
        """
        if self.config is None:
            return np.zeros_like(x)
            
        # Discrete Laplacian on a periodic grid
        # L(x) = x[i+1] - 2x[i] + x[i-1]
        laplacian = np.roll(x, -1, axis=0) - 2 * x + np.roll(x, 1, axis=0)
        
        # Tension effectively scales with N^2 if we consider physical length fixed
        # But for visual intuition, we can just use the coupling constant * Laplacian
        # Normalizing by (2pi/N)^2 would be physically accurate for fixed length.
        # Let's tune 'tension' via coupling_constant.
        # If coupling_constant is high, waves move faster.
        
        # Heuristic scaling to keep things visually reasonable regardless of resolution
        # For wave equation dx/dt = c, acceleration ~ c^2 * laplacian / dx^2
        # dx ~ 1/N. So factor ~ N^2.
        scale_factor = (self.num_points / (2 * np.pi)) ** 2
        
        return self.config.coupling_constant * scale_factor * laplacian

    def step(self, dt: float) -> None:
        """
        Symplectic integration (Velocity Verlet).
        """
        if self.positions is None or self.velocities is None:
            return

        # 1. Half-step velocity
        # v(t + 0.5dt) = v(t) + 0.5 * a(t) * dt
        acc_t = self._compute_acceleration(self.positions)
        self.velocities += 0.5 * acc_t * dt

        # 2. Full-step position
        # x(t + dt) = x(t) + v(t + 0.5dt) * dt
        self.positions += self.velocities * dt

        # 3. Recalculate acceleration at new position
        acc_t_plus_dt = self._compute_acceleration(self.positions)

        # 4. Finish velocity update
        # v(t + dt) = v(t + 0.5dt) + 0.5 * a(t + dt) * dt
        self.velocities += 0.5 * acc_t_plus_dt * dt

    def get_state(self) -> StringState:
        """Return the current immutable state."""
        if self.positions is None or self.velocities is None:
             raise RuntimeError("Physics engine not initialized")
             
        # Energy calculation
        # Mass of each segment m_i = 2pi / N (since length is 2pi and uniform density 1)
        # However, our acceleration scaling implies m_i = 2pi / N.
        # See derivation: F = m*a => C*(N/2pi)*Lap = m * C*(N/2pi)^2 * Lap => m = 2pi/N.
        
        mass_per_point = (2 * np.pi) / self.num_points
        
        # KE = 0.5 * m * v^2
        ke = 0.5 * mass_per_point * np.sum(np.linalg.norm(self.velocities, axis=1)**2)
        
        # PE = 0.5 * T * integral (dx/d_sigma)^2 d_sigma
        # discretized: 0.5 * T * sum ( (dx)^2 / d_sigma^2 ) * d_sigma
        # = 0.5 * T * sum (dx^2) / d_sigma
        # = 0.5 * T * (N/2pi) * sum(dx^2)
        # This matches the previous PE formula.
        
        diffs = np.roll(self.positions, -1, axis=0) - self.positions
        pe = 0.5 * self.config.coupling_constant * np.sum(np.linalg.norm(diffs, axis=1)**2) * (self.num_points / (2 * np.pi))

        return StringState(
            positions=self.positions.copy(),
            velocities=self.velocities.copy(),
            energy=ke + pe
        )
