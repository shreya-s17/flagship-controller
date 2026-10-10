"""Observable-evidence controller. Gold labels are never accepted as inputs."""
from dataclasses import dataclass, asdict
import hashlib
import json
import time
import random


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class Config:
    acquisition: bool = True
    verification: bool = True
    recovery: bool = True
    stopping: bool = True
    max_expansions: int = 8
    max_checks: int = 32
    seconds: float = 120
    threshold: float = .8
    verifier_error_rate: float = 0.
    parse_error_rate: float = 0.
    seed: int = 17

    def __post_init__(self):
        if min(self.max_expansions, self.max_checks) < 0 or self.seconds < 0:
            raise ValueError("Budgets must be nonnegative")
        if not 0 <= self.threshold <= 1:
            raise ValueError("Threshold must be between zero and one")
        if not 0 <= self.verifier_error_rate <= 1 or not 0 <= self.parse_error_rate <= 1:
            raise ValueError('Verifier perturbation rates must be probabilities')

    @property
    def bits(self):
        return ''.join(str(int(x)) for x in (self.acquisition, self.verification,
                                            self.recovery, self.stopping))


class LocalEvidence:
    """Query-independent frozen envelope; returns all adjacent facts, including denials.

    Types are returned only for endpoints of observed facts. One retrieval is one
    EXPAND call; the number of edges scanned/returned is additionally recorded.
    """
    def __init__(self, graph):
        self._edges = graph['edges']
        self._types = graph['types']
        ids = [e['id'] for e in self._edges]
        if len(ids) != len(set(ids)):
            raise ValueError('Evidence IDs must be unique within the envelope')
        self._index = {}
        for edge in self._edges:
            self._index.setdefault((edge['source'], edge['relation']), []).append(edge)

    def expand(self, node, relation):
        edges = sorted(self._index.get((node, relation), []), key=lambda e: e['id'])
        nodes = {e[k] for e in edges for k in ('source', 'target')}
        return edges, {n: self._types[n] for n in nodes if n in self._types}


def check(query, path, observed, types):
    """Symbolic prefix check against acquired evidence, not an omniscient KG."""
    node = query['start']
    for depth, eid in enumerate(path):
        e = observed.get(eid)
        if e is None or depth >= len(query['relations']):
            return {'status': 'unobserved_or_invalid', 'complete': False}
        if e['source'] != node or e['relation'] != query['relations'][depth]:
            return {'status': 'path_error', 'complete': False}
        if not e.get('provenance'):
            return {'status': 'missing_provenance', 'complete': False}
        allowed = query['types'][depth]
        if allowed and types.get(e['target']) not in allowed:
            return {'status': 'type_failure', 'complete': False}
        if e.get('polarity', 1) != 1 or any(
            f['source'] == e['source'] and f['relation'] == e['relation']
            and f['target'] == e['target'] and f.get('polarity', 1) == -1
            for f in observed.values()
        ):
            return {'status': 'conflict', 'complete': False}
        node = e['target']
    complete = len(path) == len(query['relations'])
    return {'status': 'supported' if complete else 'missing_support',
            'complete': complete, 'satisfied': len(path)}


def execute(query, evidence, config=Config()):
    if not query['relations'] or len(query['relations']) != len(query['types']):
        raise ValueError('One type obligation required for every relation')
    started = time.perf_counter()
    observed, types, cache, trace = {}, {}, {}, []
    frontier = [([], 0.)]
    expansions = checks = edges_examined = 0
    retained, rejected = [], set()
    first_failure = None
    last_candidate = []
    terminal_reason = 'search_exhausted'
    rng = random.Random(config.seed)

    def state(path):
        return {'path': path, 'observed': sorted(observed),
                'frontier': [p for p, _ in frontier], 'retained': retained.copy()}

    def log(action, path, before, *, signal=None, candidates=None, added=None, reason=None):
        after = state(path)
        trace.append({'step_id': len(trace), 'action': action, 'arguments': {'path': path.copy()},
                      'state_before': before, 'state_after': after,
                      'state_hash_before': digest(before), 'state_hash_after': digest(after),
                      'candidates': candidates or [], 'chosen_action': action,
                      'evidence_added': added or [], 'verifier': signal,
                      'constraint_gaps': list(range(len(path), len(query['relations']))),
                      'recovery_decision': reason if action == 'BACKTRACK' else None,
                      'stop_decision': action if action in ('ANSWER', 'ABSTAIN') else None,
                      'reason': reason, 'cost': {'expansions': expansions, 'checks': checks,
                      'edges_examined': edges_examined, 'unique_edges': len(observed),
                      'elapsed_seconds': time.perf_counter() - started,
                      'tokens': 0, 'llm_calls': 0, 'gpu_seconds': None}})

    def fail(path, why):
        nonlocal first_failure
        if first_failure is None:
            first_failure = {'path': path.copy(), 'reason': why, 'step': len(trace),
                             'observed': sorted(observed)}
        if config.recovery:
            log('BACKTRACK', path, state(path), reason=why)
            return True
        return False

    while frontier:
        if time.perf_counter() - started >= config.seconds:
            terminal_reason = 'timeout'; break
        path, score = frontier.pop(0)
        last_candidate = path
        log('SELECT', path, state(path), candidates=[{'path': path, 'score': score}],
            reason='obligation_score' if config.acquisition else 'fixed_id_order')
        signal = None
        if config.verification:
            if checks >= config.max_checks:
                terminal_reason = 'check_cap'; break
            checks += 1
            signal = check(query, path, observed, types)
            if rng.random() < config.parse_error_rate:
                signal = {'status': 'parse_error', 'complete': False}
            elif rng.random() < config.verifier_error_rate:
                if signal['status'] not in ('supported', 'missing_support'):
                    signal = {'status': 'supported' if len(path) == len(query['relations']) else 'missing_support',
                              'complete': len(path) == len(query['relations']), 'injected_fault': 'false_accept'}
                else:
                    signal = {'status': 'false_rejection', 'complete': False, 'injected_fault': 'false_reject'}
            log('RECHECK', path, state(path), signal=signal)
            if signal['status'] not in ('supported', 'missing_support'):
                rejected.add(tuple(path))
                if not fail(path, signal['status']):
                    terminal_reason = 'recovery_disabled'; break
                continue
        if len(path) == len(query['relations']):
            confidence = .9  # Explicit heuristic diagnostic, NOT a probability of truth.
            if not config.stopping or confidence >= config.threshold:
                retained.append(path)
                if config.stopping:
                    terminal_reason = 'support_gate' if config.verification else 'confidence_only'
                    break
            continue
        node = observed[path[-1]]['target'] if path else query['start']
        relation = query['relations'][len(path)]
        key = (node, relation)
        if key not in cache:
            if expansions >= config.max_expansions:
                terminal_reason = 'expansion_cap'
                if not fail(path, terminal_reason): break
                continue
            before = state(path)
            edges, new_types = evidence.expand(node, relation)
            cache[key] = edges
            expansions += 1
            edges_examined += len(edges)
            new = [e for e in edges if e['id'] not in observed]
            observed.update({e['id']: e for e in edges})
            types.update(new_types)
            log('EXPAND', path, before, added=new, reason='next_relation_obligation')
            trace[-1]['arguments'].update(node=node, relation=relation)
        else:
            edges = cache[key]
            log('CONTINUE', path, state(path), reason='cached_evidence_no_retrieval')
        candidates = []
        for e in edges:
            if e.get('polarity', 1) != 1:
                continue
            next_path = path + [e['id']]
            # Score uses only query obligations and observed endpoint schema.
            allowed = query['types'][len(path)]
            type_match = int(not allowed or types.get(e['target']) in allowed)
            rank = len(next_path) + .5 * type_match if config.acquisition else 0.
            candidates.append({'path': next_path, 'score': rank,
                               'reason': 'depth_plus_observed_type' if config.acquisition else 'id_order'})
        log('CONTINUE', path, state(path), candidates=candidates, reason='propose_branches')
        if not candidates:
            if not fail(path, 'missing_edge'):
                terminal_reason = 'recovery_disabled'; break
        frontier.extend((c['path'], c['score']) for c in candidates)
        frontier.sort(key=lambda item: (-item[1], item[0]))

    chosen = retained[0] if retained else []
    # With V off this emits an unchecked candidate; independent evaluation must catch it.
    terminal = 'ANSWER' if chosen else 'ABSTAIN'
    log(terminal, chosen, state(chosen), reason=terminal_reason)
    candidate = chosen or last_candidate
    return {'terminal': terminal, 'answer': observed[chosen[-1]]['target'] if chosen else None,
            'proof': chosen, 'candidate': candidate,
            'confidence': .9 if len(candidate) == len(query['relations']) else
                          len(candidate) / len(query['relations']) * .7,
            'confidence_kind': 'uncalibrated_heuristic', 'reason': terminal_reason,
            'first_failure': first_failure, 'trace': trace, 'cost': trace[-1]['cost'],
            'config': asdict(config)}
