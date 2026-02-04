import sys
import time
import os
import pyvista as pv

from stringverse.core.models import SimulationConfig
from stringverse.core.interfaces import PhysicsEngine, Renderer

# Import Engines
from stringverse.physics.string_engine import RelativisticString
from stringverse.physics.matrix_engine import BFSSMatrixModel

# Import Renderers
from stringverse.visualization.string_renderer import StringRenderer
from stringverse.visualization.matrix_renderer import MatrixRenderer
from stringverse.visualization.calabi_renderer import CalabiYauRenderer

class MainController:
    def __init__(self, interactive: bool = True):
        self.config = SimulationConfig(
            time_step=0.05, 
            resolution=100,  # N=100 for emergent geometry (GPU) or 32 (CPU fallback)
            coupling_constant=1.0
        )
        self.interactive = interactive
        
        # Modules map
        # Key: Name -> (PhysicsEngine Class, Renderer Class)
        # Note: Calabi-Yau has no physics engine (None)
        self.modules = {
            "1": ("Nambu-Goto String", RelativisticString, StringRenderer),
            "2": ("BFSS Matrix", BFSSMatrixModel, MatrixRenderer),
            "3": ("Calabi-Yau", None, CalabiYauRenderer)
        }
        
        self.current_mode = "1"
        self.physics: PhysicsEngine | None = None
        self.renderer: Renderer | None = None
        
        self.is_running = True

    def switch_module(self, mode_key: str):
        if mode_key not in self.modules:
            return
            
        print(f"Switching to {self.modules[mode_key][0]}...")
        self.current_mode = mode_key
        
        # Cleanup old renderer if exists
        if self.renderer and hasattr(self.renderer, 'plotter'):
            # self.renderer.plotter.close() # Don't close window, just clear
            self.renderer.plotter.clear()
        
        # Instantiate new components
        name, PhysicsCls, RendererCls = self.modules[mode_key]
        
        if PhysicsCls:
            self.physics = PhysicsCls()
            self.physics.initialize(self.config)
        else:
            self.physics = None
            
        # We need to preserve the plotter window if possible, 
        # but Renderers currently create their own Plotter in __init__.
        # To reuse the window, we would need to pass the plotter to the renderer.
        # Refactoring Renderers to accept an existing plotter is better, 
        # but for now, we'll close and recreate or just let Renderer handle it.
        # Actually, closing the plotter breaks the 'show' loop usually.
        # Let's try to keep the plotter in MainController and pass it? 
        # Too much refactoring for now. 
        # Current Renderer impl creates 'self.plotter = pv.Plotter()'.
        # If we switch, we might need to close the old window and open a new one, 
        # which is jarring.
        
        # Quick fix: If we are already running, we can't easily swap the plotter 
        # because the 'show()' loop is blocking in the renderer's plotter.
        # BUT, we are running our own loop 'while True'.
        # The plotter is created in Renderer.__init__.
        # If we discard the old Renderer, we discard the old Plotter.
        # We need to close the old plotter window.
        
        if self.renderer:
            self.renderer.plotter.close()
            
        self.renderer = RendererCls(interactive=self.interactive)
        self.renderer.setup_scene()
        
        # Re-bind keys to the NEW plotter
        if self.interactive:
            self.setup_ui()
            # If we are inside the loop, we just need to show the new plotter?
            # PyVista 'show(interactive_update=True)' creates the window.
            self.renderer.plotter.show(interactive_update=True, title=f"StringVerse - {name}")

    def setup_ui(self):
        """Setup UI widgets and callbacks on the current plotter."""
        if not self.interactive or not self.renderer:
            return
            
        plotter = self.renderer.plotter
        
        # Key callbacks
        plotter.add_key_event("1", lambda: self.request_switch("1"))
        plotter.add_key_event("2", lambda: self.request_switch("2"))
        plotter.add_key_event("3", lambda: self.request_switch("3"))
        plotter.add_key_event("space", lambda: self.trigger_poke())
        
        # Sliders
        # We need to update self.config
        
        def update_coupling(value):
            self.config.coupling_constant = value
            
        def update_mass(value):
            # Hack: access physics engine directly if it has mass
            if hasattr(self.physics, 'mass'):
                self.physics.mass = value

        plotter.add_slider_widget(
            update_coupling,
            [0.1, 10.0],
            value=self.config.coupling_constant,
            title="Coupling / Tension",
            pointa=(0.025, 0.1),
            pointb=(0.31, 0.1),
            style="modern"
        )
        
        if self.current_mode == "2": # BFSS
             plotter.add_slider_widget(
                update_mass,
                [0.1, 5.0],
                value=1.0,
                title="Mass / Confinement",
                pointa=(0.6, 0.1),
                pointb=(0.9, 0.1),
                style="modern"
            )

    def request_switch(self, mode: str):
        # We can't switch immediately inside a callback or we risk race conditions/segfaults 
        # if we destroy the plotter while it's processing events.
        # We set a flag or just do it if careful.
        # Since we control the loop, it's safer to set a flag.
        self._pending_switch = mode

    def trigger_poke(self):
        """Trigger an explosion in the current physics engine (if supported)."""
        if self.physics and hasattr(self.physics, 'poke'):
            self.physics.poke(strength=5.0)
            print("💥 BOOM! D0-branes excited!")

    def run(self):
        # Initial setup
        self._pending_switch = self.current_mode
        
        # Main Loop
        while self.is_running:
            # Handle Scene Switching
            if hasattr(self, '_pending_switch') and self._pending_switch:
                mode = self._pending_switch
                self._pending_switch = None
                self.switch_module(mode)
            
            # Simulation Loop
            if self.renderer:
                try:
                    start_time = time.time()
                    
                    # Physics Step
                    if self.physics:
                        self.physics.step(self.config.time_step)
                        state = self.physics.get_state()
                        self.renderer.update_actors(state)
                    else:
                        # Just update renderer (e.g. rotation for static mesh)
                        self.renderer.update_actors(None)
                    
                    # Render
                    self.renderer.plotter.update()
                    
                    # Check close
                    if getattr(self.renderer.plotter, 'closed', False):
                        self.is_running = False
                        break
                        
                    # Pacing
                    elapsed = time.time() - start_time
                    target = 1.0 / 60.0
                    if elapsed < target:
                        time.sleep(target - elapsed)
                        
                except KeyboardInterrupt:
                    print("Stopped.")
                    break
                except Exception as e:
                    print(f"Error in loop: {e}")
                    # Try to recover or exit
                    break
            else:
                break

if __name__ == "__main__":
    interactive_mode = True
    if len(sys.argv) > 1 and sys.argv[1] == "--headless":
        interactive_mode = False
        
    controller = MainController(interactive=interactive_mode)
    controller.run()
