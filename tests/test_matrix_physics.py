import unittest
import numpy as np
from stringverse.core.models import SimulationConfig
from stringverse.physics.matrix_engine import BFSSMatrixModel

class TestMatrixPhysics(unittest.TestCase):
    def test_initialization(self):
        config = SimulationConfig(resolution=10) # N=10
        engine = BFSSMatrixModel()
        engine.initialize(config)
        state = engine.get_state()
        
        self.assertEqual(len(state.matrices), 3)
        self.assertEqual(state.matrices[0].shape, (10, 10))
        self.assertEqual(state.eigenvalues.shape, (10, 3))

    def test_step_execution(self):
        config = SimulationConfig(resolution=5, time_step=0.01)
        engine = BFSSMatrixModel()
        engine.initialize(config)
        
        initial_trace = np.trace(engine.matrices[0])
        engine.step(0.01)
        final_trace = np.trace(engine.matrices[0])
        
        # Just check that it changed
        self.assertNotEqual(initial_trace, final_trace)

if __name__ == '__main__':
    unittest.main()
