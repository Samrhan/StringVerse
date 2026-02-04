import numpy as np
import pyvista as pv
from stringverse.core.interfaces import Renderer
from stringverse.core.models import MatrixState

class MatrixRenderer(Renderer):
    """
    Visualization module for the BFSS Matrix Model.
    Renders D0-branes as glowing spheres with connection lines showing interactions.
    """

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.point_cloud: pv.PolyData | None = None
        self.glyphs: pv.PolyData | None = None
        self.lines: pv.PolyData | None = None
        self.interactive = interactive
        self.connection_threshold = 3.0  # Distance threshold for drawing connections

    def setup_scene(self) -> None:
        self.plotter.set_background("black")
        
        # Dramatic lighting
        self.plotter.add_light(pv.Light(position=(20, 20, 20), color='white', intensity=0.7))
        self.plotter.add_light(pv.Light(position=(-15, 10, -10), color='cyan', intensity=0.5))
        self.plotter.add_light(pv.Light(position=(0, -20, 10), color='orange', intensity=0.3))
        
        # Initialize with dummy data
        points = np.random.randn(10, 3) * 2
        self.point_cloud = pv.PolyData(points)
        
        # Create glowing spheres
        sphere = pv.Sphere(radius=0.25)
        self.glyphs = self.point_cloud.glyph(scale=False, orient=False, geom=sphere)
        
        self.plotter.add_mesh(
            self.glyphs,
            color="cyan",
            specular=1.0,
            specular_power=20,
            ambient=0.3,
            smooth_shading=True,
            name="brane_actor"
        )
        
        # Connection lines will be added dynamically in update_actors
        self.lines = None
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'

    def _create_connections(self, points: np.ndarray) -> pv.PolyData:
        """Create line connections between nearby D0-branes."""
        n = len(points)
        lines = []
        line_scalars = []
        
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(points[i] - points[j])
                if dist < self.connection_threshold:
                    lines.append([2, i, j])  # VTK line format
                    line_scalars.append(1.0 - dist / self.connection_threshold)
        
        if lines:
            cells = np.array(lines).flatten()
            mesh = pv.PolyData(points, lines=cells)
            mesh.cell_data["intensity"] = np.array(line_scalars)
            return mesh
        else:
            return pv.PolyData()

    def update_actors(self, state: MatrixState) -> None:
        if self.point_cloud is None:
            return

        points = state.eigenvalues
        self.point_cloud.points = points
        
        # Create glyphs with size based on local density
        sphere = pv.Sphere(radius=0.25)
        new_glyphs = self.point_cloud.glyph(scale=False, orient=False, geom=sphere)
        
        # Color by position (distance from origin) for visual interest
        distances = np.linalg.norm(points, axis=1)
        glyph_colors = np.repeat(distances, sphere.n_points)
        
        self.plotter.add_mesh(
            new_glyphs,
            scalars=glyph_colors,
            cmap="cool",  # Cyan to magenta
            show_scalar_bar=False,
            specular=1.0,
            specular_power=20,
            ambient=0.3,
            smooth_shading=True,
            name="brane_actor",
            reset_camera=False
        )
        
        # Update connection lines
        connections = self._create_connections(points)
        if connections.n_points > 0:
            self.plotter.add_mesh(
                connections,
                scalars="intensity" if "intensity" in connections.cell_data else None,
                cmap="Blues",
                opacity=0.4,
                line_width=2,
                show_scalar_bar=False,
                name="connection_actor",
                reset_camera=False
            )

    def render_frame(self) -> None:
        self.plotter.render()
