"""Voie B: topologie sémantique réelle, score interne uniquement.

Le pipeline charge les paramètres scellés, obtient des embeddings OpenRouter,
normalise le nuage, puis réduit le complexe Vietoris--Rips en homologie
persistante H1 sur F2. Les scores ne sont jamais destinés au commentaire public.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
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
    if len(a) != len(b):
        raise ValueError("embedding dimensions differ")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _xor_reduce(column: set[int], reduced: dict[int, set[int]], pivots: dict[int, int]) -> set[int]:
    """Reduce one boundary column over F2 using the standard pivot map."""
    while column:
        pivot = max(column)
        previous = reduced.get(pivots.get(pivot, -1))
        if previous is None:
            break
        column.symmetric_difference_update(previous)
    return column


def h1_persistence(points: list[list[float]], max_edge: float) -> list[tuple[float, float]]:
    """Compute H1 birth/death pairs by Vietoris--Rips matrix reduction over F2."""
    if max_edge <= 0 or not points:
        return []
    n = len(points)
    distances = {(i, j): _distance(points[i], points[j]) for i in range(n) for j in range(i + 1, n)}
    edges = [(d, 1, (i, j)) for (i, j), d in distances.items() if d <= max_edge]
    triangles = [
        (max(distances[(i, j)], distances[(i, k)], distances[(j, k)]), 2, (i, j, k))
        for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n)
        if distances[(i, j)] <= max_edge and distances[(i, k)] <= max_edge and distances[(j, k)] <= max_edge
    ]
    simplices: list[tuple[float, int, tuple[int, ...]]] = [(0.0, 0, (i,)) for i in range(n)]
    simplices.extend(edges)
    simplices.extend(triangles)
    simplices.sort(key=lambda item: (item[0], item[1], item[2]))
    index = {simplex: position for position, (_, _, simplex) in enumerate(simplices)}
    reduced: dict[int, set[int]] = {}
    pivots: dict[int, int] = {}
    births: dict[int, float] = {}
    intervals: list[tuple[float, float]] = []

    for column_index, (filtration, dimension, simplex) in enumerate(simplices):
        if dimension == 0:
            boundary: set[int] = set()
        elif dimension == 1:
            boundary = {index[(simplex[0],)], index[(simplex[1],)]}
        else:
            boundary = {
                index[(simplex[0], simplex[1])],
                index[(simplex[0], simplex[2])],
                index[(simplex[1], simplex[2])],
            }
        boundary = _xor_reduce(boundary, reduced, pivots)
        if not boundary:
            if dimension == 1:
                births[column_index] = filtration
        else:
            pivot = max(boundary)
            reduced[column_index] = boundary
            pivots[pivot] = column_index
            if dimension == 2 and pivot in births:
                intervals.append((births.pop(pivot), filtration))

    intervals.extend((birth, max_edge) for birth in births.values())
    return sorted((birth, death) for birth, death in intervals if death > birth + 1e-12)


def _prepare_points(points: list[list[float]], params: dict[str, Any]) -> list[list[float]]:
    limit = int(params["n_points"])
    selected = list(points)
    if len(selected) > limit:
        rng = random.Random(int(params["seed"]))
        selected = [selected[i] for i in sorted(rng.sample(range(len(selected)), limit))]
    if params.get("normalization") != "l2":
        raise ValueError("unsupported normalization")
    return _l2_normalize(selected)


def internal_topology_score(points: list[list[float]], max_edge: float) -> float:
    pairs = h1_persistence(points, max_edge)
    return sum(max(0.0, death - birth) for birth, death in pairs)


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


def compute_real_topology(texts: list[str]) -> dict[str, Any]:
    """Compute bounded real topology with explicit disabled/error/ok status."""
    params, params_sha256 = load_topology_params()
    if not os.getenv("OPENROUTER_API_KEY"):
        return {"status": "disabled", "params_sha256": params_sha256, "reason": "missing_api_key"}
    client = _embedding_client()
    if client is None:
        return {"status": "error", "params_sha256": params_sha256, "reason": "embedding_client_unavailable"}
    try:
        response = client.embeddings.create(
            model=params["model"],
            input=texts[: int(params["n_points"])],
        )
        vectors = _prepare_points([item.embedding for item in response.data], params)
        score = internal_topology_score(vectors, float(params["max_edge"]))
        bucket = "structured" if score > 0 else "no_cycle"
        factor = float(params["uncertainty_buckets"][bucket])
        return {
            "status": "ok",
            "score_internal": score,
            "adjusted_score_internal": score * factor,
            "uncertainty_bucket": bucket,
            "uncertainty_factor": factor,
            "params_sha256": params_sha256,
            "n_points": len(vectors),
        }
    except Exception as exc:
        return {"status": "error", "params_sha256": params_sha256, "reason": type(exc).__name__}
