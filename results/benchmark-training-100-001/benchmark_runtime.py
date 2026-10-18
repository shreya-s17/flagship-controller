"""Frozen benchmark composition: nested factorial controls and local ToG.

Existing inference/adapter sources are preserved. No annotations/scorer imports.
"""
import copy
import time
from . import factorial_runtime as factorial, study_runtime as shared

VERSION = 'reserved-training-benchmark-v1'
POLICIES = (*factorial.POLICIES, 'tog-declared-json')


def capture(record, endpoint, model_url, model_name, snapshot, seed, on_event=None):
    started = time.perf_counter();link = None
    graph = factorial.FactorialGraph(endpoint, snapshot, max_calls=80)
    model = shared.StudyModel(model_url, model_name, graph=graph, seed=seed, max_calls=10, max_tokens=16000)
    def linked():
        nonlocal link
        link = factorial._prefix(graph, model, time.perf_counter() - started)
    graph.link_ready = linked
    result = factorial.run(record, graph, model, variant='fixed', on_event=factorial._boundary(
        on_event, 'SCHEMA', 'pre_catalog_capture_boundary'))
    seconds = time.perf_counter() - started
    return {'record': record, 'seed': seed, 'model': model_name, 'snapshot': snapshot,
            'link': link, 'internal': factorial._prefix(graph, model, seconds),
            'capture_result': result, 'internal_ready': result['reason'] == 'pre_catalog_capture_boundary',
            'provider_audit': model.provider_audit, 'stage': 'pre_catalog',
            'physical_stage': {'seconds': seconds, 'model_attempts': model.physical_attempts, 'graph_calls': graph.calls}}


def baseline(packet, endpoint, model_url, upstream, on_event=None):
    row = shared.continue_policy(packet, 'tog-declared-json', endpoint, model_url, upstream, on_event)
    row['benchmark_composition'] = VERSION
    row['shared_link_packet_sha256'] = shared.digest(packet['link'])
    return row


def interrupted_capture(record, seed, model, snapshot, progress):
    from .factorial_study import interrupted_packet
    return interrupted_packet(record, seed, model, snapshot, progress, stage='pre_catalog', link=None)
