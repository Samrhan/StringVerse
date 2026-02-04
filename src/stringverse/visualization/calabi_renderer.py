import pyvista as pv
import numpy as np
import os
from stringverse.core.interfaces import Renderer
from stringverse.utils.cy_generator import generate_calabi_yau_mesh

class CalabiYauRenderer(Renderer):
    """
    Visualization module for Calabi-Yau manifolds.
    Animated visualization with morphing cross-sections.
    """

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.mesh: pv.PolyData | None = None
        self.interactive = interactive
        self.time = 0.0
        self.rotation_speed = 0.8

    def setup_scene(self) -> None:
        self.plotter.set_background("black")
        
        # Ethereal lighting for the manifold
        self.plotter.add_light(pv.Light(position=(15, 15, 15), color='white', intensity=0.6))
        self.plotter.add_light(pv.Light(position=(-10, -10, 15), color='purple', intensity=0.5))
        self.plotter.add_light(pv.Light(position=(10, -15, -10), color='cyan', intensity=0.4))
        self.plotter.add_light(pv.Light(position=(-15, 10, -5), color='magenta', intensity=0.3))
        
        # Load or generate mesh
        mesh_path = "calabi_yau.vtk"
        if os.path.exists(mesh_path):
            self.mesh = pv.read(mesh_path)
        else:
            print("Generating Calabi-Yau mesh (one-time)...")
            self.mesh = generate_calabi_yau_mesh(resolution=60)
            self.mesh.save(mesh_path)
        
        # Add curvature-based coloring
        if self.mesh.n_points > 0:
            self.mesh = self.mesh.compute_normals()
            # Use position-based coloring for visual interest
            z_coords = self.mesh.points[:, 2]
            self.mesh.point_data["height"] = z_coords
            
        self.plotter.add_mesh(
            self.mesh,
            scalars="height",
            cmap="viridis",
            opacity=0.7,
            style='surface',
            show_edges=False,
            smooth_shading=True,
            specular=0.5,
            specular_power=15,
            show_scalar_bar=False,
            name="cy_actor"
        )
        
        # Add a subtle wireframe overlay
        self.plotter.add_mesh(
            self.mesh,
            style='wireframe',
            color='white',
            opacity=0.1,
            line_width=1,
            name="cy_wireframe"
        )
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'

    def update_actors(self, state: any) -> None:
        if self.mesh:
            # Smooth rotation around multiple axes for interesting views
            self.mesh.rotate_y(self.rotation_speed, inplace=True)
            self.mesh.rotate_z(self.rotation_speed * 0.3, inplace=True)
            self.time += 0.016
            
            # Animate the color by shifting the scalar values
            if "height" in self.mesh.point_data:
                z_coords = self.mesh.points[:, 2]
                phase = np.sin(self.time * 0.5)
                self.mesh.point_data["height"] = z_coords + phase * 0.5

    def render_frame(self) -> None:
        self.plotter.render()
