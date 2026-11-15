from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
items=[]
def request(name,method,path,body=None,status=200,tests='',pre=''):
    entry={'name':name,'request':{'method':method,'header':[], 'url':'{{baseUrl}}'+path},'event':[]}
    if body is not None:
        entry['request']['header']=[{'key':'Content-Type','value':'application/json'}]
        entry['request']['body']={'mode':'raw','raw':json.dumps(body).replace('"{{productId}}"','{{productId}}'),'options':{'raw':{'language':'json'}}}
    script=f'pm.test("HTTP {status}",()=>pm.response.to.have.status({status}));\n'+tests
    entry['event'].append({'listen':'test','script':{'type':'text/javascript','exec':script.splitlines()}})
    if pre: entry['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':pre.splitlines()}})
    items.append(entry)

request('01 Gateway health','GET','/actuator/health',tests='pm.test("Gateway UP",()=>pm.expect(pm.response.json().status).to.eql("UP"));')
request('02 List products','GET','/api/products',tests='pm.test("Product list",()=>pm.expect(pm.response.json()).to.be.an("array"));')
request('03 Create isolated product','POST','/api/products',{'name':'Postman test product','price':19.95,'stock':10},201,
    'const p=pm.response.json(); pm.collectionVariables.set("productId",p.id); pm.test("Decimal price",()=>pm.expect(p.price).to.eql(19.95));')
request('04 Update product','PUT','/api/products/{{productId}}',{'name':'Postman test product updated','price':19.95,'stock':10},200,
    'pm.test("Updated name",()=>pm.expect(pm.response.json().name).to.eql("Postman test product updated"));')
request('05 Reject invalid product','POST','/api/products',{'name':'','price':-1,'stock':-1},400)
request('06 Reject zero quantity','POST','/api/orders',{'productId':'{{productId}}','quantity':0},400)
request('07 Reject missing product','POST','/api/orders',{'productId':9223372036854775807,'quantity':1},404)
request('08 Reject insufficient stock','POST','/api/orders',{'productId':'{{productId}}','quantity':11},409)
request('09 Create order via gRPC','POST','/api/orders',{'productId':'{{productId}}','quantity':3},201,
    '''const o=pm.response.json(); pm.collectionVariables.set("orderId",o.id);
pm.test("Exact total 59.85",()=>pm.expect(o.totalPrice).to.eql(59.85));
pm.test("Initially pending",()=>pm.expect(o.status).to.eql("PENDING"));''')
request('10 Await Kafka confirmation','GET','/api/orders/{{orderId}}',tests='''const o=pm.response.json();
let attempts=Number(pm.collectionVariables.get("attempts")||0);
if(o.status==="PENDING" && attempts<30){pm.collectionVariables.set("attempts",attempts+1);pm.execution.setNextRequest("10 Await Kafka confirmation");}
else {pm.collectionVariables.unset("attempts");pm.test("Order confirmed by inventory result",()=>pm.expect(o.status).to.eql("CONFIRMED"));}''',
    pre='setTimeout(()=>{},500);')
request('11 Verify async stock deduction','GET','/api/products/{{productId}}',tests='pm.test("Stock 10 - 3 = 7",()=>pm.expect(pm.response.json().stock).to.eql(7));')
request('12 List orders','GET','/api/orders',tests='pm.test("Order persisted",()=>pm.expect(pm.response.json().some(o=>String(o.id)===String(pm.collectionVariables.get("orderId")))).to.be.true);')
request('13 Delete test product','DELETE','/api/products/{{productId}}',status=204)
request('14 Deleted product returns 404','GET','/api/products/{{productId}}',status=404)
request('15 Reject invalid pagination','GET','/api/products?size=1000',status=400)
collection={'info':{'name':'TX2 E-commerce REST gRPC Kafka','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
    'description':'Runnable API contract. Run requests in order against a real stack. Creates one test product and an order; deletes the product at the end. No authentication for the local classroom demo.'},
    'variable':[{'key':'baseUrl','value':'http://localhost:18080'}], 'item':items}
target=root/'postman'; target.mkdir(exist_ok=True)
(target/'tx2.postman_collection.json').write_text(json.dumps(collection,ensure_ascii=False,indent=2),encoding='utf-8')
(target/'local.postman_environment.json').write_text(json.dumps({'name':'TX2 Docker Compose','values':[{'key':'baseUrl','value':'http://localhost:18080','enabled':True}],'_postman_variable_scope':'environment'},indent=2),encoding='utf-8')
print('Generated Postman collection and environment')
