import numpy as np
import pyvista as pv
from stringverse.core.interfaces import Renderer
from stringverse.core.models import StringState

class StringRenderer(Renderer):
    """
    Visualization module for the relativistic string using PyVista.
    Renders as a glowing tube with velocity-based coloring.
    """

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.string_mesh: pv.PolyData | None = None
        self.tube_mesh: pv.PolyData | None = None
        self.interactive = interactive
        self.trail_points: list = []  # For motion trail effect
        self.max_trail_length = 5

    def setup_scene(self) -> None:
        """Initialize cameras, lights, and VTK actors."""
        self.plotter.set_background("black")
        
        # Dramatic lighting for the string
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
        
        # Create initial spline and tube
        self.string_mesh = pv.Spline(points, 500)
        self.tube_mesh = self.string_mesh.tube(radius=0.15, n_sides=12)
        
        # Add glowing tube
        self.plotter.add_mesh(
            self.tube_mesh, 
            scalars=np.zeros(self.tube_mesh.n_points), 
            cmap="plasma",  # Hot colors: purple -> orange -> yellow
            render_points_as_spheres=False,
            show_scalar_bar=False,
            lighting=True,
            smooth_shading=True,
            specular=0.8,
            specular_power=30,
            ambient=0.2,
            name="string_actor"
        )
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'

    def update_actors(self, state: StringState) -> None:
        """
        Update the string mesh with velocity-colored tube.
        """
        if self.string_mesh is None:
            return

        points = state.positions
        velocities = state.velocities
        
        # Close the loop
        points_closed = np.vstack([points, points[0]])
        
        # Create new spline
        new_spline = pv.Spline(points_closed, 500)
        
        # Create tube from spline
        new_tube = new_spline.tube(radius=0.15, n_sides=12)
        
        # Calculate velocity magnitude for coloring
        vel_mag = np.linalg.norm(velocities, axis=1)
        vel_mag = np.append(vel_mag, vel_mag[0])
        
        # Also calculate local curvature for additional visual interest
        # Curvature ~ |d²r/ds²| approximated by second differences
        d2r = np.roll(points, -1, axis=0) - 2 * points + np.roll(points, 1, axis=0)
        curvature = np.linalg.norm(d2r, axis=1)
        curvature = np.append(curvature, curvature[0])
        
        # Combine velocity and curvature for coloring
        combined = vel_mag + 0.5 * curvature
        
        # Interpolate to spline points
        old_indices = np.linspace(0, 1, len(points_closed))
        spline_indices = np.linspace(0, 1, new_spline.n_points)
        interpolated_scalars = np.interp(spline_indices, old_indices, combined)
        
        # Map spline scalars to tube surface
        # Approximate by nearest neighbor from spline to tube points
        tube_scalars = np.zeros(new_tube.n_points)
        for i in range(new_tube.n_points):
            # Find closest spline point
            dists = np.linalg.norm(new_spline.points - new_tube.points[i], axis=1)
            tube_scalars[i] = interpolated_scalars[np.argmin(dists)]
        
        # Update mesh
        self.plotter.add_mesh(
            new_tube,
            scalars=tube_scalars,
            cmap="plasma",
            show_scalar_bar=False,
            lighting=True,
            smooth_shading=True,
            specular=0.8,
            specular_power=30,
            ambient=0.2,
            name="string_actor",
            reset_camera=False
        )

    def render_frame(self) -> None:
        """Trigger a frame render."""
        # For interactive mode, we usually rely on the loop calling update(), 
        # but explicitly calling render is good.
        self.plotter.render()
