"""Update only the system title in the existing report, preserving other edits."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

root=Path(__file__).resolve().parents[1]
target=root.parent/'baocao.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(target) as source:
    entries=[(info,source.read(info.filename)) for info in source.infolist()]
rewritten=[]
for info,data in entries:
    if info.filename=='word/document.xml':
        tree=etree.fromstring(data)
        for paragraph in tree.xpath('//w:body/w:p[w:pPr/w:pStyle[@w:val="Title"]]',namespaces=ns):
            for text in paragraph.xpath('.//w:t',namespaces=ns):
                if text.text=='thương mại điện tử microservices':text.text='E-COMMERCE MICROSERVICES'
        data=etree.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
    elif info.filename=='docProps/core.xml':
        tree=etree.fromstring(data)
        title=tree.find('{http://purl.org/dc/elements/1.1/}title')
        if title is not None:title.text='Báo cáo xây dựng hệ thống E-COMMERCE MICROSERVICES'
        data=etree.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
    rewritten.append((info,data))
# Preserve a local rollback copy outside the three-entry submission root.
backup=root/'tmp/report-before-system-rename.docx'; backup.parent.mkdir(exist_ok=True)
if not backup.exists():backup.write_bytes(target.read_bytes())
with ZipFile(target,'w') as result:
    for info,data in rewritten:result.writestr(info,data)
print('Updated report system title')
