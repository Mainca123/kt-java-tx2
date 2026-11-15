"""Check real REST reads remain available while Product pods roll one by one."""
import json, subprocess, threading, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

root=Path(__file__).resolve().parents[1]
base='http://localhost:18081'
results=[]
stop=threading.Event()
def poll():
    while not stop.is_set():
        started=time.monotonic()
        try:
            with urllib.request.urlopen(base+'/api/products/1',timeout=5) as response:
                product=json.load(response)
                results.append({'status':response.status,'valid':product.get('id')==1,'ms':round((time.monotonic()-started)*1000)})
        except Exception as e: results.append({'status':0,'valid':False,'error':str(e)})
        stop.wait(.25)
thread=threading.Thread(target=poll); thread.start()
try:
    command=['minikube','kubectl','--','-n','tx2-ecommerce']
    restart=subprocess.run(command+['rollout','restart','deployment/product-service'],capture_output=True,text=True,encoding='utf-8',timeout=30)
    if restart.returncode: raise RuntimeError(restart.stderr)
    rollout=subprocess.run(command+['rollout','status','deployment/product-service','--timeout=240s'],capture_output=True,text=True,encoding='utf-8',timeout=250)
    if rollout.returncode: raise RuntimeError(rollout.stderr)
    time.sleep(2)
finally:
    stop.set(); thread.join()
evidence={'runAt':datetime.now(timezone.utc).isoformat(),'url':base+'/api/products/1','strategy':'RollingUpdate maxSurge=1 maxUnavailable=0; product replicas=2',
    'totalRequests':len(results),'failedRequests':sum(not r['valid'] for r in results),'rolloutExitCode':rollout.returncode,'rolloutOutput':rollout.stdout,'requests':results}
(root/'evidence/rolling-update.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in evidence.items() if k!='requests'},indent=2))
if not results or evidence['failedRequests']: raise SystemExit(1)
