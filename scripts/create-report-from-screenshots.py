"""Write the TX2 report using the user's original screenshots, without modifying pixels.
Run with Codex bundled Python. No browser/terminal UI automation is performed.
"""
from pathlib import Path
from datetime import datetime
import argparse, hashlib, json, shutil
from PIL import Image
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.section import WD_ORIENT, WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

parser=argparse.ArgumentParser()
parser.add_argument('--name',default='Giàng Seo Chính')
parser.add_argument('--student-id',default='2023602847')
parser.add_argument('--class-name',default='')
student=parser.parse_args()
code=Path(__file__).resolve().parents[1]
root=code.parent
jpegs=sorted(root.glob('*.jpg'))
if len(jpegs)!=14:raise SystemExit('Expected the 14 inspected Postman screenshots in the workspace root')
sources={f'J{i:02}':p for i,p in enumerate(jpegs,1)}
sources.update({str(i):root/f'{i}.png' for i in range(2,9)})
sources.update({'products':root/'sản phẩm.png','orders':root/'đơn hàng.png'})
for path in sources.values():
    if not path.exists():raise SystemExit(f'Missing screenshot: {path}')

doc=Document()
def geometry(section,landscape=False):
    section.orientation=WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    section.page_width=Cm(29.7 if landscape else 21)
    section.page_height=Cm(21 if landscape else 29.7)
    section.top_margin=Cm(1.15 if landscape else 1.7)
    section.bottom_margin=Cm(1.15 if landscape else 1.7)
    section.left_margin=Cm(1.3 if landscape else 2.0)
    section.right_margin=Cm(1.3 if landscape else 1.7)
    section.header_distance=Cm(.5); section.footer_distance=Cm(.5)
geometry(doc.sections[0])
styles=doc.styles
for style in styles:
    for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    for fonts in style.element.iter(qn('w:rFonts')):
        for key in list(fonts.attrib):
            if 'theme' in key.lower():del fonts.attrib[key]
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
    style=styles[name]
    style.font.name='Times New Roman';style.font.color.rgb=RGBColor(0,0,0)
    fonts=style.element.get_or_add_rPr().get_or_add_rFonts()
    for key in ['ascii','hAnsi','cs','eastAsia']:fonts.set(qn('w:'+key),'Times New Roman')
styles['Normal'].font.size=Pt(12)
styles['Normal'].paragraph_format.line_spacing=1.08
styles['Normal'].paragraph_format.space_after=Pt(6)
styles['Title'].font.size=Pt(23);styles['Title'].font.bold=True
styles['Title'].paragraph_format.space_after=Pt(12)
styles['Subtitle'].font.size=Pt(12)
styles['Heading 1'].font.size=Pt(16)
styles['Heading 1'].paragraph_format.space_before=Pt(0)
styles['Heading 1'].paragraph_format.space_after=Pt(6)
styles['Heading 2'].font.size=Pt(13)
styles['Heading 2'].paragraph_format.space_before=Pt(6)
styles['Heading 2'].paragraph_format.space_after=Pt(4)
styles['Caption'].font.size=Pt(10)
styles['Caption'].font.italic=False
styles['Caption'].paragraph_format.space_before=Pt(3)
styles['Caption'].paragraph_format.space_after=Pt(5)
footer=doc.sections[0].footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=footer.add_run(f'{student.name}  |  {student.student_id}  |  Trang ');run.font.size=Pt(9)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

landscape=False
figure_no=0
used=[]
def p(text,style=None):return doc.add_paragraph(text,style)
def start_page(title,wide=False):
    global landscape
    changed=wide!=landscape
    if changed:
        geometry(doc.add_section(WD_SECTION_START.NEW_PAGE),wide)
        landscape=wide
    heading=doc.add_heading(title,level=1)
    if not changed:heading.paragraph_format.page_break_before=True
    if wide:
        for run in heading.runs:run.font.size=Pt(15)
    return heading
def description(text):
    para=p(text);para.paragraph_format.keep_with_next=True
    if landscape:
        para.paragraph_format.line_spacing=1.02
        for run in para.runs:run.font.size=Pt(11)
    return para
def picture(key,caption,width=None,max_height=None):
    global figure_no
    path=sources[key]
    if key=='J03':raise AssertionError('The excluded API 03 error screenshot must not be used')
    with Image.open(path) as image:aspect=image.height/image.width
    w=width or (26.4 if landscape else 16.8)
    h=w*aspect
    limit=max_height or (14.25 if landscape else 18.9)
    if h>limit:w=limit/aspect
    para=p('');para.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after=Pt(0);para.paragraph_format.keep_with_next=True
    para.add_run().add_picture(str(path),width=Cm(w))
    figure_no+=1
    cap=p(f'Hình {figure_no}  {caption}','Caption');cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
    # The image bytes in the DOCX are the original source bytes; no crops or painted text.
    used.append({'figure':figure_no,'key':key,'filename':path.name,'caption':caption,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
def table(headers,rows,widths):
    tab=doc.add_table(rows=1,cols=len(headers));tab.alignment=WD_TABLE_ALIGNMENT.CENTER;tab.autofit=False
    for i,(header,width) in enumerate(zip(headers,widths)):
        tab.columns[i].width=Cm(width);tab.rows[0].cells[i].text=header
    for row in rows:
        for cell,text in zip(tab.add_row().cells,row):cell.text=str(text)
    for ri,row in enumerate(tab.rows):
        for ci,cell in enumerate(row.cells):
            cell.width=Cm(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props=cell._tc.get_or_add_tcPr()
            edges=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                node=OxmlElement('w:'+edge);node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'D9D9D9');edges.append(node)
            props.append(edges)
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E5EDE7' if ri==0 else 'F6F7F5' if ri%2==0 else 'FFFFFF');props.append(shade)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                node=OxmlElement('w:'+edge);node.set(qn('w:w'),'80');node.set(qn('w:type'),'dxa');margins.append(node)
            props.append(margins)
            for para in cell.paragraphs:
                para.paragraph_format.space_after=Pt(3);para.paragraph_format.line_spacing=1.02
                for run in para.runs:run.font.size=Pt(10.5);run.bold=ri==0
            trpr=row._tr.get_or_add_trPr()
            if trpr.find(qn('w:cantSplit')) is None:trpr.append(OxmlElement('w:cantSplit'))
    tab.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    p('')
    return tab
def evidence_page(title,key,caption,text,wide=True):
    start_page(title,wide)
    description(text)
    picture(key,caption)

# 1. Subject, student identity and measured results.
p('BÁO CÁO THỰC HÀNH\nHỆ THỐNG E-COMMERCE MICROSERVICES','Title')
p('Bài kiểm tra TX2  |  Môn Java Web','Subtitle')
p('Họ và tên: '+student.name)
p('Mã sinh viên: '+student.student_id)
if student.class_name:p('Lớp: '+student.class_name)
p('Ngày thực hiện: 15 tháng 11 năm 2026')
doc.add_heading('1 Mục tiêu và phạm vi',level=1)
p('Bài thực hành xây dựng ứng dụng thương mại điện tử theo kiến trúc microservices bằng Spring Boot. Hệ thống gồm API Gateway, Product Service và Order Service; sử dụng REST cho client, gRPC để kiểm tra sản phẩm và Kafka để cập nhật tồn kho bất đồng bộ. Dữ liệu sản phẩm và đơn hàng được lưu bằng Spring Data JPA trong MySQL.')
table(['Phần đề','Nội dung triển khai'],[
    ('Câu 1','Gateway, REST, gRPC, MySQL/JPA; Docker Compose; cấu hình GitLab CI/CD và Minikube.'),
    ('Câu 2','Kafka producer/consumer, transactional outbox, xử lý sự kiện trùng và rolling update.')],[3,14])
doc.add_heading('Kết quả kiểm chứng',level=2)
table(['Phép kiểm tra','Kết quả ghi nhận'],[
    ('Build Maven','6 module SUCCESS; BUILD SUCCESS; thời gian 25.988 giây.'),
    ('Triển khai Kubernetes','6 pod Running; Product có 2 replica; PVC Kafka 1 GiB và MySQL 2 GiB đều Bound.'),
    ('Postman CLI','15 request, 24 assertion, không có lỗi assertion.'),
    ('Kiểm thử tích hợp','10/10 kiểm tra đạt, gồm luồng gRPC, Kafka và đặt hàng đồng thời.'),
    ('Rolling update','281 request đọc sản phẩm; 0 request lỗi; rolloutExitCode = 0.')],[4.4,12.6])
p('Các phần sau trình bày kiến trúc, ảnh terminal triển khai, giao diện ứng dụng và ảnh kiểm thử từng API trong Postman.')

# 2. Technical implementation tied to the code; avoids claiming unexecuted remote CI.
start_page('2 Kiến trúc và cách tổ chức hệ thống')
table(['Thành phần','Chức năng','Cổng nội bộ'],[
    ('api-gateway','Định tuyến /api/products/** và /api/orders/**; phục vụ giao diện web.','8080'),
    ('product-service','REST quản lý sản phẩm; gRPC server; Kafka consumer trừ tồn kho.','8081 và 9090'),
    ('order-service','REST quản lý đơn; gRPC client kiểm tra giá và tồn kho; xử lý kết quả cấp hàng.','8082'),
    ('mysql-db','Lưu product_db và order_db; tách dữ liệu sở hữu của hai service.','3306'),
    ('kafka','Broker KRaft cho topic order-events và stock-results.','9092 và 9093')],[4,10,3])
doc.add_heading('Luồng tạo đơn và cập nhật tồn kho',level=2)
p('Client gửi POST /api/orders qua Gateway. Order gọi GetProductById qua gRPC để lấy sản phẩm, giá và tồn kho. Nếu hợp lệ, Order lưu đơn PENDING cùng OrderCreatedEvent vào outbox trong một transaction MySQL; publisher chuyển sự kiện đến topic order-events.')
p('Product nhận sự kiện, khóa dòng sản phẩm, kiểm tra lại số lượng và trừ tồn kho. Bảng processed_orders khử trùng theo orderId. Kết quả được ghi vào outbox của Product và phát qua stock-results. Order tiếp nhận kết quả để chuyển sang CONFIRMED hoặc REJECTED.')
p('Giá và tổng tiền dùng BigDecimal, lưu bằng DECIMAL; proto truyền thêm price_decimal để tính tiền chính xác. Khi có nhiều đơn tranh hàng cuối, việc kiểm tra lại trong transaction quyết định đơn nào được cấp hàng và ngăn tồn kho âm.')
doc.add_heading('Môi trường và cách chạy',level=2)
p('Môi trường sử dụng Java 17, Maven, Spring Boot 3.5.4, Spring Cloud 2025.0.0, MySQL 8.0, Apache Kafka 3.9.1, Docker Compose và Minikube. Mã nguồn là Maven multi-module gồm proto, common, product-service, order-service và api-gateway.')
p('Docker Compose công bố Gateway tại localhost:18080. Trong các ảnh kiểm chứng dưới đây, ứng dụng chạy trên Minikube và được port-forward tại http://localhost:18081. Namespace triển khai là tx2-ecommerce. MySQL và Kafka sử dụng PVC để giữ dữ liệu qua vòng đời pod.')

# 3. Original terminal screenshots.
evidence_page('3 Build và đóng gói ứng dụng','2','Maven hoàn tất build toàn bộ module',
    'Chạy mvn -B clean verify -ntp tại thư mục code. Ảnh terminal cho thấy cả 6 module đều SUCCESS, Maven báo BUILD SUCCESS và tổng thời gian 25.988 giây. Các service được đóng gói thành JAR để đưa vào Docker image.')
evidence_page('4 Trạng thái triển khai trên Minikube','3','Minikube đang chạy cùng các Deployment Service và PVC',
    'Minikube báo host, kubelet và apiserver đều Running. Product Service đạt READY 2/2; Gateway, Order, Kafka và MySQL đều 1/1. Danh sách có 6 pod Running, không restart tại thời điểm chụp; PVC kafka-data 1 GiB và mysql-data 2 GiB đều Bound.')
start_page('5 Kiểm tra Gateway và luồng tích hợp',True)
description('Port-forward sử dụng cổng 18081. Endpoint /actuator/health trả status UP và công bố hai nhóm liveness, readiness.')
picture('4','Gateway phản hồi trạng thái UP qua địa chỉ localhost')
doc.add_heading('Kiểm thử tích hợp trên các dịch vụ thật',level=2)
description('verify-system.py hoàn thành 10/10 kiểm tra: tạo sản phẩm, tra cứu gRPC, tính tổng tiền, xác nhận qua Kafka, kiểm tra dữ liệu lỗi, thiếu hàng, sản phẩm không tồn tại, đặt hàng đồng thời và giới hạn phân trang.')
picture('6','Script tích hợp ghi nhận 10 checks passed')
evidence_page('6 Kiểm thử tự động bằng Postman CLI','5','Postman CLI hoàn tất 15 request và 24 assertion không lỗi',
    'Collection chạy qua Gateway Kubernetes tại localhost:18081. Bảng tổng kết ghi nhận 15 request, 24 assertion và 0 lỗi, thời gian 2.7 giây. Các phản hồi 400 và 404 ở ca kiểm thử lỗi là kết quả kỳ vọng. Thông báo đăng nhập chỉ liên quan việc xuất bản kết quả lên Postman cloud.')
evidence_page('7 Kafka xử lý đơn và bảo vệ tồn kho','7','Log Product ghi nhận cả đơn được cấp hàng và đơn bị từ chối',
    'Log InventoryService cho thấy các đơn 34, 35 và 36 của sản phẩm 14 được xử lý accepted=true, mỗi đơn mua 1 sản phẩm. Các đơn tiếp theo bị accepted=false khi hàng không còn đủ. Kết quả JSON cùng lần kiểm thử ghi nhận 12 yêu cầu đồng thời, 3 đơn xác nhận, 9 đơn bị từ chối và tồn kho cuối bằng 0.')
evidence_page('8 Kiểm chứng rolling update','8','Rolling update Product hoàn tất với 281 request không lỗi',
    'test-rolling-update.py liên tục gọi GET /api/products/1 khi thay lần lượt hai Product pod. Ảnh ghi nhận totalRequests = 281, failedRequests = 0 và rolloutExitCode = 0. Deployment dùng maxSurge 1, maxUnavailable 0; kết quả này áp dụng cho các request đọc đã quan sát trong lần thử.')

# 4. Original browser screenshots, kept at their original aspect ratio.
evidence_page('9 Giao diện danh sách sản phẩm','products','Giao diện sản phẩm và thao tác chọn số lượng đặt hàng',
    'Trang web hiển thị đúng tên HỆ THỐNG E-COMMERCE MICROSERVICES. Mỗi thẻ sản phẩm gồm tên, giá, mã và tồn kho, ô nhập số lượng và nút Đặt hàng. Trong ảnh, Laptop Java Developer có giá 15.000.000 đồng, còn 17 sản phẩm; các sản phẩm hết hàng có nút đặt bị vô hiệu hóa.',False)
evidence_page('10 Giao diện theo dõi đơn hàng','orders','Bảng đơn hàng hiển thị kết quả xác nhận và từ chối cấp hàng',
    'Bảng Đơn hàng gần đây hiển thị mã đơn, sản phẩm, số lượng, thành tiền và trạng thái. Đơn 31 mua Laptop Java Developer với số lượng 1 và thành tiền 15.000.000 đồng ở trạng thái Đã xác nhận. Các dòng Không đủ tồn kho phản ánh những đơn bị từ chối khi xử lý cấp hàng.',False)

# 5. Original Postman screenshots. J03 is intentionally never included.
evidence_page('11 Cấu hình collection kiểm thử API','J13','Collection sử dụng baseUrl productId và orderId',
    'Collection HỆ THỐNG E-COMMERCE MICROSERVICES sử dụng baseUrl = http://localhost:18081. Hai biến productId = 15 và orderId = 46 được dùng trong chuỗi tạo đơn được trình bày phía sau. Postman đang chọn No Environment để sử dụng trực tiếp biến của collection.')
evidence_page('12 API lấy danh sách sản phẩm','J01','GET danh sách sản phẩm trả 200 OK',
    'Gửi GET {{baseUrl}}/api/products. Hệ thống trả 200 OK, Test Results 1/1 và mảng JSON sản phẩm. Phần phản hồi nhìn thấy Laptop Java Developer ID 1, giá 15.000.000, tồn kho 17; bàn phím ID 2 và chuột ID 3 cũng có trong danh sách.')
evidence_page('13 API tạo sản phẩm demo','J02','POST sản phẩm trả 201 Created với ID 15',
    'Body gửi tên San pham demo Postman, price = 250000 và stock = 10. POST /api/products trả 201 Created, Test Results 2/2 và sản phẩm ID 15 đúng dữ liệu đầu vào. Bản ghi này là dữ liệu ban đầu để đối chiếu việc trừ kho sau khi đặt đơn.')
evidence_page('14 API tra cứu một sản phẩm','J14','GET chi tiết sản phẩm thành công với ID 16',
    'Gửi GET {{baseUrl}}/api/products/{{productId}}. Ở lần tra cứu độc lập này, phản hồi là sản phẩm ID 16, tên San pham demo Postman, giá 250000 và stock = 10; HTTP 200 OK và Test Results 2/2. Chuỗi tạo đơn ở các trang tiếp theo sử dụng sản phẩm ID 15.')
evidence_page('15 API tiếp nhận đơn hàng','J04','POST đơn hàng trả 201 Created và trạng thái PENDING',
    'POST /api/orders tạo đơn ID 46 cho sản phẩm ID 15, số lượng 2. Phản hồi có unitPrice = 250000.00, totalPrice = 500000.00, status = PENDING và reason = null; Test Results 3/3. HTTP 201 thể hiện đơn đã được tiếp nhận, còn bước cấp hàng được xử lý qua Kafka.')
evidence_page('16 API xác nhận kết quả cấp hàng','J05','Đơn ID 46 chuyển từ PENDING sang CONFIRMED',
    'Gọi GET /api/orders/{{orderId}} để đọc lại đơn ID 46. HTTP 200 OK, Test Results 2/2; sản phẩm vẫn là ID 15, số lượng 2, tổng tiền 500000.00. Trạng thái chuyển sang CONFIRMED và reason = Stock deducted, cho thấy luồng xử lý cấp hàng đã hoàn tất.')
evidence_page('17 API kiểm tra tồn kho sau Kafka','J06','Sản phẩm ID 15 còn 8 đơn vị sau đơn hàng mua 2',
    'GET /api/products/{{productId}} trả 200 OK và sản phẩm ID 15 với stock = 8, Test Results 2/2. So với tồn kho 10 lúc tạo sản phẩm và số lượng 2 trong đơn ID 46, kết quả khớp phép tính 10 − 2 = 8. Giá sản phẩm vẫn là 250000.00.')
evidence_page('18 API từ chối số lượng không hợp lệ','J07','Số lượng bằng 0 bị từ chối với HTTP 400',
    'Ca kiểm thử gửi yêu cầu tạo đơn với quantity = 0. API trả 400 Bad Request và thông báo quantity: must be greater than or equal to 1; Test Results 1/1. Đây là phản hồi kiểm tra dữ liệu đầu vào của OrderInput, yêu cầu số lượng tối thiểu là 1.')
evidence_page('19 API từ chối đơn vượt tồn kho','J08','Yêu cầu mua vượt tồn kho trả HTTP 409',
    'Ca kiểm thử gửi số lượng 99 cho sản phẩm demo. API trả 409 Conflict, message = Insufficient stock, path = /api/orders và Test Results 1/1. Hệ thống từ chối yêu cầu tại bước kiểm tra tồn kho trước khi lưu đơn mới.')
evidence_page('20 API xử lý sản phẩm không tồn tại','J09','Tra cứu sản phẩm không tồn tại khi đặt đơn trả HTTP 404',
    'Yêu cầu POST /api/orders sử dụng mã sản phẩm không tồn tại. Phản hồi là 404 Not Found, message = Product not found và Test Results 1/1. Kết quả cho thấy lỗi NOT_FOUND từ bước tra cứu gRPC được ánh xạ thành phản hồi REST phù hợp.')
evidence_page('21 API xem danh sách đơn hàng','J10','Danh sách đơn trả HTTP 200 và chứa đơn ID 46',
    'GET /api/orders trả 200 OK, Test Results 1/1 và mảng đơn hàng. Bản ghi đầu ảnh là đơn ID 46, sản phẩm ID 15, số lượng 2, tổng tiền 500000.00, status = CONFIRMED. Bản ghi kế tiếp có status = REJECTED với lý do không đủ hàng tại thời điểm cấp hàng.')
evidence_page('22 API cập nhật sản phẩm','J11','PUT sản phẩm ID 15 cập nhật giá và tồn kho thành công',
    'PUT /api/products/{{productId}} gửi tên San pham demo da cap nhat, giá 300000 và stock = 20. API trả 200 OK, Test Results 3/3; phản hồi giữ ID 15 và thể hiện đúng tên, giá, tồn kho mới. Thao tác này được thực hiện sau phép kiểm tra tồn kho 8 ở chuỗi đặt hàng.')
evidence_page('23 API xóa sản phẩm demo','J12','DELETE sản phẩm demo trả HTTP 204 No Content',
    'DELETE /api/products/{{productId}} dọn sản phẩm demo sau kiểm thử. Phản hồi 204 No Content, Test Results 1/1 và body trống là hành vi đúng của API xóa thành công. Đơn hàng giữ thông tin sản phẩm và đơn giá đã chụp tại thời điểm đặt.')

# 6. Summary and honest delivery boundary for CI/CD.
start_page('24 Đánh giá và hồ sơ bàn giao')
p('Các ảnh kiểm chứng thể hiện hệ thống đã build thành công, triển khai trên Minikube, phục vụ giao diện web và xử lý API qua Gateway. Chuỗi sản phẩm ID 15 và đơn ID 46 cho thấy sự chuyển trạng thái PENDING sang CONFIRMED, tổng tiền 500000.00 và tồn kho giảm đúng từ 10 xuống 8.')
table(['Nội dung','Kết quả'],[
    ('REST và Gateway','Các API đọc, tạo, sửa, xóa phản hồi đúng mã HTTP trong các ảnh Postman.'),
    ('gRPC','Đơn hợp lệ lấy được thông tin và đơn giá sản phẩm; mã không tồn tại được phản hồi 404.'),
    ('Kafka và tồn kho','Đơn được xác nhận sau xử lý bất đồng bộ; ca đặt hàng đồng thời giữ tồn kho không âm.'),
    ('Kubernetes','Các Deployment sẵn sàng, Product có 2 replica; MySQL và Kafka có PVC Bound.'),
    ('Rolling update','281 request đọc được quan sát, không có request lỗi trong lần cập nhật.'),
    ('GitLab CI/CD','Đã cấu hình pipeline build, push image theo commit SHA và deploy. Chưa có minh chứng pipeline GitLab chạy từ xa.')],[4,13])
doc.add_heading('Cấu hình CI CD và giới hạn kiểm chứng',level=2)
p('File .gitlab-ci.yml gồm ba stage build, images và deploy. Build chạy Maven verify; images build và đẩy image vào GitLab Container Registry theo CI_COMMIT_SHA; deploy dùng Windows shell runner có tag minikube-windows để truy cập cụm local. Cần cấu hình repository, runner và deploy token read_registry trước khi chạy pipeline từ xa. Các ảnh trong báo cáo xác nhận triển khai và rolling update tại Minikube local.')
p('Bản thực hành dùng một MySQL và một Kafka broker, chưa có xác thực hoặc thanh toán. Outbox và consumer khử trùng bảo vệ luồng sự kiện; HTTP tạo đơn chưa có Idempotency-Key. Kết quả rolling update là bằng chứng cho phép thử đọc đã thực hiện, không phải cam kết không gián đoạn cho mọi loại sự cố.')
doc.add_heading('Tệp bàn giao',level=2)
p('baocao.docx chứa ảnh terminal, giao diện và Postman. Thư mục code chứa mã nguồn, Docker Compose, k8s, .gitlab-ci.yml, bộ Postman và database/backup.sql. Hướng dẫn chạy nằm tại code/README.md. Hồ sơ được đóng gói thành GIANGSEOCHINH_2023602847.RAR.')

doc.core_properties.title='Báo cáo thực hành HỆ THỐNG E-COMMERCE MICROSERVICES'
doc.core_properties.subject='TX2 Java Web với ảnh chụp terminal và Postman thực tế'
doc.core_properties.author=student.name
target=root/'baocao.docx'
backup=code/'tmp/baocao-truoc-khi-chen-anh-thuc-te.docx'
backup.parent.mkdir(exist_ok=True)
if target.exists() and not backup.exists():shutil.copy2(target,backup)
doc.save(target)
assert len(used)==22 and all(row['key']!='J03' for row in used)
manifest={'report':'baocao.docx','student':{'name':student.name,'id':student.student_id},
    'included':used,'excluded':[{'key':'J03','filename':sources['J03'].name,'reason':'Ảnh API 03 trả 405, loại khỏi báo cáo theo yêu cầu.'}],
    'facts':{'postmanRequests':15,'postmanAssertions':24,'postmanFailedAssertions':0,'integrationPassed':10,'integrationTotal':10,'rollingRequests':281,'rollingFailed':0,'productId':15,'orderId':46,'initialStock':10,'finalStock':8,'independentLookupProductId':16}}
(code/'evidence/report-screenshots.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Created {target} with {len(used)} original screenshots; excluded API 03 error')
