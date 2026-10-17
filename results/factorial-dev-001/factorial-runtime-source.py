"""Development-only catalog x closed-guard interventions with nested captures.

The preserved v2 runtime is composed, not edited. No evaluator is imported.
"""
import copy
import time
from . import obligation_runtime as parent
from .webqsp_runtime import Blocked

VERSION = 'catalog-guard-factorial-v1'
POLICIES = ('repair-C0G0', 'repair-C0G1', 'repair-C1G0', 'repair-C1G1', 'fixed-C1G1')


def settings(policy):
    if policy not in POLICIES:
        raise ValueError('Unknown factorial condition')
    return ('on' if 'C1' in policy else 'off', 'G1' in policy,
            'fixed' if policy.startswith('fixed') else 'repair')


class FactorialGraph(parent.ObligationGraph):
    def __init__(self, *args, catalog_mode='on', **kwargs):
        if catalog_mode not in ('on', 'off'):
            raise ValueError('Unknown catalog intervention')
        super().__init__(*args, **kwargs)
        self.catalog_mode = catalog_mode

    def catalog(self, question, roots, schema, anchors, mentions, connections):
        if self.catalog_mode == 'on':
            return super().catalog(question, roots, schema, anchors, mentions, connections)
        self.obligation = parent.question_obligation(question, mentions, self.question_contract['answer_category'])
        self.primary_join_options = []
        selected = parent.base.rank_catalog(question, parent.base.program_catalog(
            roots, schema, len(anchors), connections, question), limit=20)
        for i, candidate in enumerate(selected):
            candidate['index'] = i
        return selected


def run(record, graph, model, **kwargs):
    result = parent.checked_run(record, graph, model, **kwargs)
    result.update(runtime_version=VERSION, parent_runtime_version=parent.VERSION,
                  catalog_mode=graph.catalog_mode)
    return result


def _prefix(graph, model, seconds):
    return {'graph_audit': copy.deepcopy(graph.audit),
            'provider_audit': copy.deepcopy(model.provider_audit),
            'model_audit': copy.deepcopy(model.audit), 'seconds': seconds,
            'cost': {'graph_calls': graph.calls, 'model_calls': model.calls, 'model_tokens': model.tokens}}


def _boundary(on_event, action, reason):
    def event(item):
        if on_event:
            on_event(item)
        if item['action'] == action:
            raise Blocked(reason)
    return event


def capture_common(record, endpoint, model_url, model_name, snapshot, seed, on_event=None):
    started = time.perf_counter()
    graph = FactorialGraph(endpoint, snapshot, max_calls=80)
    model = parent.shared.StudyModel(model_url, model_name, graph=graph, seed=seed, max_calls=10, max_tokens=16000)
    result = run(record, graph, model, variant='fixed', on_event=_boundary(
        on_event, 'SCHEMA', 'pre_catalog_capture_boundary'))
    seconds = time.perf_counter() - started
    return {'record': record, 'seed': seed, 'model': model_name, 'snapshot': snapshot,
            'internal': _prefix(graph, model, seconds), 'capture_result': result,
            'internal_ready': result['reason'] == 'pre_catalog_capture_boundary',
            'provider_audit': model.provider_audit, 'stage': 'pre_catalog',
            'physical_stage': {'seconds': seconds, 'model_attempts': model.physical_attempts, 'graph_calls': graph.calls}}


def _replay(packet, endpoint, model_url, catalog_mode, guard_enabled=True):
    prefix = packet['internal']
    graph = FactorialGraph(endpoint, packet['snapshot'], prefix=prefix['graph_audit'],
                           max_calls=80, guard_enabled=guard_enabled, catalog_mode=catalog_mode)
    model = parent.shared.StudyModel(model_url, packet['model'], graph=graph, seed=packet['seed'],
        prefix=prefix['provider_audit'], max_calls=10, max_tokens=16000)
    return graph, model


def _assert_consumed(graph, model, result):
    if graph.cursor != len(graph.saved) or model.cursor != len(model.prefix) or 'shared_state_' in result['reason']:
        raise ValueError('Factorial common-state replay mismatch')


def capture_catalog(packet, catalog_mode, endpoint, model_url, on_event=None):
    if not packet['internal_ready']:
        result = copy.deepcopy(packet)
        result.update(stage='catalog', catalog_mode=catalog_mode, common_sha256=parent.digest(packet),
                      physical_stage={'seconds': 0., 'model_attempts': 0, 'graph_calls': 0})
        return result
    started = time.perf_counter()
    graph, model = _replay(packet, endpoint, model_url, catalog_mode)
    result = run(packet['record'], graph, model, variant='fixed',
                 seconds=max(0., 600 - packet['internal']['seconds']),
                 on_event=_boundary(on_event, 'PLAN', 'catalog_first_plan_capture_boundary'))
    _assert_consumed(graph, model, result)
    actual = time.perf_counter() - started
    return {**{k: copy.deepcopy(packet[k]) for k in ('record', 'seed', 'model', 'snapshot')},
            'internal': _prefix(graph, model, packet['internal']['seconds'] + actual),
            'capture_result': result, 'internal_ready': result['reason'] == 'catalog_first_plan_capture_boundary',
            'provider_audit': model.provider_audit, 'stage': 'catalog', 'catalog_mode': catalog_mode,
            'common_sha256': parent.digest(packet),
            'physical_stage': {'seconds': actual, 'model_attempts': model.physical_attempts,
                               'graph_calls': graph.calls - graph.cursor}}


def continue_policy(packet, policy, endpoint, model_url, on_event=None):
    catalog_mode, guard_enabled, variant = settings(policy)
    if packet['catalog_mode'] != catalog_mode:
        raise ValueError('Condition/catalog capture mismatch')
    if not packet['internal_ready']:
        result = copy.deepcopy(packet['capture_result'])
        result.update(variant=policy, catalog_mode=catalog_mode, obligation_guard_enabled=guard_enabled,
                      policy_continuation_executed=False, provider_audit=copy.deepcopy(packet['provider_audit']))
        result['cost'].update(physical_new_model_calls=0, physical_new_graph_calls=0,
                              physical_execution_seconds=0.)
        return result
    started = time.perf_counter()
    graph, model = _replay(packet, endpoint, model_url, catalog_mode, guard_enabled)
    result = run(packet['record'], graph, model, variant=variant,
        seconds=max(0., 600 - packet['internal']['seconds']), on_event=on_event)
    _assert_consumed(graph, model, result)
    actual = time.perf_counter() - started
    result['cost'].update(physical_execution_seconds=actual,
        charged_common_prefix_seconds=packet['internal']['seconds'],
        elapsed_seconds=packet['internal']['seconds'] + actual,
        physical_new_graph_calls=graph.calls - graph.cursor, physical_new_model_calls=model.physical_attempts)
    result.update(variant=policy, provider_audit=model.provider_audit, policy_continuation_executed=True,
        shared_state={'seed': packet['seed'], 'prefix_kind': 'catalog_specific_first_plan',
                      'catalog_mode': catalog_mode, 'common_pre_catalog_sha256': packet['common_sha256'],
                      'catalog_packet_sha256': parent.digest(packet),
                      'replayed_graph_calls': graph.cursor, 'replayed_model_calls': model.cursor,
                      'latency': 'charged nested capture plus replay/continuation; not fresh end-to-end latency'})
    return result
