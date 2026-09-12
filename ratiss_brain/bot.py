"""RatissForecastBot - orchestrateur du cerveau custom RATISS Labs.

Regles rouges:
- R1: submit_predictions=False partout (garde-fou go-live).
- R3: budget LLM plafonne a MAX_QUESTIONS_PER_RUN questions par run.
- R4: aucun P_sig chiffre en clair dans la sortie publique.
- R5: chaque run logue le prompt_sha256 du prompt scelle.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ratiss_brain.config import MAX_QUESTIONS_PER_RUN, SUBMIT_PREDICTIONS
from ratiss_brain.forecast_method import build_public_comment
from ratiss_brain.scaled_prompt import load_scaled_prompt
from ratiss_brain.topology_real import compute_real_topology, load_topology_params

logger = logging.getLogger(__name__)


def _sanitize_public_comment(comment: str) -> str:
    """Keep internal P_sig scores out of public comments and logs."""
    return re.sub(r"P_sig\s*[:=]\s*[-+]?\d+(?:\.\d+)?", "P_sig: [internal score withheld]", comment, flags=re.IGNORECASE)


class RatissForecastBot:
    """Bot Metaculus custom - commentaires publics calibres par question."""

    def __init__(self, get_llm: Any, logs_dir: str = "ratiss_brain/logs"):
        self.get_llm = get_llm
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_content, self.prompt_sha256 = load_scaled_prompt()

    async def process_question(self, question: Any) -> dict:
        """Recherche + methode Jonathan + commentaire public pour UNE question."""
        comment = _sanitize_public_comment(await build_public_comment(question=question, get_llm=self.get_llm))
        _, params_sha256 = load_topology_params()
        real_topology_probe = compute_real_topology([getattr(question, "question_text", str(question))])
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "question_id": getattr(question, "id_of_question", None),
            "prompt_sha256": self.prompt_sha256,
            "comment": comment,
            "submit": SUBMIT_PREDICTIONS,
            "params_sha256": params_sha256,
            "real_topology_probe": real_topology_probe,
        }
        self._log_run(entry)
        return entry

    async def run(self, questions: list) -> list:
        """Traite la liste de questions dans la limite du budget R3."""
        selected = questions[:MAX_QUESTIONS_PER_RUN]
        if len(questions) > MAX_QUESTIONS_PER_RUN:
            logger.warning("R3 plafond: %d questions ignorees", len(questions) - MAX_QUESTIONS_PER_RUN)
        return [await self.process_question(q) for q in selected]

    def _log_run(self, entry: dict) -> None:
        """Append une ligne JSONL horodatee par run."""
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        run_file = self.logs_dir / f"run_{stamp}.jsonl"
        with run_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
