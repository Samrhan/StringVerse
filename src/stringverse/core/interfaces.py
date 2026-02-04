from typing import Protocol, Any, runtime_checkable
from stringverse.core.models import SimulationConfig

@runtime_checkable
class PhysicsEngine(Protocol):
    """Contract for any physics engine module."""
    
    def initialize(self, config: SimulationConfig) -> None:
        """Initialize the physics simulation with the given configuration."""
        ...

    def step(self, dt: float) -> None:
        """Advance the simulation by one time step."""
        ...
        
    def get_state(self) -> Any:
        """Return the current state for rendering."""
        ...

@runtime_checkable
class Renderer(Protocol):
    """Contract for the visualization system."""
    
    def setup_scene(self) -> None:
        """Initialize cameras, lights, and VTK actors."""
        ...

    def update_actors(self, state: Any) -> None:
        """Update vertex buffers (VBO) without recreating objects."""
        ...

    def render_frame(self) -> None:
        """Trigger a frame render."""
        ...
