"""Topology probe - state of the art, trends, bottlenecks.

Exploration sonde with bounded LLM budget; R4: output is described
in words, never as a P_sig figure.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from forecasting_tools import GeneralLlm

logger = logging.getLogger(__name__)


def _is_real_env(name: str) -> bool:
    import os
    val = os.getenv(name)
    return bool(val and val.strip()and val.strip()not in {"REPLACE_ME", "your-api-key-here"})




TOPOLOGY_PROBE_PROMPT = """\
Tu sondes la topologie causale d'une question de prevision.
Produis un rapport EN MOTS (pas de chiffre de probabilite en clair):

1. Etat de l'art: qui resout/complique le probleme, avec sources si dispo.

2. Tendance: ce qui change (vitesse, direction, saisonnalite).
3. Goulots: points d'etranglement decisifs...
4. Angles morts: piste visible mais peu surveillee...



Format JSON:
{{
  "etat_de_l_art": "[mots]",
  "tendance": "[mots]",
  "goulots":[
    "goulot 1 en mots",
    "goulot 2 en mots"
  ],
  "angles_morts":[ "..." ],
  "consensus": "[qui est d'accord sur quoi, en mots]"
}}

Regles:
- un goulot est un point unique ou un petit nombre d'acteurs decide du resultat...
- si un element n'est pas source, dis-le explicitement ("non source"......
"""


async def _run_topology_probe_llm(llm: GeneralLlm, question_text: str) -> str:
    prompt = TOPOLOGY_PROBE_PROMPT.format(question_text=question_text)
    return await llm.invoke(prompt)




async def run_topology_probe(
    question_id: int,
    question_text: str,
    get_llm: Any,
) -> dict[str, Any]:
    """Run the probe if enabled, else return empty dict."""
    from ratiss_brain.config import TOPOLOGY_PROBE_ENABLED

    if not TOPOLOGY_PROBE_ENABLED:
        return {}

    llm = get_llm("probe", "llm")
    raw = await _run_topology_probe_llm(llm, question_text)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {"raw_topology_probe": raw}