"""Smoke tests de l'architecture ratiss_brain - regles rouges R1/R3/R4/R5."""

import hashlib
import unittest
from pathlib import Path

from ratiss_brain.config import MAX_QUESTIONS_PER_RUN, SUBMIT_PREDICTIONS, TOPOLOGY_PROBE_ENABLED
from ratiss_brain.scaled_prompt import load_scaled_prompt, prompt_sha256_of_file

PROMPT_FILE = Path(__file__).resolve().parents[1] / "prompts" / "jonathans_method.md"


class TestRedRules(unittest.TestCase):
    def test_r1_no_submission_by_default(self):
        self.assertFalse(SUBMIT_PREDICTIONS)

    def test_r3_budget_cap(self):
        self.assertEqual(MAX_QUESTIONS_PER_RUN, 200)
        self.assertLessEqual(MAX_QUESTIONS_PER_RUN, 200)

    def test_r4_no_clear_psig_in_sealed_prompt(self):
        content = PROMPT_FILE.read_text(encoding="utf-8")
        import re
        self.assertIsNone(re.search(r"P_sig\s*[:=]\s*[\d.]+", content))
        self.assertIsNone(re.search(r"P_sig\s*=\s*[\d.]+", content))

    def test_r5_sealed_prompt_hash_stable(self):
        content, digest = load_scaled_prompt()
        expected = hashlib.sha256(PROMPT_FILE.read_bytes()).hexdigest()
        self.assertEqual(digest, expected)
        self.assertEqual(prompt_sha256_of_file(), expected)

    def test_module_imports(self):
        import importlib
        for module in (
            "ratiss_brain",
            "ratiss_brain.config",
            "ratiss_brain.scaled_prompt",
            "ratiss_brain.research_method",
            "ratiss_brain.topology_probe",
            "ratiss_brain.forecast_method",
            "ratiss_brain.bot",
        ):
            importlib.import_module(module)

    def test_topology_probe_off_by_default(self):
        self.assertFalse(TOPOLOGY_PROBE_ENABLED)


if __name__ == "__main__":
    unittest.main()