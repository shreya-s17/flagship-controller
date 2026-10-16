"""Development common linking boundary; no benchmark annotations are imported.

The preserved structured runner calls these same graph/model methods. Its linking
prefix is checked against link_question in tests before baseline use.
"""
import re
import json
from . import structured_runtime as base
from .semantic_runtime import SemanticGraph, SemanticModel
from .webqsp_runtime import NS, Blocked

VERSION = 'canonical-alias-linker-v1'
DISAMBIGUATE = 'Choose only one supplied entity for the mentioned topic from the question and observed descriptions. Return JSON {"entity":string,"supported":boolean}. Ambiguity unresolved => supported false. Do not answer the question.'
CATEGORIES = {'movie','movies','film','films','song','songs','language','languages','postcode','postal code','birthplace','character','characters'}


class LinkingGraph(SemanticGraph):
    def typed_link(self, mention, hint):
        if not isinstance(mention, str) or not mention.strip() or len(mention)>200 or hint not in base.TYPES:
            raise Blocked('invalid_anchor')
        normalized = re.sub(r'^the\s+', '', mention, flags=re.I)
        slug = re.sub(r'[^a-z0-9]+', '_', normalized.lower()).strip('_')
        if slug:
            # Key AND an exact case-folded English name/alias. The name need not
            # equal the alias, and a model's inferred type is only a soft hint.
            rows = self.select('SELECT DISTINCT ?entity WHERE { ?entity ns:type.object.key '+json.dumps('/en/'+slug)+' . '
                '?entity ?label_property ?label . VALUES ?label_property { ns:type.object.name ns:common.topic.alias } '
                'FILTER(LANG(?label)="en" && LCASE(STR(?label))='+json.dumps(normalized.lower())+') } ORDER BY ?entity LIMIT '+str(self.row_limit+1))
            candidates = sorted({r['entity']['value'].removeprefix(NS) for r in rows
                if r['entity']['type']=='uri' and r['entity']['value'].startswith(NS)})
            if candidates:
                self.link_repairs.append({'mention':mention, 'inferred_type_hint':hint, 'candidates':candidates,
                    'reason':'Canonical key plus observed exact English name/alias; type is a soft model hint, not a hard filter'})
                return candidates, 'type.object.key+casefold-name-or-alias; soft inferred type'
        return super().typed_link(mention, hint)

    def cards(self, candidates, context=None):
        cards = super().cards(candidates, context)
        for card in cards:
            rows = self.select('SELECT DISTINCT ?type WHERE { '+base.identifier(card['entity'])+
                ' ns:type.object.type ?type . FILTER(STRSTARTS(STR(?type),"'+NS+'")) } ORDER BY ?type LIMIT '+str(self.row_limit+1))
            card['observed_types'] = sorted({r['type']['value'].removeprefix(NS) for r in rows})
        return cards


def link_question(record, graph, model, log):
    """Same parse/link/disambiguation prefix as preserved base.run.

    All costs accrue on the supplied graph/model objects and remain in their
    audits. Independent executions are not claimed to have identical responses.
    """
    base.validate_question(record)
    parsed = model.ask(base.EXTRACT, {'question':record['question']})
    log('PARSE', parsed=parsed)
    mentions = parsed.get('anchors')
    if parsed.get('supported') is not True or not isinstance(mentions,list) or not 1<=len(mentions)<=3:
        raise Blocked('unsupported_parse')
    if not isinstance(parsed.get('obligations'),list) or not parsed['obligations']:
        raise Blocked('missing_obligations')
    excluded = [a for a in mentions if a.get('mention','').lower().strip() in CATEGORIES]
    if excluded: log('EXCLUDE_ANSWER_CATEGORY', excluded=excluded)
    mentions = [a for a in mentions if a not in excluded]
    if not mentions: raise Blocked('no_named_anchor')
    anchors = []
    for a in mentions:
        mention, hint = a.get('mention'), a.get('type_hint')
        if not isinstance(mention,str) or mention.casefold() not in record['question'].casefold() or mention.strip().rstrip('?').casefold()==record['question'].strip().rstrip('?').casefold():
            raise Blocked('invalid_topic_mention')
        candidates, predicate = graph.typed_link(mention,hint)
        log('LINK', mention=mention,type_hint=hint,candidates=candidates,predicate=predicate)
        if not candidates: raise Blocked('entity_not_found')
        if len(candidates)==1:
            anchors.append(candidates[0]); continue
        cards = graph.cards(candidates, anchors[0] if anchors else None)
        choice = model.ask(DISAMBIGUATE, {'question':record['question'],'mention':mention,'candidates':cards})
        log('DISAMBIGUATE', cards=cards,choice=choice)
        if choice.get('supported') is not True or choice.get('entity') not in candidates:
            raise Blocked('unresolved_entity')
        anchors.append(choice['entity'])
    return parsed, anchors


def semantic_run(record, graph, model, variant='repair', **kwargs):
    from .semantic_runtime import run
    result = run(record,graph,model,variant,**kwargs)
    result['linker_version'] = VERSION
    result['runtime_version'] += '+'+VERSION
    return result
