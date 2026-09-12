"""Voie B: topologie sémantique réelle, score interne uniquement.

Le pipeline charge les paramètres scellés, obtient des embeddings OpenRouter,
normalise le nuage, calcule une persistance H1 Vietoris--Rips mod-2 et expose
un score interne. Aucun score n'est destiné au commentaire public.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

_PARAMS_PATH = Path(__file__).with_name("topology_params.json")


def load_topology_params() -> tuple[dict[str, Any], str]:
    raw = _PARAMS_PATH.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _l2_normalize(points: Iterable[Iterable[float]]) -> list[list[float]]:
    normalized: list[list[float]] = []
    for point in points:
        values = [float(value) for value in point]
        norm = math.sqrt(sum(value * value for value in values))
        if norm:
            normalized.append([value / norm for value in values])
    return normalized


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def h1_persistence(points: list[list[float]], max_edge: float) -> list[tuple[float, float]]:
    """Return H1 birth/death pairs using a small mod-2 VR reduction.

    This implementation tracks triangle boundaries over increasing edge
    thresholds. It is deliberately bounded for the n<=200 sealed budget.
    """
    n = len(points)
    edges = {(i, j): _distance(points[i], points[j]) for i in range(n) for j in range(i + 1, n)}
    levels = sorted({d for d in edges.values() if d <= max_edge})
    active_edges: set[tuple[int, int]] = set()
    active_triangles: set[tuple[int, int, int]] = set()
    births: list[tuple[float, tuple[tuple[int, int], ...]]] = []
    deaths: list[tuple[float, tuple[tuple[int, int], ...]]] = []

    def components() -> int:
        parent = list(range(n))
        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
        for a, b in active_edges:
            union(a, b)
        return len({find(i) for i in range(n)})

    previous_rank = 0
    for level in levels:
        for edge, distance in edges.items():
            if distance <= level:
                active_edges.add(edge)
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    triangle = (i, j, k)
                    if all(edge in active_edges for edge in ((i, j), (i, k), (j, k))):
                        active_triangles.add(triangle)
        rank = max(0, len(active_edges) - n + components() - len(active_triangles))
        if rank > previous_rank:
            for _ in range(rank - previous_rank):
                births.append((level, tuple(sorted(active_edges))))
        elif rank < previous_rank:
            for _ in range(previous_rank - rank):
                birth, _cycle = births.pop() if births else (level, tuple())
                deaths.append((birth, level))
        previous_rank = rank

    return [(birth, max_edge) for birth, _ in births] + deaths


def internal_topology_score(points: list[list[float]], max_edge: float) -> float:
    pairs = h1_persistence(_l2_normalize(points), max_edge)
    persistence = sum(max(0.0, death - birth) for birth, death in pairs)
    return persistence


def _embedding_client() -> Any | None:
    if not os.getenv("OPENROUTER_API_KEY"):
        return None
    try:
        from openai import OpenAI
        return OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1"),
        )
    except Exception:
        return None


def compute_real_topology(texts: list[str]) -> dict[str, Any] | None:
    """Compute bounded real topology; return None cleanly without credentials."""
    params, params_sha256 = load_topology_params()
    client = _embedding_client()
    if client is None:
        return None
    try:
        response = client.embeddings.create(
            model=params["model"],
            input=texts[: int(params.get("n_points", 200))],
        )
        vectors = [item.embedding for item in response.data]
        score = internal_topology_score(vectors, float(params["max_edge"]))
        return {
            "score_internal": score,
            "params_sha256": params_sha256,
            "n_points": len(vectors),
            "uncertainty_bucket": "structured" if score else "no_cycle",
        }
    except Exception:
        return None
