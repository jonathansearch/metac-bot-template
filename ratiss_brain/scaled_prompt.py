"""Chargeur du prompt scelle (clause R5.

Le prompt systeme du bot vit dans ratiss_brain/prompts/jonathans_method.md.
A chaque chargement, on calcule son SHA-256 (prompt_sha256) logue dans chaque run JSONL.
Toute modification du fichier change le hash - l'audit rouge peut verifier l'empreinte a tout moment.

Si le fichier est absent/illisible: echec bruyant - ne jamais prevoir avec un prompt invalide ou vide:la methode est le contrat.

"""

from __future__ import annotations

import hashlib
from pathlib import Path

_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "jonathans_method.md"


def _read_prompt() -> str:
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt scelle introuvable: {_PROMPT_PATH}. Impossible de prevoir sans la methode Jonathan."
        )
    return _PROMPT_PATH.read_text(encoding="utf-8")


def load_scaled_prompt() -> tuple[str, str]:
    """Retourne (contenu_du_prompt, prompt_sha256)."""
    content = _read_prompt()
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return content, digest


def prompt_sha256_of_file() -> str:
    """Empreinte courante du fichier - utilisee pour l'audit et pour etre comparee aux runs."""
    return hashlib.sha256(_read_prompt().encode("utf-8")).hexdigest()


def verify_prompt_integrity(expected_digest: str) -> bool:
    """Verifie que le fichier courant correspond bien a une empreinte donnee."""
    return prompt_sha256_of_file() == expected_digest
