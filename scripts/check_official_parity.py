"""Compare our scorer with the inspected official WebQSP script, offline only.

Usage: python3 scripts/check_official_parity.py /path/to/WebQSP.zip
No test questions are executed. The downloaded script is not redistributed.
Python 2 print statements are mechanically converted to Python 3 print calls.
"""
import contextlib
import hashlib
import io
import itertools
import json
from pathlib import Path
import sys
import tempfile
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.official_score import prf,score

archive=Path(sys.argv[1]);digest=hashlib.sha256(archive.read_bytes()).hexdigest()
if digest!='95cb9cd2f6b4e1116ba4bec348f08a7f5ca2a5df4f223ea5af3f9b25a971b0ee':
    raise SystemExit('Unexpected archive hash; inspect source before executing evaluator')
z=zipfile.ZipFile(archive);raw=z.read('WebQSP/eval/eval.py');source=raw.decode('utf-8-sig')
converted='\n'.join(line[:len(line)-len(line.lstrip())]+'print('+line.strip()[6:]+')' if line.strip().startswith('print ') else line for line in source.splitlines())
namespace={'__name__':'parity_reference'};exec(compile(converted,'official-WebQSP-eval','exec'),namespace)
sets=[[],['a'],['b'],['a','b'],['a','a'],['a','c','b']]
for gold,pred in itertools.product(sets,repeat=2):
    assert list(prf(gold,pred))==namespace['CalculatePRF1']([{'AnswerArgument':v} for v in gold],pred)
train=json.loads(z.read('WebQSP/data/WebQSP.train.json'))
fixtures=[train,{'Questions':[{'QuestionId':'parity-q','Parses':[
 {'AnnotatorComment':{'QuestionQuality':'Good','ParseQuality':'Complete'},'Answers':[{'AnswerArgument':'a'}]},
 {'AnnotatorComment':{'QuestionQuality':'Bad','ParseQuality':'Incomplete'},'Answers':[{'AnswerArgument':'b'}]}]}]}]
checks=[]
for fixture_index,gold in enumerate(fixtures):
    annotations=[{'id':q['QuestionId'],'parses':q['Parses']} for q in gold['Questions']]
    predictions=[]
    for i,label in enumerate(annotations):
        answers=[] if fixture_index==0 else ['b']
        predictions.append({'id':label['id'],'terminal':'ANSWER' if answers else 'ABSTAIN','answers':answers})
    ours=score(predictions,annotations)
    with tempfile.TemporaryDirectory() as tmp:
        a,b=Path(tmp)/'gold.json',Path(tmp)/'pred.json'
        a.write_text(json.dumps(gold));b.write_text(json.dumps([{'QuestionId':r['id'],'Answers':r['answers']} for r in predictions]))
        captured=io.StringIO();saved_argv=sys.argv
        try:
            sys.argv=['official_eval.py',str(a),str(b)]
            with contextlib.redirect_stdout(captured):namespace['main']()
        finally:sys.argv=saved_argv
    output=captured.getvalue()
    for label,key in [('Average precision over questions','macro_precision'),('Average recall over questions','macro_recall'),('Average f1 over questions (accuracy)','macro_f1'),('True accuracy (ratio of questions answered exactly correctly)','exact_f1_accuracy')]:
        line=next(line for line in output.splitlines() if line.startswith(label+':'))
        assert line.split(': ')[-1]==format(ours[key],'.3f'),(line,ours[key])
    checks.append({'fixture':'all-training-empty-predictions' if fixture_index==0 else 'good-admission-noncomplete-winning-parse','scorable':ours['scorable'],'official_stdout':output})
report={'source':'https://www.microsoft.com/en-us/download/details.aspx?id=52763','archive_sha256':digest,
 'official_script_sha256':hashlib.sha256(raw).hexdigest(),'helper_cases':36,'aggregate_cli_checks':checks,
 'scope':'Exact helper parity on 36 edge cases; full official CLI output parity at its 3-decimal reporting precision on two fixtures. Only print syntax changed. No test outcomes executed.','test_executed':False}
print(json.dumps(report,indent=2))
