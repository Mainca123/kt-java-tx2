from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]
out=root/'evidence'; out.mkdir(exist_ok=True)
commands={
    'kubernetes-pods.txt':['minikube','kubectl','--','-n','tx2-ecommerce','get','pods','-o','wide'],
    'kubernetes-services.txt':['minikube','kubectl','--','-n','tx2-ecommerce','get','services,pvc'],
    'kubernetes-deployments.json':['minikube','kubectl','--','-n','tx2-ecommerce','get','deployments','-o','json'],
}
for name,command in commands.items():
    r=subprocess.run(command,cwd=root,capture_output=True,timeout=40)
    if r.returncode: raise RuntimeError(r.stderr.decode('utf-8',errors='replace'))
    (out/name).write_bytes(r.stdout)
    print('Captured '+name)
(out/'maven-build.txt').write_bytes((root/'build.log').read_bytes())
