"""Render DOCX through the packaged renderer; use native Word conversion on Windows
when LibreOffice is absent. Poppler and Python come from the Codex runtime.
The PDF and PNGs stay in output/qa and are not submission deliverables.
"""
import importlib.util, os, subprocess, sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
doc=root.parent/'baocao.docx'; out=root/'output/qa'; out.mkdir(parents=True,exist_ok=True)
renderers=list((Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents').glob('*/skills/documents/render_docx.py'))
if not renderers: raise SystemExit('Codex documents renderer not found')
renderer=sorted(renderers)[-1]
dependencies=Path(sys.executable).parent.parent
poppler=dependencies/'native/poppler/Library/bin'
os.environ['PATH']=str(poppler)+os.pathsep+os.environ['PATH']
direct=subprocess.run([sys.executable,str(renderer),str(doc),'--output_dir',str(out),'--dpi','144','--emit_pdf'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
(out/'renderer.log').write_text(direct.stdout+'\n'+direct.stderr,encoding='utf-8')
if direct.returncode==0:
    print(direct.stdout); raise SystemExit(0)
if 'soffice' not in direct.stderr: raise RuntimeError(direct.stderr)
print('Packaged renderer has no LibreOffice on Windows; using installed Word for PDF conversion.')
spec=importlib.util.spec_from_file_location('docx_renderer',renderer)
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
def word_to_pdf(input_path,user_profile,convert_tmp_dir,stem,verbose=False):
    pdf=Path(convert_tmp_dir)/(stem+'.pdf')
    r=subprocess.run(['powershell','-NoProfile','-File',str(root/'scripts/export-report-pdf.ps1'),'-InputFile',str(input_path),'-OutputFile',str(pdf)],capture_output=True,text=True,timeout=90)
    if r.returncode or not pdf.exists(): raise RuntimeError(r.stderr)
    return str(pdf),'Native Word PDF export'
module.convert_to_pdf=word_to_pdf
pages=module.rasterize(str(doc),str(out),144,verbose=True,emit_pdf=True)
print(f'Rendered {len(pages)} pages into {out}')
