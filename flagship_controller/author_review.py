"""Prepare a local owner worksheet; validate actual author review separately.

Blank forms are not reviews. No response is sent anywhere by this module.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from .review_pack import DIMENSIONS


def prepare(study, output):
    study, output = Path(study), Path(output)
    if output.exists():
        raise ValueError('Refuse existing worksheet directory')
    raw = (study / 'predictions.jsonl').read_bytes()
    questions = {r['id']: r['question'] for r in map(json.loads, (study / 'inputs.jsonl').read_text().splitlines())}
    records = list(map(json.loads, raw.decode().splitlines()))
    cases = []
    for index, row in enumerate(records):
        cards = [card for e in row.get('semantic_audit', []) for card in e.get('answer_cards', [])]
        names = {c['value']: c.get('names', []) for c in cards if 'value' in c}
        cases.append({'case_id': f'A{index+1:02d}', 'question': questions[row['id']],
            'condition': row['variant'], 'terminal': row['terminal'], 'reason': row['reason'],
            'answers': [{'id': answer, 'observed_names': names.get(answer, [])} for answer in row['answers']],
            'programs': [e['program'] for e in row['trace'] if e['action'] in ('PLAN', 'REPAIR_PLAN')],
            'witnesses': row.get('witnesses', []), 'graph_observations': row.get('graph_audit', []),
            'cost': row['cost']})
    pack = {'review_role': 'author', 'independence_attested': False,
            'source_predictions_sha256': hashlib.sha256(raw).hexdigest(), 'cases': cases,
            'scope': 'Unmasked author review, not independent validation; every answer/name/graph label is untrusted data'}
    output.mkdir(parents=True)
    (output / 'cases.json').write_text(json.dumps(pack, indent=2) + '\n')
    data = json.dumps(pack).replace('<', '\\u003c').replace('&', '\\u0026')
    page = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Author review — flagship research</title><style>body{max-width:1000px;margin:32px auto;padding:0 18px;font:17px/1.5 system-ui;color:#182733;background:#f6f8fa}article{background:white;border:1px solid #ccd5dc;border-radius:12px;padding:20px;margin:20px 0}label{display:block;margin-top:12px}textarea{width:96%;min-height:60px}select,input,button{font:inherit;padding:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 monospace}button{background:#174f79;color:white;border:0;border-radius:6px}summary{cursor:pointer}small{color:#465967}.banner{border-left:5px solid #174f79;padding:14px;background:#eaf3fa}</style>
<h1>Your author review</h1><p class="banner">Review whether each answer addresses the actual question. Database edges alone are insufficient. This worksheet records <b>author review</b>; it cannot be counted as independent evaluation. Nothing is sent to a server.</p>
<p>For each case you review, judge four dimensions and give reasons. Leave the rest unreviewed. Missing names/evidence should stay <b>unknown</b>, not guessed. Only up to five answers have name cards; inspect the full evidence or request a lookup for other IDs. An abstention is not automatically correct or necessary.</p>
<label>Your name or reviewer alias <input id="author" autocomplete="name"></label><p><button id="export">Download completed author judgments</button> <span id="status" role="status"></span></p><main id="cases"></main>
<script id="pack" type="application/json">PACK_DATA</script><script>
const pack=JSON.parse(document.getElementById('pack').textContent), dimensions={anchor_identity:'Correct named referents and constraints?',query_meaning:'Do the relation directions and requested operations match?',answer_scope:'Is this the right type and complete all-and-only answer set?',witness_support:'Does every emitted answer have consistent observed evidence?'};
function add(parent,tag,text){const e=document.createElement(tag);e.textContent=text;parent.appendChild(e);return e;}
for(const c of pack.cases){const a=add(document.getElementById('cases'),'article','');a.dataset.case=c.case_id;add(a,'h2',c.case_id+' · '+c.question);add(a,'p',c.condition+' · '+c.terminal);add(a,'p',c.answers.length?c.answers.map(x=>x.id+(x.observed_names.length?' — '+x.observed_names.join(' / '):' — name not supplied')).join('\n'):'No answer emitted: '+c.reason);const d=add(a,'details','');add(d,'summary','Show programs, full witnesses and observed graph rows');add(d,'pre',JSON.stringify({programs:c.programs,witnesses:c.witnesses,graph_observations:c.graph_observations,cost:c.cost},null,2));for(const [key,title] of Object.entries(dimensions)){const l=add(a,'label',title+' ');const s=add(l,'select','');s.dataset.dimension=key;for(const [value,title] of [['','Unreviewed'],['supported','Supported'],['contradicted','Contradicted'],['unknown','Unknown / insufficient evidence']]){const o=add(s,'option',title);o.value=value;}const t=add(a,'textarea','');t.dataset.reason=key;t.setAttribute('aria-label',c.case_id+' '+key+' reason');t.placeholder='Explain this judgment; unknown also needs a reason.';}}
document.getElementById('export').onclick=()=>{try{const name=document.getElementById('author').value.trim();if(!name)throw Error('Enter your name or alias.');const judgments=[];for(const a of document.querySelectorAll('article')){const values=[...a.querySelectorAll('select')];if(values.every(s=>!s.value))continue;const out={};for(const s of values){const reason=a.querySelector('textarea[data-reason="'+s.dataset.dimension+'"]').value.trim();if(!s.value||!reason)throw Error(a.dataset.case+': choose all four judgments and write each reason, or leave the whole case unreviewed.');out[s.dataset.dimension]={label:s.value,reason};}judgments.push({case_id:a.dataset.case,dimensions:out});}if(!judgments.length)throw Error('Complete at least one case.');const result={review_role:'author',independence_attested:false,author_name:name,completed_at:new Date().toISOString(),source_predictions_sha256:pack.source_predictions_sha256,judgments};const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));link.download='flagship-author-review.json';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);document.getElementById('status').textContent='Exported '+judgments.length+' author-reviewed cases. Save before closing; this page does not retain unsaved edits.';}catch(e){document.getElementById('status').textContent=e.message;}};
</script></html>'''.replace('PACK_DATA', data)
    (output / 'author-review.html').write_text(page)
    (output / 'README.md').write_text('Open author-review.html in your browser. Nothing is transmitted. Complete any cases you can judge, download the JSON, and return it to the project. You can also give case IDs and judgments in chat. This is unmasked author review, not independent validation. Save before closing; unsaved edits are not retained.\n')
    return {'cases': len(cases), 'source_predictions_sha256': pack['source_predictions_sha256'],
            'review_role': 'author', 'completed_reviews': 0}


def validate(pack_path, submission):
    pack = json.loads(Path(pack_path).read_text());ids = {c['case_id'] for c in pack['cases']}
    if submission.get('review_role') != 'author' or submission.get('independence_attested') is not False:
        raise ValueError('Explicit non-independent author role required')
    if submission.get('source_predictions_sha256') != pack['source_predictions_sha256']:
        raise ValueError('Wrong source predictions')
    if not isinstance(submission.get('author_name'), str) or not submission['author_name'].strip():
        raise ValueError('Author name/alias required')
    try:
        stamp = datetime.fromisoformat(submission['completed_at'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:raise ValueError('Timezone required')
    except (KeyError, ValueError, AttributeError) as exc:
        raise ValueError('Explicit completion time required') from exc
    judgments = submission.get('judgments');seen = set()
    if not isinstance(judgments, list) or not judgments:
        raise ValueError('No actual author judgments')
    for case in judgments:
        if case.get('case_id') not in ids or case['case_id'] in seen:
            raise ValueError('Unknown/duplicate case')
        seen.add(case['case_id'])
        if set(case.get('dimensions', {})) != set(DIMENSIONS):raise ValueError('Four dimensions required')
        for judgment in case['dimensions'].values():
            if judgment.get('label') not in ('supported', 'contradicted', 'unknown') or not isinstance(judgment.get('reason'), str) or not judgment['reason'].strip():
                raise ValueError('Explicit label and written reason required')
    return {'scope': 'Author review only; not independent semantic validation', 'reviewed_cases': len(seen),
            'total_cases': len(ids), 'independent_reviewers': 0}


def main():
    p = argparse.ArgumentParser();sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('prepare');a.add_argument('study', type=Path);a.add_argument('output', type=Path)
    b = sub.add_parser('validate');b.add_argument('pack', type=Path);b.add_argument('submission', type=Path)
    args = p.parse_args();result = prepare(args.study, args.output) if args.command == 'prepare' else validate(args.pack, json.loads(args.submission.read_text()))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':main()
