import unittest
import numpy as np
import sys
import os

from stringverse.core.models import SimulationConfig
from stringverse.physics.string_engine import RelativisticString

class TestStringPhysics(unittest.TestCase):
    def test_initialization(self):
        config = SimulationConfig(resolution=100)
        engine = RelativisticString()
        engine.initialize(config)
        state = engine.get_state()
        
        self.assertEqual(state.positions.shape, (100, 3))
        self.assertEqual(state.velocities.shape, (100, 3))
        self.assertGreater(state.energy, 0)

    def test_energy_conservation(self):
        config = SimulationConfig(time_step=0.005, resolution=50, coupling_constant=1.0)
        engine = RelativisticString()
        engine.initialize(config)
        
        initial_state = engine.get_state()
        initial_energy = initial_state.energy
        
        # Run 500 steps
        for _ in range(500):
            engine.step(config.time_step)
            
        final_energy = engine.get_state().energy
        
        # Check conservation within 1%
        fluctuation = abs(final_energy - initial_energy) / initial_energy
        print(f"Energy fluctuation: {fluctuation:.4%}")
        self.assertLess(fluctuation, 0.01, "Energy drifted too much")

if __name__ == '__main__':
    unittest.main()
