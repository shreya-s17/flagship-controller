"""Generated development fixtures. No relation plans extracted from benchmark gold."""
import copy
import random

CONDITIONS = ('intact', 'support_deletion', 'distractor_deletion', 'conflict',
              'noise_25', 'noise_100', 'alias_ambiguity')


def suite(count=50, seed=17, namespace='pilot'):
    rng = random.Random(seed)
    records = []
    for i in range(count):
        prefix = f'{namespace}-{i:03d}'
        start, answer = prefix + '-root', prefix + '-answer'
        hops = rng.choice((2, 3))
        relations = ['supervisor', 'education', 'location'][:hops]
        allowed = ['person', 'university', 'country'][:hops]
        types, edges = {start: 'person'}, []
        def edge(src, rel, dst, eid, polarity=1):
            edges.append({'id': prefix + '-' + eid, 'source': src, 'relation': rel,
                          'target': dst, 'provenance': 'generated-v2', 'polarity': polarity})
        # Distractor ID order varies independently of schema; some chains are dead ends,
        # others have wrong types. The suite deliberately favors symbolic schema checks.
        for b in range(rng.randint(1, 5)):
            previous = start
            for depth in range(hops):
                node = f'{prefix}-b{b}-{depth}'
                types[node] = 'company' if depth == 0 and b % 2 == 0 else allowed[depth]
                edge(previous, relations[depth], node, f'{rng.randrange(10000):04d}-bad{b}-{depth}')
                previous = node
                if b % 2 and depth == 0: break
        good_ids = []
        previous = start
        for depth in range(hops):
            node = answer if depth == hops - 1 else f'{prefix}-good-{depth}'
            types[node] = allowed[depth]
            eid = f'{rng.randrange(10000):04d}-good-{depth}'
            edge(previous, relations[depth], node, eid)
            good_ids.append(edges[-1]['id'])
            previous = node
        base = {'base_id': prefix, 'query': {'start': start, 'relations': relations,
                'types': [[t] for t in allowed]}, 'graph': {'types': types, 'edges': edges},
                'factual_answers': [answer], 'generator_seed': seed}
        for condition in CONDITIONS:
            record = copy.deepcopy(base)
            record['condition'] = condition
            record['id'] = prefix + ':' + condition
            edited = record['graph']['edges']
            edit = {'removed': [], 'added': []}
            if condition == 'support_deletion':
                # Some cases have a separate alternative proof to the same answer.
                if i % 5 == 0:
                    alternate = copy.deepcopy([e for e in edited if e['id'] in good_ids])
                    for e in alternate: e['id'] += '-alt'
                    edited.extend(alternate)
                    edit['added'].extend(e['id'] for e in alternate)
                removed = good_ids[-1]
                edited[:] = [e for e in edited if e['id'] != removed]
                edit['removed'].append(removed)
            elif condition == 'distractor_deletion':
                removed = next(e['id'] for e in edited if e['id'] not in good_ids)
                edited[:] = [e for e in edited if e['id'] != removed]
                edit['removed'].append(removed)
            elif condition == 'conflict':
                denial = copy.deepcopy(next(e for e in edited if e['id'] == good_ids[-1]))
                denial['id'] += '-denial'; denial['polarity'] = -1
                edited.append(denial); edit['added'].append(denial['id'])
            elif condition.startswith('noise'):
                n = max(1, int(len(edited) * (.25 if condition == 'noise_25' else 1)))
                for j in range(n):
                    e = {'id': f'{prefix}-noise-{j}', 'source': start,
                         'relation': 'unrelated', 'target': f'{prefix}-noise-node-{j}',
                         'provenance': 'generated-v2', 'polarity': 1}
                    edited.append(e); edit['added'].append(e['id'])
            elif condition == 'alias_ambiguity':
                # The seed linker picks an incorrect ID sharing the same display alias.
                wrong = prefix + '-alias-root'
                record['query']['start'] = wrong
                record['graph']['types'][wrong] = 'person'
                record['linker_edit'] = {'true_id': start, 'selected_id': wrong,
                                         'alias': 'researcher X'}
            record['edit'] = edit
            records.append(record)
    return records
