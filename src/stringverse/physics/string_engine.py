"""
Multi-String Relativistic String Engine with Topological Changes.

Implements the Nambu-Goto action with:
- Multiple independent string loops
- Self-intersection detection (vectorized cdist)
- String splitting (topology change)
- Dynamic resampling for numerical stability
"""
import numpy as np
import numpy.typing as npt
from typing import List, Optional, Tuple
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from stringverse.core.models import SimulationConfig, StringState, StringLoop
from stringverse.core.interfaces import PhysicsEngine


class RelativisticString(PhysicsEngine):
    """
    Multi-String Relativistic String Simulator.
    
    Features:
    - Multiple closed string loops
    - Self-intersection detection
    - String SPLITTING when loops cross themselves
    - Automatic resampling after topological changes
    """

    # Configuration
    MIN_LOOP_POINTS = 20  # Minimum points per loop (below = annihilate)
    MAX_LOOPS = 8  # Maximum simultaneous loops
    INTERSECTION_THRESHOLD = 0.8  # Distance threshold for collision
    NEIGHBOR_MASK_SIZE = 5  # Ignore this many neighbors in collision check
    TARGET_POINT_DENSITY = 0.5  # Target spacing between points

    def __init__(self) -> None:
        self.config: SimulationConfig | None = None
        self.loops: List[StringLoop] = []
        self.next_color_id: int = 0
        self.total_splits: int = 0

    def initialize(self, config: SimulationConfig) -> None:
        """Initialize with a single perturbed string loop."""
        self.config = config
        self.loops = []
        self.next_color_id = 0
        self.total_splits = 0
        
        # Create initial loop
        initial_loop = self._create_initial_loop(config.resolution)
        self.loops.append(initial_loop)

    def _create_initial_loop(self, num_points: int) -> StringLoop:
        """Create a perturbed circular string with traveling waves."""
        theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        radius = 5.0
        
        positions = np.zeros((num_points, 3), dtype=np.float64)
        positions[:, 0] = radius * np.cos(theta)
        positions[:, 1] = radius * np.sin(theta)
        
        # Figure-8 like perturbation to encourage self-crossing
        # z = A * sin(2θ) creates two lobes that can overlap
        positions[:, 2] = 3.0 * np.sin(2 * theta) + 1.5 * np.cos(3 * theta)
        
        # Strong radial perturbation (pinches the loop)
        radial_perturb = 1.5 * np.cos(2 * theta)  # Mode-2 = figure-8
        positions[:, 0] += radial_perturb * np.cos(theta)
        positions[:, 1] += radial_perturb * np.sin(theta)

        # Traveling wave velocities to drive crossing
        velocities = np.zeros((num_points, 3), dtype=np.float64)
        velocities[:, 2] = 4.0 * np.cos(2 * theta)  # Phase shifted from position
        velocities[:, 0] = 1.0 * np.sin(3 * theta)
        velocities[:, 1] = 1.0 * np.cos(3 * theta)
        
        color_id = self.next_color_id
        self.next_color_id += 1
        
        return StringLoop(positions=positions, velocities=velocities, color_id=color_id)

    def _compute_acceleration(self, positions: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Compute wave equation acceleration for a single loop."""
        if self.config is None:
            return np.zeros_like(positions)
        
        n = len(positions)
        laplacian = np.roll(positions, -1, axis=0) - 2 * positions + np.roll(positions, 1, axis=0)
        scale_factor = (n / (2 * np.pi)) ** 2
        
        return self.config.coupling_constant * scale_factor * laplacian

    def _integrate_loop(self, loop: StringLoop, dt: float) -> None:
        """Velocity Verlet integration for a single loop."""
        # Half-step velocity
        acc = self._compute_acceleration(loop.positions)
        loop.velocities += 0.5 * acc * dt
        
        # Full-step position
        loop.positions += loop.velocities * dt
        
        # Recalculate acceleration
        acc_new = self._compute_acceleration(loop.positions)
        
        # Finish velocity update
        loop.velocities += 0.5 * acc_new * dt

    def _check_self_intersection(self, loop: StringLoop) -> Optional[Tuple[int, int]]:
        """
        Detect self-intersection using vectorized distance matrix.
        Returns (i, j) indices of colliding points, or None.
        
        Key constraint: Both daughter loops must be viable (>= MIN_LOOP_POINTS).
        """
        n = len(loop.positions)
        if n < self.MIN_LOOP_POINTS * 2:
            return None  # Too small to split meaningfully
        
        # Compute full distance matrix (vectorized, fast)
        dists_sq = cdist(loop.positions, loop.positions, metric='sqeuclidean')
        
        threshold_sq = self.INTERSECTION_THRESHOLD ** 2
        
        # Minimum arc separation for viable daughters
        # Both daughters need MIN_LOOP_POINTS, so we need |j-i| >= MIN_LOOP_POINTS
        # AND n - |j-i| >= MIN_LOOP_POINTS
        min_separation = self.MIN_LOOP_POINTS
        
        # Create mask to ignore:
        # 1. Diagonal (self-distance)
        # 2. Nearby neighbors (within min_separation for viable splits)
        mask = np.ones((n, n), dtype=bool)
        
        for k in range(-min_separation, min_separation + 1):
            indices = np.arange(n)
            mask[indices, (indices + k) % n] = False
        
        # Also mask the "far side" that would make the other daughter too small
        for k in range(n - min_separation + 1, n):
            indices = np.arange(n)
            mask[indices, (indices + k) % n] = False
        
        # Find collisions
        collisions = (dists_sq < threshold_sq) & mask
        
        if not np.any(collisions):
            return None
        
        # Get the closest collision pair
        masked_dists = np.where(collisions, dists_sq, np.inf)
        min_idx = np.unravel_index(np.argmin(masked_dists), masked_dists.shape)
        
        i, j = min_idx
        if i > j:
            i, j = j, i  # Ensure i < j
        
        return (i, j)

    def _perform_split(self, loop: StringLoop, i: int, j: int) -> Tuple[Optional[StringLoop], Optional[StringLoop]]:
        """
        Split a loop at intersection points i and j.
        Returns two new daughter loops (or None if too small).
        """
        n = len(loop.positions)
        
        # Daughter 1: points from i to j (exclusive)
        if j > i:
            pos1 = loop.positions[i:j+1].copy()
            vel1 = loop.velocities[i:j+1].copy()
        else:
            pos1 = np.concatenate([loop.positions[i:], loop.positions[:j+1]])
            vel1 = np.concatenate([loop.velocities[i:], loop.velocities[:j+1]])
        
        # Daughter 2: points from j to i (wrapping around)
        pos2 = np.concatenate([loop.positions[j:], loop.positions[:i+1]])
        vel2 = np.concatenate([loop.velocities[j:], loop.velocities[:i+1]])
        
        # Check minimum size
        loop1 = None
        loop2 = None
        
        if len(pos1) >= self.MIN_LOOP_POINTS:
            # Resample to uniform density
            pos1, vel1 = self._resample_loop(pos1, vel1)
            loop1 = StringLoop(positions=pos1, velocities=vel1, color_id=self.next_color_id)
            self.next_color_id += 1
        
        if len(pos2) >= self.MIN_LOOP_POINTS:
            pos2, vel2 = self._resample_loop(pos2, vel2)
            loop2 = StringLoop(positions=pos2, velocities=vel2, color_id=self.next_color_id)
            self.next_color_id += 1
        
        return loop1, loop2

    def _resample_loop(self, positions: npt.NDArray, velocities: npt.NDArray, 
                       target_points: Optional[int] = None) -> Tuple[npt.NDArray, npt.NDArray]:
        """
        Resample a loop to have uniform point density.
        Critical for numerical stability after splitting!
        """
        n = len(positions)
        
        # Calculate arc length
        diffs = np.diff(positions, axis=0, append=positions[:1])
        segment_lengths = np.linalg.norm(diffs, axis=1)
        total_length = np.sum(segment_lengths)
        
        # Determine target number of points
        if target_points is None:
            target_points = max(self.MIN_LOOP_POINTS, 
                               int(total_length / self.TARGET_POINT_DENSITY))
            target_points = min(target_points, 150)  # Cap for performance
        
        if target_points == n:
            return positions, velocities
        
        # Cumulative arc length (normalized to [0, 1])
        cumulative = np.zeros(n + 1)
        cumulative[1:] = np.cumsum(segment_lengths)
        cumulative /= total_length
        
        # Close the loop for interpolation
        pos_closed = np.vstack([positions, positions[0:1]])
        vel_closed = np.vstack([velocities, velocities[0:1]])
        
        # Interpolate positions
        new_params = np.linspace(0, 1, target_points, endpoint=False)
        
        new_positions = np.zeros((target_points, 3))
        new_velocities = np.zeros((target_points, 3))
        
        for dim in range(3):
            interp_pos = interp1d(cumulative, pos_closed[:, dim], kind='cubic', fill_value='extrapolate')
            interp_vel = interp1d(cumulative, vel_closed[:, dim], kind='linear', fill_value='extrapolate')
            new_positions[:, dim] = interp_pos(new_params)
            new_velocities[:, dim] = interp_vel(new_params)
        
        return new_positions.astype(np.float64), new_velocities.astype(np.float64)

    def step(self, dt: float) -> None:
        """
        Main simulation step:
        1. Integrate each loop
        2. Check for self-intersections
        3. Perform splits if detected
        """
        if not self.loops or self.config is None:
            return
        
        new_loops: List[StringLoop] = []
        
        for loop in self.loops:
            # Physics integration
            self._integrate_loop(loop, dt)
            
            # Check for topology change (splitting)
            if (self.config.splitting_enabled and 
                len(self.loops) + len(new_loops) < self.MAX_LOOPS):
                
                collision = self._check_self_intersection(loop)
                
                if collision is not None:
                    i, j = collision
                    
                    # Probabilistic split (controlled by coupling)
                    if np.random.random() < self.config.splitting_probability:
                        daughter1, daughter2 = self._perform_split(loop, i, j)
                        
                        # Only commit split if at least one daughter is viable
                        if daughter1 is not None or daughter2 is not None:
                            if daughter1 is not None:
                                new_loops.append(daughter1)
                            if daughter2 is not None:
                                new_loops.append(daughter2)
                            
                            self.total_splits += 1
                            print(f"✂️ STRING SPLIT! Now {len(new_loops)} loop(s)")
                            continue  # Don't add original loop
            
            new_loops.append(loop)
        
        self.loops = new_loops

    def get_state(self) -> StringState:
        """Return state for rendering (multi-loop aware)."""
        if not self.loops:
            raise RuntimeError("Physics engine not initialized")
        
        # Primary loop for backward compatibility
        primary = self.loops[0]
        
        # Calculate total energy
        total_energy = 0.0
        for loop in self.loops:
            n = len(loop.positions)
            mass_per_point = (2 * np.pi) / n
            ke = 0.5 * mass_per_point * np.sum(np.linalg.norm(loop.velocities, axis=1)**2)
            
            diffs = np.roll(loop.positions, -1, axis=0) - loop.positions
            pe = 0.5 * self.config.coupling_constant * np.sum(np.linalg.norm(diffs, axis=1)**2) * (n / (2 * np.pi))
            
            total_energy += ke + pe
        
        # Create loop list for renderer
        loop_copies = [
            StringLoop(
                positions=loop.positions.copy(),
                velocities=loop.velocities.copy(),
                color_id=loop.color_id
            )
            for loop in self.loops
        ]
        
        return StringState(
            positions=primary.positions.copy(),
            velocities=primary.velocities.copy(),
            energy=total_energy,
            loops=loop_copies,
            num_loops=len(self.loops)
        )
