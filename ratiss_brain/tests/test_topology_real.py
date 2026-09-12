import math
import unittest

from ratiss_brain.topology_real import h1_persistence, internal_topology_score, load_topology_params


class TestRealTopology(unittest.TestCase):
    def test_unit_square_cycle_transition(self):
        square = [[0, 0], [1, 0], [1, 1], [0, 1]]
        pairs = h1_persistence(square, math.sqrt(2))
        self.assertEqual(len(pairs), 1)
        birth, death = pairs[0]
        self.assertAlmostEqual(birth, 1.0, places=3)
        self.assertAlmostEqual(death, math.sqrt(2), places=3)

    def test_live_cycle_is_bounded_by_max_edge(self):
        square = [[0, 0], [1, 0], [1, 1], [0, 1]]
        pairs = h1_persistence(square, 1.1)
        self.assertEqual(pairs, [(1.0, 1.1)])

    def test_dispersed_cloud_has_no_cycle(self):
        points = [[0, 0], [10, 0], [0, 10], [10, 10]]
        self.assertEqual(internal_topology_score(points, 0.5), 0.0)

    def test_params_hash_is_available(self):
        params, digest = load_topology_params()
        self.assertEqual(len(digest), 64)
        self.assertEqual(params["uncertainty_buckets"], {"structured": 0.9, "no_cycle": 1.1, "mixed": 1.0})


if __name__ == "__main__":
    unittest.main()
