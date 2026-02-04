import pyvista as pv
import numpy as np
import os
from stringverse.core.interfaces import Renderer
from stringverse.utils.cy_generator import generate_calabi_yau_mesh

class CalabiYauRenderer(Renderer):
    """
    Visualization module for Calabi-Yau manifolds.
    Features an INTERACTIVE SLICER to explore the extra dimensions.
    Moving the slice plane reveals how the internal geometry changes.
    """

    def __init__(self, interactive: bool = True) -> None:
        self.plotter = pv.Plotter(off_screen=not interactive)
        self.mesh: pv.PolyData | None = None
        self.original_mesh: pv.PolyData | None = None
        self.interactive = interactive
        self.time = 0.0
        self.rotation_speed = 0.3  # Slower for better observation
        self.slice_position = 0.0  # Current slice position
        self.auto_slice = True  # Animate slice automatically

    def setup_scene(self) -> None:
        self.plotter.set_background("black")
        
        # Ethereal lighting
        self.plotter.add_light(pv.Light(position=(15, 15, 15), color='white', intensity=0.6))
        self.plotter.add_light(pv.Light(position=(-10, -10, 15), color='purple', intensity=0.5))
        self.plotter.add_light(pv.Light(position=(10, -15, -10), color='cyan', intensity=0.4))
        self.plotter.add_light(pv.Light(position=(-15, 10, -5), color='magenta', intensity=0.3))
        
        # Load or generate mesh
        mesh_path = "calabi_yau.vtk"
        if os.path.exists(mesh_path):
            self.original_mesh = pv.read(mesh_path)
        else:
            print("Generating Calabi-Yau mesh (one-time)...")
            self.original_mesh = generate_calabi_yau_mesh(resolution=60)
            self.original_mesh.save(mesh_path)
        
        self.mesh = self.original_mesh.copy()
        
        # Compute mesh bounds for slicing
        self.bounds = self.mesh.bounds
        self.slice_range = (self.bounds[4], self.bounds[5])  # Z range
        
        # Add curvature-based coloring
        if self.mesh.n_points > 0:
            self.mesh = self.mesh.compute_normals()
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
        
        # Add slice plane indicator
        self._update_slice_plane()
        
        # Add interactive slider for slice position
        if self.interactive:
            def update_slice(value):
                self.slice_position = value
                self.auto_slice = False  # Disable auto when user interacts
                
            self.plotter.add_slider_widget(
                update_slice,
                [self.slice_range[0], self.slice_range[1]],
                value=0.0,
                title="Slice Z (Extra Dimension)",
                pointa=(0.6, 0.1),
                pointb=(0.95, 0.1),
                style="modern"
            )
        
        self.plotter.show_axes()
        self.plotter.camera_position = 'iso'

    def _update_slice_plane(self) -> None:
        """Update the clipped mesh based on current slice position."""
        if self.original_mesh is None:
            return
            
        # Clip mesh to show cross-section
        # Use a thin slab around the slice position
        slab_thickness = 0.5
        z_min = self.slice_position - slab_thickness
        z_max = self.slice_position + slab_thickness
        
        # Clip to slab
        try:
            clipped = self.original_mesh.clip(normal='z', origin=(0, 0, z_min), invert=False)
            clipped = clipped.clip(normal='z', origin=(0, 0, z_max), invert=True)
            
            if clipped.n_points > 0:
                clipped = clipped.compute_normals()
                clipped.point_data["height"] = clipped.points[:, 2]
                
                self.plotter.add_mesh(
                    clipped,
                    scalars="height",
                    cmap="plasma",  # Different colormap for slice
                    opacity=0.9,
                    style='surface',
                    show_edges=True,
                    edge_color='white',
                    smooth_shading=True,
                    specular=0.8,
                    specular_power=20,
                    show_scalar_bar=False,
                    name="cy_slice"
                )
        except Exception:
            pass  # Clipping can fail at boundaries

    def update_actors(self, state: any) -> None:
        if self.mesh:
            # Slow rotation
            self.mesh.rotate_y(self.rotation_speed, inplace=True)
            if self.original_mesh:
                self.original_mesh.rotate_y(self.rotation_speed, inplace=True)
            
            self.time += 0.016
            
            # Auto-animate slice position (oscillate through the manifold)
            if self.auto_slice:
                amplitude = (self.slice_range[1] - self.slice_range[0]) * 0.4
                center = (self.slice_range[0] + self.slice_range[1]) / 2
                self.slice_position = center + amplitude * np.sin(self.time * 0.5)
            
            # Update the slice visualization
            self._update_slice_plane()
            
            # Update main mesh coloring
            if "height" in self.mesh.point_data:
                z_coords = self.mesh.points[:, 2]
                phase = np.sin(self.time * 0.3)
                self.mesh.point_data["height"] = z_coords + phase * 0.3

    def render_frame(self) -> None:
        self.plotter.render()
