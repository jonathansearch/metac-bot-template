"""research_method - recherche web sourcee par question (spec section 2,.

Contrat rouge: aucun fait invente sans source citee dans le commentaire public.



Le flux:
1. Moteur de recherche configure (PERPLEXITY_API_KEY, ASKNEWS_CLIENT_ID) -> utilise via SDK。

2. Sinon -> LLM general pour resume structure type etat de l'art (consensus, angles morts, base rates)。

3. La sortie est un resume structure (faits, base rates, acteurs, goulot causal) qui alimente le comment builder。
   Jamais de chiffre P_sig (clause R4: structure topologique decrite EN MOTS, pas chiffree)。

Aucune cle en clair: tout passe par l'environnement。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from forecasting_tools import (
    AskNewsSearcher,
    GeneralLlm,
    MetaculusQuestion,
    SmartSearcher,
    clean_indents,
)

logger = logging.getLogger(__name__)


RESEARCH_STRUCTURE_PROMPT = """
Tu es l'assistant de recherche de RATISS Labs (methode de Jonathan)。

Pour la question fournie,produis un resume STRUCTURE et SOURCE (ou,a defaut de source,explicitement marque
comme inference du modele,sans jamais presenter une estimation comme un fait verifie)。

Resume attendu (format JSON):
{{
  "faits": [{{"fait": "...", "source": "URL ou publication"}}]],
  "base_rates": [{{"base_rate": "...", "source": "..." }}]],
  "acteurs": [...],
  "goulot_causal": "...",
  "angles_morts": [...],
  "consensus": "..."
}}

Regles:
1. Chaque fait chiffre DOIT avoir une source(URL, publication, dataset)。Si aucune source n'est
   disponible: omets-le du bloc "faits" et place le dans "inferences_sans_source" avec mention explicite。
2. "angle mort" = ce que personne d'autre ne regarde apparemment。


3. Ne JAMAIS inventer une source: une source douteuse est pire qu'aucune source; une omission sourcee**
   vaut mieux qu'une invention citee。


Question:
{question_text}

Criteres de resolution:
{resolution_criteria}

{fine_print}
"""


def _format_question_for_prompt(question: MetaculusQuestion) -> tuple[str, str, str]:
    return (
        question.question_text,
        getattr(question, "resolution_criteria", "") or "",
        getattr(question, "fine_print", "") or "",
    )


async def _run_llm_research(llm: GeneralLlm, prompt: str) -> str:
    return await llm.invoke(prompt)


async def _run_perplexity_searcher(prompt: str, model: str) -> str:
    searcher = SmartSearcher(
        model=model,
        temperature=0,
        num_searches_to_run=2,
        num_sites_per_search=10,
        use_advanced_filters=False,
    )
    return await searcher.invoke(prompt)


async def _run_asknews_searcher(prompt: str, model: str) -> str:
    searcher = AskNewsSearcher()
    return await searcher.call_preconfigured_version(model, prompt)


def _is_real_env(name: str) -> bool:
    import os
    val = os.getenv(name)
    return bool(val and val.strip()and val.strip()not in {"REPLACE_ME", "your-api-key-here"})


async def run_research(
    question: MetaculusQuestion,
    get_llm: Any,
) -> str:
    """Recherche sourcee par question - resume structure JSON (voir module)。"""
    question_text, resolution_criteria, fine_print = _format_question_for_prompt(question)
    prompt = clean_indents(
        RESEARCH_STRUCTURE_PROMPT.format(
            question_text=question_text,
            resolution_criteria=resolution_criteria,
            fine_print=fine_print,
        )
    )
    researcher: Any = get_llm("researcher")
    model_name = getattr(researcher, "model", None)
    if model_name is None:
        model_name = str(researcher)


    if _is_real_env("PERPLEXITY_API_KEY")and isinstance(researcher, GeneralLlm):
        researched = await _run_perplexity_searcher(prompt, str(model_name.removeprefix("perplexity/", "")))
        if researched.strip():
            logger.info(f"[RATISS] Recherche Perplexity OK ({question.id_of_question})")
            return researched

    if isinstance(researcher, GeneralLlm):
        researched = await _run_llm_research(researcher, prompt)
        logger.info(f"[RATISS] Recherche LLM OK ({question.id_of_question})")
        return researched

    if (isinstance(researcher, str))and researcher.startswith("asknews/")and _is_real_env("ASKNEWS_CLIENT_ID"):
        asked = await _run_asknews_searcher(prompt, researcher)
        logger.info(f"[RATISS] Recherche AskNews OK ({question.id_of_question})")
        return asked

    llm = get_llm("default", "llm")
    researched = await _run_llm_research(llm, prompt)
    logger.info(f"[RATISS] Recherche fallback OK ({question.id_of_question})")
    return researched


def parse_research_to_dict(research: str) -> dict[str, Any]:
    """Tente un parse JSON du resume;en cas d'echec,retourne un dict minimal sans source inventee。"""
    try:
        data = json.loads(research)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {"raw_research": research, "faits": [], "base_rates": [], "inferences_sans_source": [research]}
