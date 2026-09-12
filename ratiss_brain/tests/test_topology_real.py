import math
import unittest

from unittest.mock import patch

from ratiss_brain.topology_real import (
    _prepare_points,
    compute_real_topology,
    h1_persistence,
    internal_topology_score,
    load_topology_params,
)


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

    def test_sampling_uses_frozen_seed_and_limit(self):
        params, _ = load_topology_params()
        params["n_points"] = 3
        points = [[float(i), 1.0] for i in range(10)]
        self.assertEqual(_prepare_points(points, params), _prepare_points(points, params))
        self.assertEqual(len(_prepare_points(points, params)), 3)

    def test_missing_key_is_explicitly_disabled(self):
        with patch.dict("os.environ", {}, clear=True):
            result = compute_real_topology(["question", "research"])
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(len(result["params_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
