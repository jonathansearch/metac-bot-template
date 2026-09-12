"""Recherche web gratuite et optionnelle via DuckDuckGo."""

from __future__ import annotations

from typing import Any


def _result_text(item: Any) -> str:
    if isinstance(item, dict):
        title = item.get("title", "")
        href = item.get("href", "") or item.get("url", "")
        body = item.get("body", "") or item.get("snippet", "")
        return f"- {title}\n  Source: {href}\n  Extrait: {body}".strip()
    return str(item)


def search_duckduckgo(query: str, max_results: int = 5) -> str:
    """Return source-labelled search results, or an explicit no-result message."""
    try:
        from ddgs import DDGS
    except ImportError:
        return "Recherche DuckDuckGo indisponible: paquet ddgs non installé."

    try:
        with DDGS() as client:
            results = list(client.text(query, max_results=max_results))
    except Exception as exc:  # network/provider errors must not crash a run
        return f"Recherche DuckDuckGo indisponible: {type(exc).__name__}."

    if not results:
        return "Aucun résultat DuckDuckGo trouvé."
    return "Résultats DuckDuckGo (sources à vérifier):\n" + "\n".join(
        _result_text(item) for item in results
    )


async def run_free_search(prompt: str, max_results: int = 5) -> str:
    """Async-compatible wrapper around the synchronous ddgs client."""
    return search_duckduckgo(prompt, max_results=max_results)
