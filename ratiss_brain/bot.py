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
from datetime import datetime
from pathlib import Path
from typing import Any

from ratiss_brain.config import MAX_QUESTIONS_PER_RUN, SUBMIT_PREDICTIONS
from ratiss_brain.forecast_method import build_public_comment
from ratiss_brain.scaled_prompt import load_scaled_prompt

logger = logging.getLogger(__name__)


class RatissForecastBot:
    """Bot Metaculus custom - commentaires publics calibres par question."""

    def __init__(self, get_llm: Any, logs_dir: str = "ratiss_brain/logs"):
        self.get_llm = get_llm
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_content, self.prompt_sha256 = load_scaled_prompt()

    async def process_question(self, question: Any) -> dict:
        """Recherche + methode Jonathan + commentaire public pour UNE question."""
        comment = await build_public_comment(question=question, get_llm=self.get_llm)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "question_id": getattr(question, "id_of_question", None),
            "prompt_sha256": self.prompt_sha256,
            "comment": comment,
            "submit": SUBMIT_PREDICTIONS,
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