"""Offline answer-set metrics. Never imported by the prediction runner."""
import argparse
import json
from pathlib import Path


def metrics(predicted, gold):
    p, g = set(predicted), set(gold)
    overlap = len(p & g)
    precision = overlap/len(p) if p else (1.0 if not g else 0.0)
    recall = overlap/len(g) if g else (1.0 if not p else 0.0)
    return {'em':int(p==g),'precision':precision,'recall':recall,
            'f1':2*precision*recall/(precision+recall) if precision+recall else 0.0}


def score(predictions, annotations):
    labels={r['id']:r['parses'] for r in annotations}
    if len(labels)!=len(annotations): raise ValueError('Duplicate gold IDs')
    ids=[r['id'] for r in predictions]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate prediction IDs')
    rows=[]
    for prediction in predictions:
        parses=labels[prediction['id']]
        eligible=[p for p in parses if p.get('AnnotatorComment',{}).get('QuestionQuality')=='Good'
                  and p.get('AnnotatorComment',{}).get('ParseQuality')=='Complete']
        if not eligible:
            rows.append({'id':prediction['id'],'scorable':False}); continue
        p=prediction['answers'] if prediction['terminal']=='ANSWER' else []
        # Dataset-native entity IDs and answer strings; no aliases supplied to runtime.
        alternatives=[metrics(p,[a['AnswerArgument'] for a in parse['Answers']]) for parse in eligible]
        best=max(alternatives,key=lambda x:(x['f1'],x['em']))
        rows.append({'id':prediction['id'],'scorable':True,'answered':prediction['terminal']=='ANSWER',**best})
    valid=[r for r in rows if r['scorable']]
    return {'scope':'local feasibility answer-set metrics; official evaluator parity not yet certified',
            'submitted':len(rows),'scorable':len(valid),'excluded':len(rows)-len(valid),
            'macro_f1':sum(r['f1'] for r in valid)/len(valid) if valid else None,
            'em':sum(r['em'] for r in valid)/len(valid) if valid else None,'rows':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('predictions',type=Path); p.add_argument('gold',type=Path)
    a=p.parse_args()
    read=lambda path:[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    print(json.dumps(score(read(a.predictions),read(a.gold)),indent=2))
