"""Package the requested three-entry layout; excludes build caches and local tooling.
Optional: python scripts/package-submission.py --name NGUYENVANA --student-id 123456
"""
import argparse, subprocess
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
    if path.is_file() and not any(part in exclude for part in rel.parts) and path.name!='.env' and not (path.parent==code and path.suffix=='.log'):
        files.append(path)
if not all(p.exists() for p in files): raise SystemExit('Missing PDF or report')
temp=code/'tmp';temp.mkdir(exist_ok=True)
listing=temp/'submission-files.txt'
listing.write_text('\n'.join('"'+str(p.relative_to(root))+'"' for p in files),encoding='utf-8')
output=code/'output';output.mkdir(exist_ok=True)
archive=output/f'{args.name}_{args.student_id}.rar'
rar=Path('C:/Program Files/WinRAR/Rar.exe')
if not rar.exists(): raise SystemExit('WinRAR Rar.exe not found')
subprocess.run([str(rar),'a','-m3','-scul','-idq',str(archive),'@'+str(listing)],cwd=root,check=True)
subprocess.run([str(rar),'t','-idq',str(archive)],cwd=root,check=True)
print(f'Packed and verified {archive} ({len(files)} files)')
