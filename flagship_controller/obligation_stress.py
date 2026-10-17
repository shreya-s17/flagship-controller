"""Offline finite countermodels for the *closed guard*, not end-to-end accuracy.

The reference interpreter below does not use the production compiler or guard
tables. Synthetic semantics are declared here, not inferred from WebQSP labels.
No model, network, graph server, benchmark input or reviewer data is accessed.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from . import obligation_runtime as runtime
from .webqsp_runtime import Blocked

VERSION = 'closed-guard-countermodels-v1'
PARENT = 'people.person.parents'
CHILD = 'people.person.children'
MEMBER = 'location.location.containedby'
CONTAINS = 'location.location.contains'
ATTRACTION = 'travel.travel_destination.tourist_attractions'
IDENTITY = 'fixture.identity'
FILTER = 'fixture.allowed'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def program(relation, direction='out', *, identity=False, filtered=False, join=None):
    steps = [{'relation': relation, 'direction': direction}]
    if identity:
        steps.append({'relation': IDENTITY, 'direction': 'out'})
    constraints = []
    if filtered:
        constraints.append({'at': len(steps), 'relation': FILTER, 'direction': 'out', 'anchor': 0})
    if join:
        constraints.append({'at': len(steps), 'relation': join[0], 'direction': join[1], 'anchor': 0})
    return {'supported': True, 'steps': steps, 'constraints': constraints}


def interpret(edges, candidate, anchor=0):
    """Independent finite relational path/join interpreter, not SPARQL replay."""
    rows = [(anchor,)]
    for step in candidate['steps']:
        rows = [row + (right if step['direction'] == 'out' else left,)
                for row in rows for left, relation, right in edges
                if relation == step['relation']
                and (left if step['direction'] == 'out' else right) == row[-1]]
    for c in candidate['constraints']:
        if c['anchor'] != 0:
            raise ValueError('Countermodel interpreter supports only anchor0')
        rows = [row for row in rows if
                ((row[c['at']], c['relation'], anchor) if c['direction'] == 'out'
                 else (anchor, c['relation'], row[c['at']])) in edges]
    return {row[-1] for row in rows}


def guard_pass(obligation, candidate, checker):
    try:
        checker(obligation, candidate)
        return True
    except Blocked:
        return False


def empty_counts():
    return dict(evaluated=0, guard_pass=0, guard_reject=0, exact_nonempty=0,
                passed_exact_nonempty=0, passed_inexact_nonempty=0,
                passed_wrong_endpoint_nonempty=0, passed_incomplete_nonempty=0,
                rejected_exact_nonempty=0, empty_candidate=0)


def record(counts, accepted, actual, expected):
    counts['evaluated'] += 1
    counts['guard_pass' if accepted else 'guard_reject'] += 1
    if not actual:
        counts['empty_candidate'] += 1
        return  # The live controller separately rejects empty acquisitions.
    exact = actual == expected
    counts['exact_nonempty'] += int(exact)
    if accepted:
        counts['passed_exact_nonempty' if exact else 'passed_inexact_nonempty'] += 1
        counts['passed_wrong_endpoint_nonempty'] += int(bool(actual - expected))
        counts['passed_incomplete_nonempty'] += int(bool(expected - actual))
    else:
        counts['rejected_exact_nonempty'] += int(exact)


def summarize_family(worlds, cases, checker):
    totals = empty_counts()
    by_case = {name: empty_counts() for name, _, _ in cases}
    examples = {}
    world_count = 0
    for world_id, edges, targets in worlds:
        world_count += 1
        for name, obligation, candidate in cases:
            expected = targets[obligation.get('role', obligation['kind'])]
            actual = interpret(edges, candidate)
            accepted = guard_pass(obligation, candidate, checker)
            record(totals, accepted, actual, expected)
            record(by_case[name], accepted, actual, expected)
            categories = []
            if accepted and actual and actual != expected:
                categories.append('passed_inexact_nonempty')
            if not accepted and actual and actual == expected:
                categories.append('rejected_exact_nonempty')
            for category in categories:
                key = name + '/' + category
                if key not in examples:
                    examples[key] = {'world_id': world_id, 'case': name,
                                     'obligation': obligation, 'program': candidate,
                                     'edges': [list(e) for e in sorted(edges)],
                                     'expected': sorted(expected), 'actual': sorted(actual),
                                     'guard_pass': accepted, 'category': category}
    return {'worlds': world_count, 'counts': totals, 'by_case': by_case,
            'first_counterexamples': list(examples.values())}


def kinship_worlds(nodes):
    pairs = list(itertools.permutations(range(nodes), 2))
    for mask in range(1 << len(pairs)):
        parents = {edge for i, edge in enumerate(pairs) if mask & (1 << i)}
        edges = {(a, PARENT, b) for a, b in parents}
        edges |= {(b, CHILD, a) for a, b in parents}
        edges |= {(a, IDENTITY, a) for a in range(nodes)}
        edges.add((1, FILTER, 0))
        # Truth is the direct matrix. No production whitelist is consulted.
        targets = {'parents': {b for a, b in parents if a == 0},
                   'children': {a for a, b in parents if b == 0}}
        yield mask, edges, targets


def kinship_cases():
    candidates = {
        'parents-out': program(PARENT), 'children-in': program(CHILD, 'in'),
        'parents-in': program(PARENT, 'in'), 'children-out': program(CHILD),
        'parents-identity': program(PARENT, identity=True),
        'children-identity': program(CHILD, identity=True),
        'parents-filtered': program(PARENT, filtered=True),
        'children-filtered': program(CHILD, filtered=True)}
    return [(role + '/' + name, {'kind': 'kinship', 'role': role}, p)
            for role in ('parents', 'children') for name, p in candidates.items()]


def location_worlds():
    # Independent three-bit attraction/root, containment and downtown sets.
    # Downtown is constrained to be a subset of the city, not equated to it.
    for roots, members, downtown in itertools.product(range(8), repeat=3):
        if downtown & ~members:
            continue
        root_set = {n for n in range(1, 4) if roots & (1 << (n - 1))}
        member_set = {n for n in range(1, 4) if members & (1 << (n - 1))}
        downtown_set = {n for n in range(1, 4) if downtown & (1 << (n - 1))}
        edges = {(0, ATTRACTION, n) for n in root_set}
        edges |= {(n, MEMBER, 0) for n in member_set}
        edges |= {(0, CONTAINS, n) for n in member_set}
        edges.add((1, FILTER, 0))
        yield [roots, members, downtown], edges, {
            'city': root_set & member_set, 'downtown': root_set & downtown_set}


def location_cases():
    candidates = {
        'unconstrained': program(ATTRACTION),
        'containedby': program(ATTRACTION, join=(MEMBER, 'out')),
        'contains-inverse': program(ATTRACTION, join=(CONTAINS, 'in')),
        'wrong-containment-direction': program(ATTRACTION, join=(MEMBER, 'in')),
        'membership-filtered': program(ATTRACTION, filtered=True, join=(MEMBER, 'out'))}
    return [(scope + '/' + name,
             {'kind': 'location_membership', 'role': scope,
              'unmodeled_qualifier': 'downtown' if scope == 'downtown' else None}, p)
            for scope in ('city', 'downtown') for name, p in candidates.items()]


def grammar_audit(cases, parser):
    rows = []
    for case in cases:
        actual = parser(case['question'], case['mentions'], case['category'])
        projected = None if actual is None else (
            {k: actual.get(k) for k in case['expected']} if case['expected'] is not None else actual)
        rows.append({'case_id': case['case_id'], 'expected': case['expected'],
                     'actual': projected, 'matches_declared_scope': projected == case['expected']})
    return {'authorship': 'Handwritten software-contract cases; not independent semantic annotations',
            'cases': len(rows), 'matching': sum(r['matches_declared_scope'] for r in rows), 'rows': rows}


def evaluate(grammar_cases, nodes=4, checker=None, parser=None):
    if type(nodes) is not int or not 2 <= nodes <= 4:
        raise ValueError('Bounded finite audit supports 2 to 4 nodes')
    checker = checker or runtime.check_obligation
    parser = parser or runtime.question_obligation
    kinship = summarize_family(kinship_worlds(nodes), kinship_cases(), checker)
    location = summarize_family(location_worlds(), location_cases(), checker)
    grammar = grammar_audit(grammar_cases, parser)
    canonical = [kinship['by_case'][f'{role}/{name}'] for role, names in
                 [('parents', ('parents-out', 'children-in')),
                  ('children', ('children-out', 'parents-in'))] for name in names]
    invariants = {
        'declared_grammar_contract': grammar['matching'] == grammar['cases'],
        'canonical_kinship_bindings_all_pass_and_are_exact_when_nonempty': all(
            r['guard_reject'] == 0 and r['passed_inexact_nonempty'] == 0 for r in canonical),
        'wrong_kinship_direction_is_always_rejected': all(
            kinship['by_case'][key]['guard_pass'] == 0 for key in
            ('parents/parents-in', 'parents/children-out', 'children/children-in', 'children/parents-out')),
        'canonical_city_membership_all_pass_and_are_exact_when_nonempty': all(
            location['by_case']['city/' + name]['guard_reject'] == 0
            and location['by_case']['city/' + name]['passed_inexact_nonempty'] == 0
            for name in ('containedby', 'contains-inverse')),
        'missing_city_membership_is_rejected': location['by_case']['city/unconstrained']['guard_pass'] == 0}
    return {'version': VERSION, 'runtime_version': runtime.VERSION,
            'scope': 'Exhaustive finite synthetic guard countermodels; not live pipeline, benchmark accuracy, or independent review',
            'nodes': nodes, 'kinship': kinship, 'location': location, 'grammar': grammar,
            'invariants': invariants, 'integrity_pass': all(invariants.values()),
            'publication_ready': False,
            'limits': [
                'No natural-world frequencies, confidence intervals, generalization or live false-rejection rate',
                'Inverse-consistent arbitrary kinship graphs include biologically impossible cycles',
                'fixture.identity and fixture.allowed are declared toy relations, not Freebase ontology claims',
                'Some tested compiler-representable programs are absent from the active bounded catalog',
                'Guard-only acceptance bypasses no claimed end-to-end test: type, empty-result and same-model checks are not simulated',
                'Canonical completeness holds only under the stated finite inverse/containment definitions',
                'Handwritten grammar fixtures and synthetic truth are software specifications, not human semantic labels',
                'Rejected exact sets can be accidental extensional coincidences; inspect the identity cases separately']}


def freeze(output, cases):
    """Bind audit inputs and all local runtime sources before enumeration."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    package = Path(__file__).parent
    sources = {p.name: sha(p) for p in sorted(package.glob('*.py'))}
    data = json.dumps(cases, indent=2, ensure_ascii=False) + '\n'
    (output / 'grammar-cases.json').write_text(data)
    manifest = {'version': VERSION, 'nodes': 4, 'grammar_sha256': sha(output / 'grammar-cases.json'),
                'source_hashes': sources, 'outputs': ['report.json'],
                'inference_requests': 0, 'benchmark_or_review_labels': False}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'manifest.sha256').write_text(sha(output / 'manifest.json') + '\n')


def execute(folder):
    folder = Path(folder)
    manifest_path = folder / 'manifest.json'
    if sha(manifest_path) != (folder / 'manifest.sha256').read_text().strip():
        raise ValueError('Frozen manifest changed')
    manifest = json.loads(manifest_path.read_text())
    if manifest['version'] != VERSION or manifest['nodes'] != 4:
        raise ValueError('Unexpected audit configuration')
    if sha(folder / 'grammar-cases.json') != manifest['grammar_sha256']:
        raise ValueError('Frozen grammar inputs changed')
    for name, expected in manifest['source_hashes'].items():
        if Path(name).name != name or sha(Path(__file__).parent / name) != expected:
            raise ValueError('Frozen audit/runtime source changed: ' + name)
    return evaluate(json.loads((folder / 'grammar-cases.json').read_text()), manifest['nodes'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('freeze');make.add_argument('--cases', type=Path, required=True)
    make.add_argument('--output', type=Path, required=True)
    run = sub.add_parser('execute');run.add_argument('folder', type=Path)
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze(args.output, json.loads(args.cases.read_text()))
    else:
        result = execute(args.folder)
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result['integrity_pass']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
