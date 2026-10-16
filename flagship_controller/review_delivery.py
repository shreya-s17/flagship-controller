"""Export an allowlisted review package locally; never contact reviewers.

Original cases and blank forms are preserved. The private owner key and unrelated
files cannot be included by recursively archiving a parent directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from .review_pack import DIMENSIONS


def export(reviewer,brief,output,expected_cases_sha256,dimensions=DIMENSIONS):
    reviewer,brief,output = Path(reviewer),Path(brief),Path(output)
    if output.exists(): raise ValueError('Refuse existing delivery archive')
    contents={name:(reviewer/name).read_bytes() for name in
              ('README.txt','cases.jsonl','submission-template.json')}
    digest=hashlib.sha256(contents['cases.jsonl']).hexdigest()
    if digest!=expected_cases_sha256: raise ValueError('Cases hash mismatch')
    cases=[json.loads(line) for line in contents['cases.jsonl'].decode().splitlines() if line.strip()]
    ids=[case['case_id'] for case in cases]
    if not ids or len(set(ids))!=len(ids): raise ValueError('Missing or duplicate cases')
    form=json.loads(contents['submission-template.json'])
    if form['cases_sha256']!=digest or form.get('independence_attested') is not False:
        raise ValueError('Expected unchanged blank submission template')
    if any(form.get(key) for key in ('reviewer_id','qualification_statement','independence_statement','completed_at')):
        raise ValueError('Delivery must not disclose a completed reviewer identity')
    judgments=form['judgments']
    if [j['case_id'] for j in judgments]!=ids: raise ValueError('Template case order mismatch')
    for item in judgments:
        if set(item['dimensions'])!=set(dimensions): raise ValueError('Template dimensions mismatch')
        if any(j!={'label':'unknown','reason':''} for j in item['dimensions'].values()):
            raise ValueError('Delivery requires a blank form, not prior judgments')
    contents['BRIEF.txt']=brief.read_bytes()
    manifest={'scope':'unannotated local handoff; no contact or independent review performed',
        'cases':len(cases),'cases_sha256':digest,
        'files':{name:hashlib.sha256(data).hexdigest() for name,data in contents.items()}}
    contents['delivery-manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    # Validate everything before writing. No recursive file collection.
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in contents.items(): archive.writestr(name,data)
    with zipfile.ZipFile(output) as archive:
        if set(archive.namelist())!=set(contents): raise ValueError('Delivery file set mismatch')
        for name,data in contents.items():
            if archive.read(name)!=data: raise ValueError('Delivery readback mismatch')
    return {**manifest,'archive_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--reviewer',type=Path,required=True)
    parser.add_argument('--brief',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-cases-sha256',required=True);parser.add_argument('--native',action='store_true');args=parser.parse_args()
    from .native_review_pack import NATIVE_DIMENSIONS
    print(json.dumps(export(args.reviewer,args.brief,args.output,args.expected_cases_sha256,NATIVE_DIMENSIONS if args.native else DIMENSIONS),indent=2))
