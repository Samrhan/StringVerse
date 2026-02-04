import numpy as np
import pyvista as pv
from stringverse.core.interfaces import Renderer
from stringverse.core.models import StringState

class StringRenderer(Renderer):
    """
    Visualization module for the relativistic string using PyVista.
    Optimized: Uses thick lines instead of expensive tube geometry.
    Color shows velocity magnitude (relativistic = bright).
    """

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.string_mesh: pv.PolyData | None = None
        self.interactive = interactive
        self.n_spline_points = 300  # Reduced for performance

    def setup_scene(self) -> None:
        """Initialize cameras, lights, and VTK actors."""
        self.plotter.set_background("black")
        
        # Dramatic lighting
        self.plotter.add_light(pv.Light(position=(15, 15, 15), color='white', intensity=0.8))
        self.plotter.add_light(pv.Light(position=(-10, -10, 10), color='cyan', intensity=0.4))
        self.plotter.add_light(pv.Light(position=(0, 0, -15), color='magenta', intensity=0.3))

        # Initialize with a dummy circle
        theta = np.linspace(0, 2 * np.pi, 100)
        x = 5 * np.cos(theta)
        y = 5 * np.sin(theta)
        z = np.zeros_like(x)
        points = np.column_stack((x, y, z))
        points = np.vstack([points, points[0]])
        
        # Create initial spline (no tube - just thick line)
        self.string_mesh = pv.Spline(points, self.n_spline_points)
        
        # Use thick line rendering - MUCH faster than tube
        self.plotter.add_mesh(
            self.string_mesh, 
            scalars=np.zeros(self.n_spline_points), 
            cmap="plasma",
            line_width=8,  # Thick line for visibility
            render_lines_as_tubes=True,  # VTK renders as tubes without geometry cost
            show_scalar_bar=False,
            lighting=True,
            name="string_actor"
        )
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'

    def update_actors(self, state: StringState) -> None:
        """
        Update the string mesh efficiently.
        Only regenerates spline (fast), colors by velocity magnitude.
        Bright = relativistic speeds approaching c.
        """
        if self.string_mesh is None:
            return

        points = state.positions
        velocities = state.velocities
        
        # Close the loop
        points_closed = np.vstack([points, points[0]])
        
        # Create new spline (fast - just interpolation)
        new_spline = pv.Spline(points_closed, self.n_spline_points)
        
        # Calculate velocity magnitude for coloring
        # Normalize to [0, 1] where 1 = "relativistic" (arbitrary threshold)
        vel_mag = np.linalg.norm(velocities, axis=1)
        max_vel = max(np.max(vel_mag), 1.0)  # Prevent division by zero
        vel_normalized = vel_mag / max_vel
        vel_normalized = np.append(vel_normalized, vel_normalized[0])
        
        # Interpolate to spline points
        old_indices = np.linspace(0, 1, len(points_closed))
        spline_indices = np.linspace(0, 1, self.n_spline_points)
        interpolated_scalars = np.interp(spline_indices, old_indices, vel_normalized)
        
        # Update mesh in-place when possible, otherwise replace
        self.plotter.add_mesh(
            new_spline,
            scalars=interpolated_scalars,
            cmap="plasma",
            line_width=8,
            render_lines_as_tubes=True,
            show_scalar_bar=False,
            lighting=True,
            clim=[0, 1],  # Fixed color scale
            name="string_actor",
            reset_camera=False
        )

    def render_frame(self) -> None:
        """Trigger a frame render."""
        # For interactive mode, we usually rely on the loop calling update(), 
        # but explicitly calling render is good.
        self.plotter.render()
