"""End-to-end checks against REAL MySQL, Kafka and gRPC, through the API Gateway.
Use --resilience only for the local Docker Compose stack: it briefly stops its services.
"""
import argparse, concurrent.futures, json, subprocess, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

parser=argparse.ArgumentParser()
parser.add_argument('--base-url',default='http://localhost:18080')
parser.add_argument('--resilience',action='store_true')
parser.add_argument('--output',default='evidence/system-tests.json')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
results=[]

def api(method,path,data=None):
    body=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request(args.base_url+path,data=body,method=method,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read(); return r.status,json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw=e.read(); return e.code,json.loads(raw) if raw else None

def check(name,condition,details):
    row={'name':name,'passed':bool(condition),'details':details}
    results.append(row); print(('PASS' if condition else 'FAIL')+' '+name,flush=True)
    if not condition: raise AssertionError(json.dumps(row))

def wait_order(order_id,timeout=90):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        status,order=api('GET',f'/api/orders/{order_id}')
        if status==200 and order['status']!='PENDING': return order
        time.sleep(.5)
    raise TimeoutError(f'Order {order_id} still pending')

def compose(*commands,input=None):
    result=subprocess.run(['docker','compose',*commands],cwd=root,input=input,text=True,encoding='utf-8',capture_output=True,timeout=120)
    if result.returncode: raise RuntimeError(result.stderr)
    return result.stdout

def wait_product():
    until=time.monotonic()+100
    while time.monotonic()<until:
        try:
            if api('GET','/api/products')[0]==200: return
        except Exception: pass
        time.sleep(1)
    raise TimeoutError('Product service unavailable')

try:
    status,health=api('GET','/actuator/health')
    check('Gateway health',status==200 and health['status']=='UP',health)
    status,p=api('POST','/api/products',{'name':'E2E decimal product','price':19.95,'stock':10})
    check('Create product',status==201,p)
    pid=p['id']
    status,o=api('POST','/api/orders',{'productId':pid,'quantity':3})
    check('gRPC lookup and exact order total',status==201 and o['totalPrice']==59.85,o)
    o=wait_order(o['id'])
    stock=api('GET',f'/api/products/{pid}')[1]['stock']
    check('Kafka confirms order and deducts stock',o['status']=='CONFIRMED' and stock==7,{'order':o,'stock':stock})
    for name,payload,expected in [
        ('Reject quantity zero',{'productId':pid,'quantity':0},400),
        ('Reject insufficient stock',{'productId':pid,'quantity':11},409),
        ('gRPC missing product maps to REST 404',{'productId':9223372036854775807,'quantity':1},404)]:
        status,body=api('POST','/api/orders',payload); check(name,status==expected,body)
    status,body=api('POST','/api/products',{'name':'','price':-1,'stock':-1})
    check('Product input validation',status==400,body)
    if args.resilience:
        event=json.dumps({'orderId':o['id'],'productId':pid,'quantity':3})
        compose('exec','-T','kafka','/opt/kafka/bin/kafka-console-producer.sh','--bootstrap-server','localhost:9092','--topic','order-events',input=event+'\n'+event+'\n')
        # Ensure both replayed records were actually consumed, rather than merely waiting a fixed time.
        until=time.monotonic()+30
        group=''
        while time.monotonic()<until:
            group=compose('exec','-T','kafka','/opt/kafka/bin/kafka-consumer-groups.sh','--bootstrap-server','localhost:9092','--describe','--group','product-group')
            rows=[line.split() for line in group.splitlines() if 'order-events' in line]
            if rows and all(len(row)>5 and (row[5]=='0' or row[4]=='0') for row in rows): break
            time.sleep(.5)
        stock=api('GET',f'/api/products/{pid}')[1]['stock']
        check('Kafka duplicate delivery deducts only once',stock==7 and bool(rows) and all(row[5]=='0' or row[4]=='0' for row in rows),{'stock':stock,'consumerGroup':group})

    status,p=api('POST','/api/products',{'name':'E2E concurrent stock','price':10,'stock':3})
    concurrent_pid=p['id']
    def place(_): return api('POST','/api/orders',{'productId':concurrent_pid,'quantity':1})
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool: placed=list(pool.map(place,range(12)))
    completed=[wait_order(body['id']) for status,body in placed if status==201]
    stock=api('GET',f'/api/products/{concurrent_pid}')[1]['stock']
    confirmed=sum(order['status']=='CONFIRMED' for order in completed)
    check('12 concurrent requests cannot oversell 3 items',confirmed==3 and stock==0 and all(status in [201,409] for status,_ in placed),
        {'confirmed':confirmed,'rejectedAsync':sum(order['status']=='REJECTED' for order in completed),'httpStatuses':[s for s,_ in placed],'stock':stock})

    if args.resilience:
        try:
            compose('stop','kafka')
            status,queued=api('POST','/api/orders',{'productId':pid,'quantity':1})
            check('Kafka outage retains a pending order',status==201 and queued['status']=='PENDING',queued)
        finally: compose('start','kafka')
        recovered=wait_order(queued['id'],120)
        stock=api('GET',f'/api/products/{pid}')[1]['stock']
        check('Outbox recovers after Kafka restart',recovered['status']=='CONFIRMED' and stock==6,{'order':recovered,'stock':stock})
        try:
            compose('stop','product-service')
            status,error=api('POST','/api/orders',{'productId':pid,'quantity':1})
            check('Unavailable gRPC server returns 503',status==503,error)
        finally:
            compose('start','product-service'); wait_product()
    status,body=api('GET','/api/orders?size=101')
    check('Bounded pagination',status==400,body)
finally:
    output=root/args.output; output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'runAt':datetime.now(timezone.utc).isoformat(),'baseUrl':args.base_url,'resilience':args.resilience,'passed':sum(r['passed'] for r in results),'total':len(results),'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(results)} checks passed; evidence: {output}',flush=True)
