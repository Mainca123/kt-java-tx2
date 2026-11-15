"""Regenerate the complete Kubernetes demo manifests from the local defaults."""
from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[1]
out=root/'k8s'; out.mkdir(exist_ok=True)
ns='tx2-ecommerce'
def save(name,docs):
    (out/name).write_text(yaml.safe_dump_all(docs,sort_keys=False),encoding='utf-8')
def meta(name): return {'name':name,'namespace':ns}
def env(name,value): return {'name':name,'value':str(value)}
def secret(name,key): return {'name':name,'valueFrom':{'secretKeyRef':{'name':'database-secret','key':key}}}
def service(name,ports):
    return {'apiVersion':'v1','kind':'Service','metadata':meta(name),'spec':{'selector':{'app':name},'ports':[{'name':key,'port':p,'targetPort':p} for key,p in ports]}}
def deploy(name,image,ports,envs,memory='384Mi',replicas=1,volumes=None,mounts=None):
    container={'name':name,'image':image,'imagePullPolicy':'IfNotPresent','ports':[{'containerPort':p} for p in ports],
        'env':envs,'resources':{'requests':{'cpu':'100m','memory':'192Mi'},'limits':{'cpu':'1000m','memory':memory}}}
    if mounts: container['volumeMounts']=mounts
    if name.endswith('service') or name=='api-gateway':
        container['lifecycle']={'preStop':{'exec':{'command':['/bin/sh','-c','sleep 10']}}}
        for probe,endpoint in [('readinessProbe','readiness'),('livenessProbe','liveness')]:
            container[probe]={'httpGet':{'path':f'/actuator/health/{endpoint}','port':ports[0]},'periodSeconds':10,'failureThreshold':6}
        container['startupProbe']={'httpGet':{'path':'/actuator/health/liveness','port':ports[0]},'periodSeconds':5,'failureThreshold':60}
    else:
        container['readinessProbe']={'tcpSocket':{'port':ports[0]},'initialDelaySeconds':20,'periodSeconds':10}
    pod={'containers':[container],'terminationGracePeriodSeconds':35}
    if volumes: pod['volumes']=volumes
    return {'apiVersion':'apps/v1','kind':'Deployment','metadata':meta(name),'spec':{
        'replicas':replicas,'strategy':{'type':'RollingUpdate','rollingUpdate':{'maxSurge':1,'maxUnavailable':0}},
        'selector':{'matchLabels':{'app':name}},'template':{'metadata':{'labels':{'app':name}},'spec':pod}}}

save('00-namespace.yaml',[{'apiVersion':'v1','kind':'Namespace','metadata':{'name':ns}}])
save('01-config.yaml',[
    {'apiVersion':'v1','kind':'Secret','metadata':meta('database-secret'),'type':'Opaque','stringData':{'username':'ecommerce','password':'ecommerce_dev','root-password':'root_dev_only'}},
    {'apiVersion':'v1','kind':'ConfigMap','metadata':meta('mysql-init'),'data':{'init.sql':(root/'database/init.sql').read_text(encoding='utf-8')}}])
pvcs=[{'apiVersion':'v1','kind':'PersistentVolumeClaim','metadata':meta(name),'spec':{'accessModes':['ReadWriteOnce'],'resources':{'requests':{'storage':size}}}} for name,size in [('mysql-data','2Gi'),('kafka-data','1Gi')]]
save('02-storage.yaml',pvcs)
mysql=deploy('mysql-db','mysql:8.0',[3306],[secret('MYSQL_ROOT_PASSWORD','root-password'),secret('MYSQL_USER','username'),secret('MYSQL_PASSWORD','password')],memory='512Mi',
    volumes=[{'name':'data','persistentVolumeClaim':{'claimName':'mysql-data'}},{'name':'init','configMap':{'name':'mysql-init'}}],
    mounts=[{'name':'data','mountPath':'/var/lib/mysql'},{'name':'init','mountPath':'/docker-entrypoint-initdb.d'}])
mysql['spec']['strategy']={'type':'Recreate'}
save('03-mysql.yaml',[mysql,service('mysql-db',[('mysql',3306)])])
kafka_env={
    'CLUSTER_ID':'MkU3OEVBNTcwNTJENDM2Qk','KAFKA_NODE_ID':1,'KAFKA_PROCESS_ROLES':'broker,controller',
    'KAFKA_LISTENERS':'PLAINTEXT://:9092,CONTROLLER://:9093','KAFKA_ADVERTISED_LISTENERS':'PLAINTEXT://kafka:9092',
    'KAFKA_LISTENER_SECURITY_PROTOCOL_MAP':'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT','KAFKA_CONTROLLER_QUORUM_VOTERS':'1@localhost:9093',
    'KAFKA_CONTROLLER_LISTENER_NAMES':'CONTROLLER','KAFKA_INTER_BROKER_LISTENER_NAME':'PLAINTEXT',
    'KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR':1,'KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR':1,
    'KAFKA_TRANSACTION_STATE_LOG_MIN_ISR':1,'KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS':0,
    'KAFKA_LOG_DIRS':'/tmp/kraft-combined-logs','KAFKA_HEAP_OPTS':'-Xmx256m -Xms128m'}
kafka=deploy('kafka','apache/kafka:3.9.1',[9092,9093],[env(k,v) for k,v in kafka_env.items()],memory='512Mi',
    volumes=[{'name':'data','persistentVolumeClaim':{'claimName':'kafka-data'}}],mounts=[{'name':'data','mountPath':'/tmp/kraft-combined-logs'}])
kafka['spec']['strategy']={'type':'Recreate'}
kafka['spec']['template']['spec']['securityContext']={'fsGroup':1000}
save('04-kafka.yaml',[kafka,service('kafka',[('broker',9092),('controller',9093)])])
for name,port,replicas in [('product-service',8081,2),('order-service',8082,1),('api-gateway',8080,1)]:
    es=[env('SERVER_PORT',port),env('APP_VERSION','local')]
    ports=[port]
    if name!='api-gateway':
        db=name.split('-')[0]+'_db'
        es += [env('DB_URL',f'jdbc:mysql://mysql-db:3306/{db}?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC'),secret('DB_USER','username'),secret('DB_PASSWORD','password'),env('KAFKA_BOOTSTRAP_SERVERS','kafka:9092'),env('MANAGEMENT_ENDPOINT_HEALTH_GROUP_READINESS_INCLUDE','readinessState,db')]
        if name=='order-service': es.append(env('PRODUCT_GRPC_ADDRESS','static://product-service:9090'))
        else: ports.append(9090)
    else: es += [env('PRODUCT_SERVICE_URL','http://product-service:8081'),env('ORDER_SERVICE_URL','http://order-service:8082')]
    d=deploy(name,f'tx2/{name}:local',ports,es,memory='512Mi',replicas=replicas)
    d['spec']['template']['spec']['securityContext']={'runAsNonRoot':True,'runAsUser':100,'runAsGroup':101}
    save(f'05-{name}.yaml',[d,service(name, [('http',port)]+([('grpc',9090)] if name=='product-service' else []))])
print('Generated k8s/*.yaml')
