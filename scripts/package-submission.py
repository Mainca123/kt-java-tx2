"""Package the requested three-entry layout; excludes build caches and local tooling.
Optional: python scripts/package-submission.py --name NGUYENVANA --student-id 123456
"""
import argparse, subprocess, uuid
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--name',default='TX2')
parser.add_argument('--student-id',default='BaiNop')
args=parser.parse_args()
if not all(x.replace('_','').isalnum() and x.isascii() for x in [args.name,args.student_id]):
    raise SystemExit('Use ASCII letters, digits and underscores for submission name')
code=Path(__file__).resolve().parents[1]; root=code.parent
files=[root/'TX2.pdf',root/'baocao.docx']
exclude={'.git','target','tmp','output','logs','__pycache__'}
for path in code.rglob('*'):
    rel=path.relative_to(code)
    if rel.parts[:2]==('evidence','figures'):
        # Legacy log illustrations are superseded by the original screenshots embedded in the report.
        continue
    if path.is_file() and not any(part in exclude for part in rel.parts) and path.name!='.env' and not (path.parent==code and path.suffix=='.log'):
        files.append(path)
if not all(p.exists() for p in files): raise SystemExit('Missing PDF or report')
temp=code/'tmp';temp.mkdir(exist_ok=True)
listing=temp/'submission-files.txt'
listing.write_text('\n'.join('"'+str(p.relative_to(root))+'"' for p in files),encoding='utf-8')
output=code/'output';output.mkdir(exist_ok=True)
archive=output/f'{args.name}_{args.student_id}.RAR'
rar=Path('C:/Program Files/WinRAR/Rar.exe')
if not rar.exists(): raise SystemExit('WinRAR Rar.exe not found')
staging=(temp/(archive.stem+'-'+uuid.uuid4().hex+'.RAR')).resolve()
if staging.parent!=temp.resolve() or archive.resolve().parent!=output.resolve():
    raise SystemExit('Unexpected archive path')
subprocess.run([str(rar),'a','-m3','-scfl','-idq',str(staging),'@'+str(listing)],cwd=root,check=True)
subprocess.run([str(rar),'t','-idq',str(staging)],cwd=root,check=True)
# Rebuild instead of adding to the previous RAR, so excluded legacy files cannot linger.
staging.replace(archive)
print(f'Packed and verified {archive} ({len(files)} files)')
