import numpy as np
import pyvista as pv
from stringverse.core.interfaces import Renderer
from stringverse.core.models import MatrixState

class MatrixRenderer(Renderer):
    """
    Visualization module for the BFSS Matrix Model.
    Renders D0-branes as spheres with connection lines showing EMERGENT GEOMETRY.
    Connection strength comes from off-diagonal matrix elements (open strings between branes).
    """

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.point_cloud: pv.PolyData | None = None
        self.glyphs: pv.PolyData | None = None
        self.lines: pv.PolyData | None = None
        self.interactive = interactive
        self.connection_threshold = 0.1  # Minimum strength to draw connection

    def setup_scene(self) -> None:
        self.plotter.set_background("black")
        
        # Dramatic lighting
        self.plotter.add_light(pv.Light(position=(20, 20, 20), color='white', intensity=0.7))
        self.plotter.add_light(pv.Light(position=(-15, 10, -10), color='cyan', intensity=0.5))
        self.plotter.add_light(pv.Light(position=(0, -20, 10), color='orange', intensity=0.3))
        
        # Initialize with dummy data
        points = np.random.randn(10, 3) * 2
        self.point_cloud = pv.PolyData(points)
        
        # Create spheres (small - branes are point-like)
        sphere = pv.Sphere(radius=0.2)
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
        
        self.lines = None
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'

    def _create_connections_from_matrix(self, points: np.ndarray, 
                                         strengths: np.ndarray) -> pv.PolyData:
        """
        Create line connections based on off-diagonal matrix elements.
        This shows the EMERGENT GEOMETRY from non-commutative matrices.
        Strong connections = open strings stretched between D0-branes.
        """
        n = len(points)
        lines = []
        line_scalars = []
        
        for i in range(n):
            for j in range(i + 1, n):
                strength = strengths[i, j]
                if strength > self.connection_threshold:
                    lines.append([2, i, j])
                    line_scalars.append(strength)
        
        if lines:
            cells = np.array(lines).flatten()
            mesh = pv.PolyData(points, lines=cells)
            mesh.cell_data["strength"] = np.array(line_scalars)
            return mesh
        else:
            return pv.PolyData()

    def update_actors(self, state: MatrixState) -> None:
        if self.point_cloud is None:
            return

        points = state.eigenvalues
        self.point_cloud.points = points
        
        # Create spheres
        sphere = pv.Sphere(radius=0.2)
        new_glyphs = self.point_cloud.glyph(scale=False, orient=False, geom=sphere)
        
        # Color by distance from center of mass (shows clustering)
        center = np.mean(points, axis=0)
        distances = np.linalg.norm(points - center, axis=1)
        glyph_colors = np.repeat(distances, sphere.n_points)
        
        self.plotter.add_mesh(
            new_glyphs,
            scalars=glyph_colors,
            cmap="cool",
            show_scalar_bar=False,
            specular=1.0,
            specular_power=20,
            ambient=0.3,
            smooth_shading=True,
            name="brane_actor",
            reset_camera=False
        )
        
        # Draw connections based on off-diagonal matrix elements
        if state.connection_strengths is not None:
            connections = self._create_connections_from_matrix(points, state.connection_strengths)
            if connections.n_points > 0:
                self.plotter.add_mesh(
                    connections,
                    scalars="strength",
                    cmap="hot",  # Strong connections = bright
                    opacity=0.6,
                    line_width=3,
                    show_scalar_bar=False,
                    name="connection_actor",
                    reset_camera=False
                )

    def render_frame(self) -> None:
        self.plotter.render()
