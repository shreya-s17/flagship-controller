from dataclasses import dataclass, field
import time


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    provenance: str


@dataclass(frozen=True)
class Query:
    start: str
    relations: tuple[str, ...]
    # Each stage supplies allowed target types; an empty set imposes no type filter.
    allowed_types: tuple[frozenset[str], ...]

    def __post_init__(self):
        if not self.relations or len(self.relations) != len(self.allowed_types):
            raise ValueError("Need nonempty relations and one type constraint per stage")


@dataclass
class Graph:
    edges: list[Edge]
    types: dict[str, str]
    conflicts: set[tuple[str, str]] = field(default_factory=set)

    def outgoing(self, entity, relation):
        return sorted((e for e in self.edges if e.source == entity and e.relation == relation),
                      key=lambda e: (e.target, e.provenance))


def verify_path(graph, query, path):
    """Only inspect observed path and declared schema; never reference gold answers."""
    node = query.start
    for depth, edge in enumerate(path):
        if depth >= len(query.relations) or edge.source != node or edge.relation != query.relations[depth]:
            return {"status": "invalid_path", "satisfied": depth, "complete": False}
        if not edge.provenance:
            return {"status": "missing_provenance", "satisfied": depth, "complete": False}
        allowed = query.allowed_types[depth]
        if allowed and graph.types.get(edge.target) not in allowed:
            return {"status": "constraint_failure", "satisfied": depth, "complete": False}
        if (edge.source, edge.relation) in graph.conflicts:
            return {"status": "contradiction", "satisfied": depth, "complete": False}
        node = edge.target
    complete = len(path) == len(query.relations)
    return {"status": "supported" if complete else "missing_support",
            "satisfied": len(path), "complete": complete}


def run(graph, query, *, adaptive=True, max_expansions=8):
    """Depth-first candidate search with verifier feedback; fixed baseline delays verification.

    Returns one supported witness, not an exhaustive answer set or shortest proof.
    Cost unit is a graph expansion; no LLM or token cost is simulated.
    """
    if max_expansions < 0:
        raise ValueError("Budget must be nonnegative")
    frontier = [[]]
    traces = []
    seen = set()
    expansions = 0
    start = time.perf_counter()
    retrieved = set()

    def log(action, path, signal, candidates=None, reason=None, cost=0):
        traces.append({"step": len(traces), "action": action,
                       "state": {"node": path[-1].target if path else query.start,
                                 "path": [e.__dict__ for e in path],
                                 "remaining_expansions": max_expansions - expansions},
                       "candidates": candidates or [], "verifier": signal,
                       "recovery_decision": action if action == "BACKTRACK" else None,
                       "stop_decision": action if action in ("ANSWER", "ABSTAIN") else None,
                       "reason": reason, "cost": {"expansions_delta": cost,
                       "expansions_total": expansions, "unique_edges_observed": len(retrieved),
                       "elapsed_seconds": time.perf_counter() - start,
                       "tokens": None, "gpu_seconds": None}})

    while frontier:
        path = frontier.pop()
        key = tuple(path)
        if key in seen:
            continue
        seen.add(key)
        signal = verify_path(graph, query, path) if adaptive or len(path) == len(query.relations) else {
            "status": "feedback_disabled", "complete": False}
        log("RECHECK", path, signal)
        if signal["complete"]:
            log("ANSWER", path, signal, reason="complete_supported_witness")
            return {"terminal": "ANSWER", "answer": path[-1].target,
                    "path": [e.__dict__ for e in path], "trace": traces}
        if signal["status"] in {"invalid_path", "missing_provenance", "constraint_failure", "contradiction"}:
            log("BACKTRACK", path, signal, reason=signal["status"])
            continue
        if expansions >= max_expansions:
            # Continue inspecting already acquired frontier paths; no new retrieval permitted.
            log("BACKTRACK", path, signal, reason="expansion_budget_exhausted")
            continue
        node = path[-1].target if path else query.start
        edges = graph.outgoing(node, query.relations[len(path)])
        expansions += 1
        retrieved.update(edges)
        candidates = [{"edge": e.__dict__, "score": 1.0,
                       "score_reason": "matches_next_declared_relation"} for e in edges]
        log("EXPAND", path, signal, candidates, cost=1,
            reason="resolve_next_constraint" if adaptive else "fixed_relation_order")
        if not edges:
            log("BACKTRACK", path, {"status": "missing_support", "complete": False},
                reason="no_matching_edge")
        frontier.extend(path + [e] for e in reversed(edges))
    reason = "budget_exhausted" if expansions >= max_expansions else "accessible_search_exhausted"
    log("ABSTAIN", [], {"status": "unresolved_support", "complete": False}, reason=reason)
    return {"terminal": "ABSTAIN", "answer": None, "path": [], "trace": traces}
