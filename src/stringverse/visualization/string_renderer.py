"""
Multi-String Renderer with dynamic actor pool.
Supports visualization of multiple string loops after splitting.
"""
import numpy as np
import pyvista as pv
from typing import List, Optional
from stringverse.core.interfaces import Renderer
from stringverse.core.models import StringState, StringLoop

# Color palette for different string loops (after splits)
LOOP_COLORS = [
    "plasma",      # Original string
    "viridis",     # First daughter
    "inferno",     # Second daughter
    "magma",       # Third
    "cividis",     # Fourth
    "twilight",    # Fifth
    "cool",        # Sixth
    "spring",      # Seventh
]


class StringRenderer(Renderer):
    """
    Multi-String Renderer with dynamic actor pool.
    
    Features:
    - Pool of pre-allocated actors (avoids add/remove overhead)
    - Different colors for each daughter string after splitting
    - Velocity-based brightness within each loop
    """

    MAX_LOOPS = 8  # Maximum renderable loops
    SPLINE_POINTS = 200  # Points per spline (reduced for multi-loop perf)

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.interactive = interactive
        self.active_loops = 0
        
        # Actor pool - pre-allocated meshes
        self.loop_meshes: List[Optional[pv.PolyData]] = [None] * self.MAX_LOOPS

    def setup_scene(self) -> None:
        """Initialize cameras, lights, and actor pool."""
        self.plotter.set_background("black")
        
        # Dramatic lighting
        self.plotter.add_light(pv.Light(position=(15, 15, 15), color='white', intensity=0.8))
        self.plotter.add_light(pv.Light(position=(-10, -10, 10), color='cyan', intensity=0.4))
        self.plotter.add_light(pv.Light(position=(0, 0, -15), color='magenta', intensity=0.3))

        # Initialize actor pool with dummy geometry
        for i in range(self.MAX_LOOPS):
            theta = np.linspace(0, 2 * np.pi, 50)
            dummy_points = np.column_stack([
                np.cos(theta), np.sin(theta), np.zeros_like(theta)
            ])
            dummy_points = np.vstack([dummy_points, dummy_points[0]])
            
            mesh = pv.Spline(dummy_points, self.SPLINE_POINTS)
            self.loop_meshes[i] = mesh
            
            # Add mesh but make it invisible initially (except first)
            self.plotter.add_mesh(
                mesh,
                scalars=np.zeros(self.SPLINE_POINTS),
                cmap=LOOP_COLORS[i % len(LOOP_COLORS)],
                line_width=6,
                render_lines_as_tubes=True,
                show_scalar_bar=False,
                lighting=True,
                opacity=1.0 if i == 0 else 0.0,  # Only first visible
                name=f"string_loop_{i}"
            )
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'
        
        # HUD
        self.plotter.add_text(
            "Nambu-Goto String [SPLITTING ENABLED]\n"
            "───────────────────────────────────\n"
            "Color = Velocity (bright = relativistic)\n"
            "Watch for self-intersections → SPLIT!\n"
            "Slider = String Tension\n"
            "[1/2/3] Switch module  [Q] Quit",
            position='upper_left',
            font_size=9,
            color='white',
            name='hud_text'
        )
        
        # Loop counter HUD
        self.plotter.add_text(
            "Loops: 1",
            position='upper_right',
            font_size=12,
            color='cyan',
            name='loop_counter'
        )

    def _render_loop(self, loop: StringLoop, actor_index: int) -> None:
        """Update a single loop's actor."""
        if actor_index >= self.MAX_LOOPS:
            return
        
        positions = loop.positions
        velocities = loop.velocities
        
        # Close the loop
        points_closed = np.vstack([positions, positions[0]])
        
        # Create spline
        new_spline = pv.Spline(points_closed, self.SPLINE_POINTS)
        
        # Velocity-based coloring
        vel_mag = np.linalg.norm(velocities, axis=1)
        max_vel = max(np.max(vel_mag), 1.0)
        vel_normalized = vel_mag / max_vel
        vel_normalized = np.append(vel_normalized, vel_normalized[0])
        
        # Interpolate to spline
        old_idx = np.linspace(0, 1, len(points_closed))
        new_idx = np.linspace(0, 1, self.SPLINE_POINTS)
        scalars = np.interp(new_idx, old_idx, vel_normalized)
        
        # Update actor
        cmap = LOOP_COLORS[loop.color_id % len(LOOP_COLORS)]
        
        self.plotter.add_mesh(
            new_spline,
            scalars=scalars,
            cmap=cmap,
            line_width=6,
            render_lines_as_tubes=True,
            show_scalar_bar=False,
            lighting=True,
            clim=[0, 1],
            opacity=1.0,
            name=f"string_loop_{actor_index}",
            reset_camera=False
        )

    def _hide_loop(self, actor_index: int) -> None:
        """Hide an unused loop actor."""
        if actor_index >= self.MAX_LOOPS:
            return
        
        # Create tiny invisible mesh
        tiny = pv.Sphere(radius=0.001, center=(1000, 1000, 1000))
        self.plotter.add_mesh(
            tiny,
            opacity=0.0,
            name=f"string_loop_{actor_index}",
            reset_camera=False
        )

    def update_actors(self, state: StringState) -> None:
        """Update all visible string loops."""
        # Multi-loop rendering
        if state.loops is not None:
            num_loops = len(state.loops)
            
            # Render active loops
            for i, loop in enumerate(state.loops):
                if i < self.MAX_LOOPS:
                    self._render_loop(loop, i)
            
            # Hide unused actors
            for i in range(num_loops, self.MAX_LOOPS):
                self._hide_loop(i)
            
            # Update counter HUD
            if num_loops != self.active_loops:
                self.active_loops = num_loops
                self.plotter.add_text(
                    f"Loops: {num_loops}",
                    position='upper_right',
                    font_size=12,
                    color='cyan' if num_loops == 1 else 'yellow',
                    name='loop_counter'
                )
        else:
            # Legacy single-loop fallback
            legacy_loop = StringLoop(
                positions=state.positions,
                velocities=state.velocities,
                color_id=0
            )
            self._render_loop(legacy_loop, 0)
            for i in range(1, self.MAX_LOOPS):
                self._hide_loop(i)

    def render_frame(self) -> None:
        """Trigger a frame render."""
        self.plotter.render()

    def render_frame(self) -> None:
        """Trigger a frame render."""
        # For interactive mode, we usually rely on the loop calling update(), 
        # but explicitly calling render is good.
        self.plotter.render()
