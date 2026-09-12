"""Forecast method - methode Jonathan (spec section 2).

Pipeline: recherche sourcee -> base rates -> topologie en mots ->
mise a jour bayesienne -> nudge sur desaccord -> commentaire public.

Regles rouges: R1 no submission; R4 never expose a P_sig figure
"""

from __future__ import annotations

import logging
from typing import Any

from forecasting_tools import GeneralLlm
logger = logging.getLogger(__name__)


FORECAST_STRUCTURE_PROMPT = """\
Tu es le bot RATISS qui prevision une question Metaculus selon la methode Jonathan.

Tu disposes des ingredients suivants, produit par la recherche:
- research_summary: resume sourcee des faits pertinents;
- topology_probe: structure causale en mots( etat de l'art, tendances,
  goulots, angles morts, consensus).

Produis un commentaire public Metaculus calibr.. qui:
1. Cadre la question par des base rates (frequences historiques du domaine,
  taux historiques de resolution Metaculus, temps restant et tendance
  du marche. Cite tes sources.

2. Decrit la chaine causale reelle EN MOTS: qui decide, quels seuils,
  quelles dependances temporelles, quels scenarios de convergence.
 Jamais
  de chiffre P_sig en clair.



3. Fait la mise a jour bayesienne en termes qualitatifs: ce qui a change
  recemment, ce que cela deplace, et pourquoi...
4. Si les marches sont tres desaccordes, identifie l'origine probable
  du desaccord( acteur heterogene, ambiguite de definition, temporalite
  bizarre) et explique-le, sans inventer de certitude...
5. Se termine par une position claire avec une raison explicite, honnete
  sur l'incertitude. Si un fait manque de source, dis-le explicitement(
  "non source").

Format JSON:
{{
  "commentaire_public": "[texte complet, style Metaculus, source si dispo]",
  "base_rates": "[mots]",
  "topologie_en_mots": "[mots]",
  "mise_a_jour": "[mots]",
  "position": "[mots]"
}}
"""


async def _run_forecast_llm(
    forecast_llm: GeneralLlm,
    question_text: str,
    research_summary: str,
    topology: dict,
) -> str:
    topo_text = topology or {}
    if topo_text:
        topo_text = str(topo_text)
    prompt = FORECAST_STRUCTURE_PROMPT.format(
        question_text=question_text,
        research_summary=research_summary,
        topology_probe=topo_text,
    )
    return await forecast_llm.invoke(prompt)


async def build_public_comment(
    question: Any,
    get_llm: Any,
) -> str:
    """Build the public comment for one question (methode Jonathan)."""
    question_text = getattr(question, "question_text", None) or str(question)
    research_summary = await run_research(question=question, get_llm=get_llm)
    from ratiss_brain.topology_probe import run_topology_probe
    topology = await run_topology_probe(
        question_id=getattr(question, "id_of_question", 0),
        question_text=question_text,
        get_llm=get_llm,
    )
    forecast_llm = get_llm("forecast", "llm")
    raw = await _run_forecast_llm(
        forecast_llm=forecast_llm,
        question_text=question_text,
        research_summary=research_summary,
        topology=topology,
    )
    try:
        import json
        data = json.loads(raw)
        if isinstance(data, dict) and "commentaire_public" in data:
            return str(data["commentaire_public"])
    except json.JSONDecodeError:
        pass
    return raw

from ratiss_brain.research_method import run_research
