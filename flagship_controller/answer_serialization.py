"""Explicit RDF-to-answer serialization; no labels, scoring or inference.

The default is raw. webqsp_calendar_date projects a valid common-era xsd:date
onto its written calendar date, discarding the zone rather than shifting time.
That is an evaluation representation policy, NOT a claim of temporal equivalence.
Current archived controllers and scores do not call this experimental adapter.
"""
from copy import deepcopy
import datetime
import re
from .webqsp_runtime import NS,Blocked


def serialize(term,policy='raw'):
    if policy not in ('raw','webqsp_calendar_date'):raise ValueError('Unknown serialization policy')
    if not isinstance(term,dict) or not isinstance(term.get('value'),str):raise Blocked('invalid_rdf_term')
    value=term['value'];changed=False
    if term.get('type')=='uri':
        if not value.startswith(NS):raise Blocked('external_uri_unsupported')
        value=value[len(NS):];changed=True
    elif term.get('type') not in ('literal','typed-literal'):raise Blocked('unsupported_rdf_term')
    elif policy=='webqsp_calendar_date' and term.get('datatype')=='http://www.w3.org/2001/XMLSchema#date':
        match=re.fullmatch(r'(\d{4}-\d{2}-\d{2})(Z|[+-]\d{2}:\d{2})?',value)
        if not match:raise Blocked('unsupported_date_lexical_form')
        try:datetime.date.fromisoformat(match[1])
        except ValueError as error:raise Blocked('invalid_calendar_date') from error
        zone=match[2]
        if zone and zone!='Z':
            hour,minute=map(int,zone[1:].split(':'))
            if hour>14 or minute>59 or hour==14 and minute!=0:raise Blocked('invalid_date_zone')
        changed=value!=match[1];value=match[1]
    return {'answer':value,'raw_term':deepcopy(term),'policy':policy,'representation_changed':changed}
