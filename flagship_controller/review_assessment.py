"""Validate explicit independent-review submissions without inventing labels.

Metadata/attestations are self-reported, not independent proof of qualification or
independence. Agreement is descriptive across correlated cases, not accuracy.
"""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from .review_pack import DIMENSIONS

LABELS={'supported','contradicted','unknown'}


def validate(pack,submission):
    data=Path(pack).read_bytes()
    cases=[json.loads(x) for x in data.decode().splitlines() if x.strip()]
    ids=[c['case_id'] for c in cases]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate source case')
    if submission.get('cases_sha256')!=hashlib.sha256(data).hexdigest():raise ValueError('Review pack hash mismatch')
    for field in ('reviewer_id','qualification_statement','independence_statement'):
        if not isinstance(submission.get(field),str) or not submission[field].strip():raise ValueError('Missing reviewer metadata: '+field)
    if submission.get('independence_attested') is not True:raise ValueError('Independent review not attested')
    try:
        stamp=datetime.fromisoformat(submission['completed_at'].replace('Z','+00:00'))
        if stamp.tzinfo is None:raise ValueError('Timezone required')
    except (KeyError,TypeError,AttributeError,ValueError) as exc:raise ValueError('Invalid completion timestamp') from exc
    judgments=submission.get('judgments')
    if not isinstance(judgments,list) or len(judgments)!=len(ids):raise ValueError('Incomplete explicit judgments; blank forms are not reviews')
    seen=set();mapped={}
    for item in judgments:
        case_id=item.get('case_id')
        if case_id not in ids or case_id in seen:raise ValueError('Unknown or duplicate reviewed case')
        seen.add(case_id)
        if set(item.get('dimensions',{}))!=set(DIMENSIONS):raise ValueError('Missing review dimension')
        mapped[case_id]={}
        for dimension,judgment in item['dimensions'].items():
            if not isinstance(judgment,dict) or judgment.get('label') not in LABELS or not isinstance(judgment.get('reason'),str) or not judgment['reason'].strip():
                raise ValueError('Each explicit label, including unknown, requires a written reason')
            mapped[case_id][dimension]=judgment['label']
    return mapped


def agreement(left,right):
    if len(left)!=len(right) or not left:raise ValueError('Paired nonempty labels required')
    n=len(left);observed=sum(a==b for a,b in zip(left,right))/n
    a,b=Counter(left),Counter(right)
    expected=sum(a[label]*b[label] for label in LABELS)/(n*n)
    known=[(a,b) for a,b in zip(left,right) if a!='unknown' and b!='unknown']
    return {'n':n,'raw_agreement':observed,'cohen_kappa':None if expected==1 else (observed-expected)/(1-expected),
        'joint_known_n':len(known),'joint_known_agreement':sum(a==b for a,b in known)/len(known) if known else None,
        'left_label_counts':dict(a),'right_label_counts':dict(b)}


def assess(pack,submissions):
    if len(submissions)!=2:raise ValueError('Exactly two first-pass reviewer submissions required')
    ids=[s.get('reviewer_id','').casefold().strip() for s in submissions]
    if ids[0]==ids[1]:raise ValueError('Distinct reviewer IDs required')
    maps=[validate(pack,s) for s in submissions]
    cases=list(maps[0]);disagreements=[]
    for case in cases:
        for dimension in DIMENSIONS:
            if maps[0][case][dimension]!=maps[1][case][dimension]:
                disagreements.append({'case_id':case,'dimension':dimension,'labels':[m[case][dimension] for m in maps]})
    return {'scope':'schema-validated self-attested independent submissions; metadata are not independently certified',
        'reviewers':ids,'cases':len(cases),'cases_sha256':hashlib.sha256(Path(pack).read_bytes()).hexdigest(),
        'agreement':{d:agreement(*[[m[c][d] for c in cases] for m in maps]) for d in DIMENSIONS},
        'disagreements_for_adjudication':disagreements,
        'limits':['descriptive agreement, not truth/accuracy','correlated questions; no independence or population interval claim',
            'unknown remains explicit; raw agreement may be inflated by shared unknown',
            'STOP/recovery rates remain unavailable without separate feasible-continuation adjudication',
            'retain first-pass files; adjudication must be a separate record']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pack',type=Path,required=True)
    parser.add_argument('--reviews',type=Path,nargs=2,required=True);args=parser.parse_args()
    print(json.dumps(assess(args.pack,[json.loads(p.read_text()) for p in args.reviews]),indent=2))

if __name__=='__main__':main()
