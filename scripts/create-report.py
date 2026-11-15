"""Create ../baocao.docx from saved, real test evidence.
Run using the Codex bundled Python (python-docx + Pillow).
Figures are explicitly log/evidence exports, not simulated UI screenshots.
"""
from pathlib import Path
import argparse, json, re, textwrap
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

parser=argparse.ArgumentParser()
parser.add_argument('--name',default='')
parser.add_argument('--student-id',default='')
parser.add_argument('--class-name',default='')
student=parser.parse_args()
root=Path(__file__).resolve().parents[1]
figures=root/'evidence/figures'; figures.mkdir(parents=True,exist_ok=True)
def read(path):
    data=(root/path).read_bytes()
    return data.decode('utf-16') if data.startswith((b'\xff\xfe',b'\xfe\xff')) else data.decode('utf-8-sig',errors='replace')
system=json.loads(read('evidence/system-tests.json'))
kube=json.loads(read('evidence/kubernetes-tests.json'))
rolling=json.loads(read('evidence/rolling-update.json'))
postman=read('evidence/postman-cli.txt')
postman_kube=read('evidence/postman-kubernetes.txt')
def count_assertions(log):
    m=re.search(r'\|\s*assertions\s*\|\s*(\d+)\s*\|\s*(\d+)',log)
    return tuple(map(int,m.groups())) if m else (0,0)
assertions=count_assertions(postman)
kube_assertions=count_assertions(postman_kube)
font_dir=Path('C:/Windows/Fonts')
def font(size,bold=False,mono=False):
    path=font_dir/('consola.ttf' if mono else 'arialbd.ttf' if bold else 'arial.ttf')
    return ImageFont.truetype(str(path),size)
def log_image(name,title,lines):
    expanded=[]
    for line in lines:
        expanded.extend(textwrap.wrap(line,width=98,replace_whitespace=False,drop_whitespace=False) or [''])
    im=Image.new('RGB',(1320,110+len(expanded)*33),'#f5f7f4'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,1320,72),fill='#173f35'); d.text((28,19),title,font=font(28,True),fill='white')
    for i,line in enumerate(expanded): d.text((28,92+i*33),line,font=font(22,mono=True),fill='#182d25')
    im.save(figures/name)

maven=[line for line in read('evidence/maven-build.txt').splitlines() if any(key in line for key in ['Tests run: 3, Failures','Tests run: 1, Failures','BUILD SUCCESS','Total time:','ecommerce-microservices ....','proto ....','common ....','product-service ....','order-service ....','api-gateway ....'])]
log_image('maven.png','Maven verify — kết quả từ log build',maven[-14:])
postman_lines=['Target: http://localhost:18080',f'Assertions: {assertions[0]} | Failed: {assertions[1]}','Process exit code: '+read('evidence/postman-exit-code.txt').strip(),'']
postman_lines += [line.strip() for line in postman.splitlines() if re.match(r'(GET|POST|PUT|DELETE) http',line.strip())][:18]
log_image('postman.png','Postman CLI — request và assertion thực tế',postman_lines)
system_lines=[('PASS ' if r['passed'] else 'FAIL ')+r['name'] for r in system['results']]
log_image('system.png','Kiểm thử tích hợp và phục hồi — dịch vụ thật',system_lines+[f"TOTAL: {system['passed']}/{system['total']} passed"])
pods=read('evidence/kubernetes-pods.txt').splitlines()
log_image('kubernetes.png','Minikube — trạng thái pod sau triển khai',pods)
log_image('rolling.png','Rolling update — kết quả request liên tục',[
    'Product Service: 2 replicas',rolling['strategy'],f"Requests during update: {rolling['totalRequests']}",
    f"Failed requests: {rolling['failedRequests']}",f"Rollout exit code: {rolling['rolloutExitCode']}",
    *rolling['rolloutOutput'].strip().splitlines()])

# A small architecture figure authored from the implemented service wiring.
im=Image.new('RGB',(1320,770),'white'); d=ImageDraw.Draw(im)
def box(x,y,w,h,title,subtitle=''):
    d.rounded_rectangle((x,y,x+w,y+h),radius=14,fill='#eff4ee',outline='#7a9482',width=2)
    d.text((x+w/2,y+25),title,anchor='mm',font=font(25,True),fill='#173f35')
    if subtitle:d.text((x+w/2,y+62),subtitle,anchor='mm',font=font(21),fill='#4e6656')
def arrow(a,b,label='',offset=(0,0)):
    import math
    d.line((a,b),fill='#4d7563',width=3)
    angle=math.atan2(b[1]-a[1],b[0]-a[0])
    tip=[b,(b[0]-16*math.cos(angle-.45),b[1]-16*math.sin(angle-.45)),(b[0]-16*math.cos(angle+.45),b[1]-16*math.sin(angle+.45))]
    d.polygon(tip,fill='#4d7563')
    if label:d.text(((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1]),label,anchor='mm',font=font(21),fill='#334e40')
box(480,15,360,82,'Browser / Postman','REST HTTP')
box(480,140,360,82,'API Gateway','Spring Cloud Gateway')
box(90,325,360,88,'Order Service','REST + gRPC client')
box(870,325,360,88,'Product Service','REST + gRPC server')
box(90,505,360,88,'order_db','orders + outbox_messages')
box(870,505,360,88,'product_db','products + processed_orders')
box(480,655,360,88,'Apache Kafka','order-events / stock-results')
arrow((660,97),(660,140))
arrow((540,222),(270,325),'REST',(-40,-5))
arrow((780,222),(1050,325),'REST',(35,-5))
arrow((450,369),(870,369),'gRPC GetProductById',(0,-25))
arrow((270,413),(270,505),'JPA',(45,0))
arrow((1050,413),(1050,505),'JPA',(45,0))
arrow((450,549),(510,655),'outbox',(-20,5))
arrow((840,686),(1020,593),'consume',(-10,0))
arrow((870,560),(810,655),'outbox',(40,0))
arrow((480,700),(180,593),'result',(0,20))
im.save(figures/'architecture.png')

doc=Document(); section=doc.sections[0]
section.page_width=Cm(21); section.page_height=Cm(29.7)
section.top_margin=Cm(1.7); section.bottom_margin=Cm(1.7)
section.left_margin=Cm(2.2); section.right_margin=Cm(1.8)
styles=doc.styles
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
    st=styles[name]; st.font.name='Times New Roman'; st.font.color.rgb=RGBColor(0,0,0)
    st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Times New Roman')
styles['Normal'].font.size=Pt(12)
styles['Normal'].paragraph_format.line_spacing=1.12
styles['Normal'].paragraph_format.space_after=Pt(6)
styles['Title'].font.size=Pt(23); styles['Title'].font.bold=True
styles['Heading 1'].font.size=Pt(16); styles['Heading 1'].paragraph_format.space_before=Pt(7)
styles['Heading 2'].font.size=Pt(13); styles['Caption'].font.size=Pt(10)
footer=section.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('TX2 Java Web  |  Trang ')
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); footer._p.append(field)
def p(text,style=None):return doc.add_paragraph(text,style)
def heading(text):doc.add_heading(text,level=1)
def page():doc.add_page_break()
def picture(name,caption):
    para=doc.add_paragraph(); para.paragraph_format.keep_with_next=True
    para.add_run().add_picture(str(figures/name),width=Cm(16.7))
    cap=p(caption,'Caption'); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER
def table(headers,rows,widths=None):
    t=doc.add_table(rows=1,cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    if widths:
        for c,w in zip(t.columns,widths): c.width=Cm(w)
    for c,label in zip(t.rows[0].cells,headers):c.text=label
    for row in rows:
        for c,text in zip(t.add_row().cells,row):c.text=str(text)
    for ri,row in enumerate(t.rows):
        for ci,c in enumerate(row.cells):
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if widths:c.width=Cm(widths[ci])
            tcPr=c._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                el=OxmlElement('w:'+edge); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'4'); el.set(qn('w:color'),'D9D9D9'); borders.append(el)
            tcPr.append(borders)
            shade=OxmlElement('w:shd'); shade.set(qn('w:fill'),'E5EDE7' if ri==0 else 'F6F7F5' if ri%2==0 else 'FFFFFF'); tcPr.append(shade)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                el=OxmlElement('w:'+edge); el.set(qn('w:w'),'85'); el.set(qn('w:type'),'dxa'); margins.append(el)
            tcPr.append(margins)
            for para in c.paragraphs:
                para.paragraph_format.space_after=Pt(3); para.paragraph_format.line_spacing=1.02
                for run in para.runs:run.font.size=Pt(10.5); run.bold=ri==0
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    p('')
    return t
def code(text):
    para=p(text)
    for run in para.runs:run.font.name='Consolas';run.font.size=Pt(9)

p('Báo cáo xây dựng hệ thống\nthương mại điện tử microservices','Title')
p('Bài kiểm tra thực hành TX2  |  Môn Java Web','Subtitle')
p('Họ và tên: '+(student.name or '........................................................................'))
p('Mã sinh viên: '+(student.student_id or '..................................')+'  Lớp: '+(student.class_name or '..................................'))
p('Ngày thực hiện kiểm chứng: 15 tháng 11 năm 2026')
heading('1 Mục tiêu và kết quả')
p('Hệ thống triển khai ba thành phần API Gateway, Product Service và Order Service. Client gọi REST qua Gateway; Order kiểm tra sản phẩm bằng gRPC và phát sự kiện Kafka để Product cập nhật tồn kho. Dữ liệu được lưu trong hai database MySQL riêng.')
p(f"Maven verify hoàn thành 7 kiểm thử Java. Docker Compose vượt qua {system['passed']}/{system['total']} kiểm tra tích hợp và phục hồi. Kubernetes vượt qua {kube['passed']}/{kube['total']} kiểm tra hệ thống; rolling update hoàn tất với {rolling['totalRequests']} request đọc sản phẩm và {rolling['failedRequests']} request lỗi trong lần quan sát.")
table(['Phần đề','Nội dung thực hiện'],[
    ('Câu 1  5 điểm','Spring Boot, Gateway, REST, gRPC, JPA/MySQL; Docker Compose; manifest Kubernetes và pipeline GitLab CI/CD.'),
    ('Câu 2  5 điểm','Kafka producer/consumer, trừ tồn kho bất đồng bộ, outbox, xử lý trùng sự kiện, rolling update.'),
    ('Hồ sơ','Mã nguồn trong code; SQL tại code/database; báo cáo Word và các tệp minh chứng trong code/evidence.')],[3,13.7])
heading('Môi trường sử dụng')
p('Windows 11; JDK 17.0.18; Maven 3.9.14; Spring Boot 3.5.4; Spring Cloud 2025.0.0; gRPC Spring starter 3.1.0.RELEASE; Kafka 3.9.1; MySQL 8.0; Docker Compose và Minikube. Broker chạy KRaft nên không cần ZooKeeper.')

page(); heading('2 Kiến trúc và luồng xử lý')
picture('architecture.png','Hình 1  Kiến trúc triển khai và hai hướng trao đổi sự kiện')
p('Gateway định tuyến /api/products/** đến Product và /api/orders/** đến Order. Product phục vụ cả REST ở cổng 8081 và gRPC ở cổng 9090. Order phục vụ REST ở cổng 8082. Hai service truy cập product_db và order_db qua Spring Data JPA.')
p('Khi tạo đơn, Order gọi GetProductById, kiểm tra số lượng và chụp lại giá sản phẩm. Nếu hợp lệ, đơn PENDING và sự kiện OrderCreatedEvent được ghi trong cùng transaction. Publisher chuyển sự kiện từ outbox sang topic order-events. Product tiếp nhận, khóa dòng sản phẩm, kiểm tra lại tồn kho rồi ghi kết quả vào stock-results thông qua outbox của mình.')
p('Order nhận kết quả và chuyển trạng thái thành CONFIRMED hoặc REJECTED. HTTP 201 biểu thị đã tiếp nhận đơn, chưa đảm bảo đã cấp hàng. Điều này cho phép giải quyết trường hợp nhiều đơn đồng thời tranh lượng hàng cuối mà không làm tồn kho âm.')
table(['Cơ chế','Mục đích'],[
    ('Outbox trong MySQL','Đơn và sự kiện cùng commit; broker ngừng hoạt động thì sự kiện vẫn còn để gửi lại.'),
    ('processed_orders','Khử trùng theo orderId; nhận lại cùng sự kiện không trừ kho lần hai.'),
    ('Khóa dòng sản phẩm','Bảo vệ tồn kho khi xử lý đồng thời hoặc khi chạy nhiều replica.'),
    ('BigDecimal và DECIMAL','Tính tổng tiền chính xác; gRPC truyền thêm price_decimal.')],[4.2,12.5])

page(); heading('3 Cài đặt và chạy ứng dụng')
p('Tại thư mục code, chạy Maven verify để biên dịch các module và sinh Java stub từ proto/product.proto. Dockerfile đóng gói từng JAR vào image chạy Java 17. Compose tạo MySQL, Kafka, Product, Order và Gateway trong cùng mạng nội bộ.')
code('mvn -B clean verify -ntp\ndocker compose up -d --build --wait --wait-timeout 300')
p('Gateway của Compose dùng http://localhost:18080. MySQL Docker dùng cổng 3310 để tránh MySQL Windows đang chạy tại 3306. Các cổng publish chỉ nhận kết nối từ 127.0.0.1. Giao diện đặt hàng được phục vụ ở trang chủ Gateway.')
picture('maven.png','Hình 2  Trích xuất log Maven verify thực tế')
table(['Module','Vai trò'],[
    ('proto','Khai báo và sinh contract gRPC dùng chung.'),('common','DTO sự kiện, xử lý lỗi REST, cấu trúc và publisher outbox.'),
    ('product-service','Quản lý sản phẩm; gRPC server; Kafka consumer và outbox kết quả.'),
    ('order-service','Tạo và xem đơn; gRPC client; nhận kết quả cấp hàng.'),('api-gateway','Định tuyến REST và cung cấp giao diện đặt hàng.')],[4.1,12.6])
p('Bảy kiểm thử Java dùng H2 và mock client để kiểm tra transaction, giá tiền, thiếu tồn kho và xử lý lặp. Việc giao tiếp với MySQL, gRPC và Kafka thật được kiểm chứng riêng bằng các bước tích hợp ở phần sau.')

page(); heading('4 Kiểm thử API bằng Postman')
p('Collection tại code/postman/tx2.postman_collection.json lưu các request, biến và assertion. Chuỗi request tạo sản phẩm thử, sửa thông tin, kiểm tra dữ liệu sai, đặt đơn, đợi xác nhận Kafka, kiểm tra tồn kho và xóa sản phẩm thử. Mỗi lần chạy dùng sản phẩm riêng; đơn thử được giữ trong database.')
code('postman collection run postman/tx2.postman_collection.json --no-report-events')
picture('postman.png','Hình 3  Kết quả request và assertion xuất từ log Postman CLI')
p(f"Lần chạy Compose ghi nhận {assertions[0]} assertion, {assertions[1]} lỗi, exit code 0. Lần chạy qua Gateway Kubernetes ghi nhận {kube_assertions[0]} assertion, {kube_assertions[1]} lỗi. Số request có thể tăng khi collection lặp bước chờ xác nhận bất đồng bộ.")
table(['Tình huống','HTTP hoặc kết quả kỳ vọng'],[
    ('Tạo sản phẩm hợp lệ','201'),('Số lượng bằng 0 hoặc dữ liệu sản phẩm sai','400'),('Sản phẩm không tồn tại qua gRPC','404'),
    ('Số lượng vượt tồn kho','409'),('Product không kết nối được','503'),('Đặt 3 sản phẩm giá 19.95','Tổng 59.85; tồn kho từ 10 xuống 7 sau Kafka')],[9.2,7.5])

page(); heading('5 Kiểm thử đồng thời và phục hồi')
p('Script code/scripts/verify-system.py gọi trực tiếp Gateway và kiểm tra trạng thái database thông qua API. Chế độ --resilience tạm dừng Kafka hoặc Product của riêng Compose project rồi khởi động lại. Toàn bộ kết quả được lưu tại evidence/system-tests.json.')
picture('system.png','Hình 4  Kết quả từ 14 kiểm tra trên các dịch vụ chạy thật')
concurrency=next(r['details'] for r in system['results'] if r['name'].startswith('12 concurrent'))
p(f"Thử nghiệm đồng thời gửi 12 yêu cầu mua sản phẩm có tồn kho 3. Kết quả có {concurrency['confirmed']} đơn CONFIRMED, {concurrency['rejectedAsync']} đơn bị từ chối bất đồng bộ và tồn kho cuối bằng {concurrency['stock']}. Các yêu cầu bị từ chối ngay trả HTTP 409.")
p('Thử phát lại hai bản sao của cùng sự kiện xác nhận consumer group đã bắt kịp log, trong khi tồn kho không giảm thêm. Khi Kafka dừng, đơn mới vẫn được tiếp nhận ở trạng thái PENDING; sau khi broker khởi động lại, outbox được gửi và đơn chuyển sang CONFIRMED. Khi Product dừng, Order trả HTTP 503 thay vì treo vô thời hạn.')

page(); heading('6 Triển khai và cập nhật trên Kubernetes')
p('Các manifest trong code/k8s triển khai vào namespace tx2-ecommerce, gồm Secret demo, ConfigMap khởi tạo MySQL, PVC và Service/Deployment cho từng thành phần. Minikube nạp image được build trên máy. Kafka dùng voter localhost cho broker và controller cùng pod để tránh phụ thuộc vào endpoint chưa Ready trong quá trình khởi động.')
code('powershell -ExecutionPolicy Bypass -File scripts/deploy-minikube.ps1\nminikube kubectl -- -n tx2-ecommerce port-forward service/api-gateway 18081:8080')
picture('kubernetes.png','Hình 5  Trạng thái pod lấy từ kubectl sau khi hoàn tất triển khai')
p(f"API Kubernetes tại http://localhost:18081 vượt qua {kube['passed']}/{kube['total']} kiểm tra hệ thống, gồm luồng gRPC, Kafka và đặt hàng đồng thời với hai Product replica. Kết quả lưu tại evidence/kubernetes-tests.json.")
picture('rolling.png','Hình 6  Kết quả kiểm tra REST trong lúc rolling update Product')
p('RollingUpdate dùng maxSurge 1 và maxUnavailable 0, kết hợp probes và graceful shutdown. Script theo dõi GET /api/products/1 mỗi khoảng 250 ms trong lúc khởi động lại lần lượt hai Product pod. Kết quả trên chứng minh các request đọc đã quan sát trong lần thử; chưa phải bảo đảm mọi loại request đều không lỗi trong mọi sự cố.')

page(); heading('7 Pipeline và hồ sơ bàn giao')
p('File .gitlab-ci.yml cấu hình ba stage. Build chạy Maven verify và xuất JUnit report. Images dùng Docker-in-Docker để build và push ba image vào GitLab Container Registry với tag CI_COMMIT_SHA. Deploy chạy trên Windows shell runner có tag minikube-windows và quyền truy cập cụm Minikube của người dùng.')
p('Script ci-deploy.ps1 tạo imagePullSecret từ deploy token read_registry, thay tag image theo commit và theo dõi rollout status. Cần thiết lập REGISTRY_PULL_USER, REGISTRY_PULL_PASSWORD, bật Container Registry và đăng ký runner đúng tài khoản Windows. Chưa có URL repository hoặc quyền GitLab nên pipeline remote chưa được thực thi; kết quả triển khai và rolling update được kiểm chứng ở Minikube local.')
table(['Thành phần bàn giao','Vị trí'],[
    ('Đề bài','TX2.pdf'),('Báo cáo','baocao.docx'),('Mã nguồn và hướng dẫn','code/ và code/README.md'),
    ('CSDL cấu trúc và dữ liệu','code/database/backup.sql'),('Khởi tạo database','code/database/init.sql'),
    ('Postman','code/postman/'),('Kubernetes và CI/CD','code/k8s/ và code/.gitlab-ci.yml'),('Kết quả kiểm chứng','code/evidence/')],[7,9.7])
heading('Phạm vi và giới hạn')
p('Bản thực hành chưa có xác thực, phân quyền hoặc thanh toán. Mật khẩu cấu hình sẵn chỉ dùng ở môi trường học tập. MySQL và Kafka có một replica nên không cung cấp HA cho tầng dữ liệu. HTTP tạo đơn chưa có Idempotency-Key, vì vậy gửi lại POST có thể tạo thêm đơn; cơ chế khử trùng hiện áp dụng cho sự kiện Kafka.')
p('Ảnh trong báo cáo là sơ đồ kiến trúc và hình xuất trực tiếp từ các tệp log hoặc JSON kiểm chứng, với tên nguồn được ghi tại chú thích. Các tệp log gốc được bàn giao cùng mã nguồn để đối chiếu.')
heading('Tài liệu tham khảo')
p('1. Đề thực hành TX2.pdf do giảng viên cung cấp.')
p('2. Spring Cloud và bảng tương thích: https://spring.io/projects/spring-cloud/')
p('3. gRPC Spring Boot starter: https://grpc-ecosystem.github.io/grpc-spring/')
p('4. Apache Kafka Docker: https://kafka.apache.org/39/getting-started/docker/')

doc.core_properties.title='Báo cáo xây dựng hệ thống thương mại điện tử microservices'
doc.core_properties.subject='Bài kiểm tra thực hành TX2 Java Web'
doc.core_properties.author=student.name
target=root.parent/'baocao.docx'; doc.save(target)
print(f'Created {target}')
