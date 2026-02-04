import numpy as np
import pyvista as pv
from skimage import measure

def generate_calabi_yau_mesh(resolution: int = 60) -> pv.PolyData:
    """
    Generates a 3D mesh representing a slice of a Calabi-Yau manifold.
    Uses a projection of the Fermat quintic: z1^5 + z2^5 + z3^5 = 0
    with a more physically motivated parameterization.
    """
    
    # Define grid with higher resolution for smoother surface
    extent = 2.5
    x = np.linspace(-extent, extent, resolution)
    y = np.linspace(-extent, extent, resolution)
    z = np.linspace(-extent, extent, resolution)
    X, Y, Z = np.meshgrid(x, y, z)
    
    # Parameterize complex coordinates as projections
    # Using a Hopf-like fibration mixing
    r = np.sqrt(X**2 + Y**2 + Z**2 + 0.1)  # Regularization
    
    z1 = (X + 1j*Y) / np.sqrt(1 + r)
    z2 = (Y + 1j*Z) / np.sqrt(1 + r)  
    z3 = (Z + 1j*X) / np.sqrt(1 + r)
    
    # Fermat quintic: z1^5 + z2^5 + z3^5
    quintic = z1**5 + z2**5 + z3**5
    
    # Use real and imaginary parts for the isosurface
    # This creates the characteristic "folded" Calabi-Yau structure
    scalar_field = np.abs(quintic) - 0.5
    
    # Also add structure from the phase
    phase_field = np.cos(5 * np.angle(quintic))
    
    # Combine for richer geometry
    combined_field = scalar_field + 0.3 * phase_field
    
    try:
        verts, faces, normals, values = measure.marching_cubes(combined_field, level=0.0)
        
        # Scale vertices back to coordinate space
        dx = x[1] - x[0]
        dy = y[1] - y[0]
        dz = z[1] - z[0]
        
        real_verts = np.zeros_like(verts)
        real_verts[:, 0] = x[0] + verts[:, 0] * dx
        real_verts[:, 1] = y[0] + verts[:, 1] * dy
        real_verts[:, 2] = z[0] + verts[:, 2] * dz
        
        # Create PyVista mesh
        faces_padded = np.hstack((np.full((faces.shape[0], 1), 3), faces))
        mesh = pv.PolyData(real_verts, faces_padded.flatten())
        
        # Smooth the mesh for better appearance
        mesh = mesh.smooth(n_iter=50, relaxation_factor=0.1)
        
        return mesh
        
    except ImportError:
        print("Scikit-image not installed. Returning sphere.")
        return pv.Sphere()
    except Exception as e:
        print(f"Error generating CY mesh: {e}. Returning sphere.")
        return pv.Sphere()

if __name__ == "__main__":
    mesh = generate_calabi_yau_mesh()
    mesh.save("calabi_yau.vtk")
    print("Saved calabi_yau.vtk")
