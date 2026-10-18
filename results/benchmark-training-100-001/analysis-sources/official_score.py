"""WebQSP official evaluator semantics, plus strict selected-slice ID validation.

Reference: Microsoft WebQSP.zip, eval/eval.py, SHA256 in the parity report.
The official script admits a question if ANY parse is Good/Complete, then
maximizes F1 over ALL parses. Empty-prediction precision is 1.0. Do not
substitute answered-only accuracy for its full-slice denominator.
"""
import argparse
import json
from pathlib import Path


def prf(gold,predicted):
    if not gold:return (1.,1.,1.) if not predicted else (0.,1.,0.)
    if not predicted:return 1.,0.,0.
    tp=1e-40;fp=fn=0.
    for g in gold:
        if g in predicted:tp+=1
        else:fn+=1
    for p in predicted:
        if p not in gold:fp+=1
    precision=tp/(tp+fp);recall=tp/(tp+fn)
    return precision,recall,2*precision*recall/(precision+recall)


def score(predictions,annotations):
    ids=[r['id'] for r in predictions];label_ids=[r['id'] for r in annotations]
    if len(set(ids))!=len(ids) or len(set(label_ids))!=len(label_ids):raise ValueError('Duplicate IDs')
    if set(ids)!=set(label_ids):raise ValueError('Selected-slice predictions and annotations must match exactly')
    predictions={r['id']:r for r in predictions};rows=[]
    for label in annotations:
        parses=label['parses']
        if not any(p.get('AnnotatorComment',{}).get('QuestionQuality')=='Good' and p.get('AnnotatorComment',{}).get('ParseQuality')=='Complete' for p in parses):
            rows.append({'id':label['id'],'scorable':False});continue
        prediction=predictions[label['id']]
        if prediction['terminal'] not in ('ANSWER','ABSTAIN'):raise ValueError('Invalid terminal')
        if prediction['terminal']=='ABSTAIN' and prediction['answers']:raise ValueError('Abstention has answers')
        answers=prediction['answers']
        best=max((prf([a['AnswerArgument'] for a in p['Answers']],answers) for p in parses),key=lambda m:m[2])
        rows.append({'id':label['id'],'scorable':True,'answered':prediction['terminal']=='ANSWER',
                     'precision':best[0],'recall':best[1],'f1':best[2],'exact_f1':int(best[2]==1.)})
    valid=[r for r in rows if r['scorable']];n=len(valid)
    return {'semantics':'Microsoft WebQSP v1.0 evaluator; selected-slice wrapper',
            'submitted':len(rows),'scorable':n,'excluded':len(rows)-n,
            'coverage':sum(r['answered'] for r in valid)/n if n else None,
            'macro_precision':sum(r['precision'] for r in valid)/n if n else None,
            'macro_recall':sum(r['recall'] for r in valid)/n if n else None,
            'macro_f1':sum(r['f1'] for r in valid)/n if n else None,
            'exact_f1_accuracy':sum(r['exact_f1'] for r in valid)/n if n else None,'rows':rows}


def main():
    p=argparse.ArgumentParser();p.add_argument('predictions',type=Path);p.add_argument('gold',type=Path);a=p.parse_args()
    predictions=[json.loads(x) for x in a.predictions.read_text().splitlines() if x.strip()]
    ids={r['id'] for r in predictions}
    annotations=[json.loads(x) for x in a.gold.read_text().splitlines() if x.strip()]
    print(json.dumps(score(predictions,[r for r in annotations if r['id'] in ids]),indent=2))
if __name__=='__main__':main()
