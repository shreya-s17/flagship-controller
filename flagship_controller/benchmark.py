"""Official WebQSP intake only; never convert gold parses into controller plans."""
import argparse
import hashlib
import json
import random
import zipfile
from pathlib import Path


def prepare(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        train = json.loads(z.read('WebQSP/data/WebQSP.train.json'))
        test = json.loads(z.read('WebQSP/data/WebQSP.test.json'))
        partial = {split: len(json.loads(z.read(f'WebQSP/data/WebQSP.{split}.partial.json'))['Questions'])
                   for split in ('train','test')}
    # Keep exact-duplicate question strings in one internal development group.
    groups = {}
    for q in train['Questions']:
        groups.setdefault(' '.join(q['ProcessedQuestion'].lower().split()), []).append(q['QuestionId'])
    keys = sorted(groups); random.Random(17).shuffle(keys)
    splits = {'pilot': [], 'calibration': [], 'policy': [], 'train_remaining': [],
              'test': [q['QuestionId'] for q in test['Questions']]}
    for index, key in enumerate(keys):
        target = 'pilot' if index < 50 else 'calibration' if index < 100 else 'policy' if index < 150 else 'train_remaining'
        splits[target].extend(groups[key])
    lookup = {qid: split for split, ids in splits.items() for qid in ids}
    question_keys_test = {' '.join(q['ProcessedQuestion'].lower().split()) for q in test['Questions']}
    overlap = sorted(set(groups) & question_keys_test)
    # Raw natural-language input is separated from every annotated entity/parse/answer.
    with (destination/'inputs.jsonl').open('w') as inputs, (destination/'evaluation-only.jsonl').open('w') as gold:
        for q in train['Questions'] + test['Questions']:
            inputs.write(json.dumps({'id':q['QuestionId'],'question':q['RawQuestion'],
                                     'split':lookup[q['QuestionId']]})+'\n')
            gold.write(json.dumps({'id':q['QuestionId'],'parses':q['Parses']})+'\n')
    # The owner must be a different account from the deployed runtime user.
    (destination/'evaluation-only.jsonl').chmod(0o600)
    manifest = {'dataset':'WebQSP', 'version':train['Version'], 'freebase_version':train['FreebaseVersion'],
                'source':'https://www.microsoft.com/en-ie/download/details.aspx?id=52763',
                'archive_sha256':hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
                'complete_train':len(train['Questions']), 'complete_test':len(test['Questions']),
                'partial_counts':partial, 'splits':splits, 'exact_question_overlap_count':len(overlap),
                'split_seed':17, 'parse_execution':'Gold parses are not executed by intake',
                'controller_plan':'Not derived from annotations; question-only runtime required',
                'paraphrase_overlap_audit':'PENDING; exact-string grouping only',
                'run_status':'INTAKE ONLY; no benchmark results'}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('archive',type=Path)
    p.add_argument('--output',type=Path,default=Path('benchmark-data/webqsp'))
    args=p.parse_args()
    manifest=prepare(args.archive,args.output)
    print(json.dumps({k:v for k,v in manifest.items() if k!='splits'},indent=2))
