"""Generate manual Postman requests and equivalent cURL commands for real screenshots."""
from pathlib import Path
import json, shlex

root=Path(__file__).resolve().parents[1]
base='http://localhost:18081'
rows=[
    ('01 Danh sách sản phẩm','GET','/api/products',None,200,'Danh sách sản phẩm hiện có.'),
    ('02 Tạo sản phẩm demo','POST','/api/products',{'name':'San pham demo Postman','price':250000,'stock':10},201,'Ghi lại id sản phẩm trả về. Collection tự lưu productId.'),
    ('03 Xem sản phẩm trước khi đặt','GET','/api/products/{{productId}}',None,200,'Tồn kho stock = 10.'),
    ('04 Tạo đơn hàng','POST','/api/orders',{'productId':'{{productId}}','quantity':2},201,'Bấm Send một lần. totalPrice = 500000; ban đầu status = PENDING. Collection tự lưu orderId.'),
    ('05 Kiểm tra xác nhận đơn','GET','/api/orders/{{orderId}}',None,200,'Đợi khoảng 2 giây sau bước 04. Nếu còn PENDING, bấm Send lại đến CONFIRMED.'),
    ('06 Kiểm tra tồn kho sau Kafka','GET','/api/products/{{productId}}',None,200,'Sau khi đơn CONFIRMED, stock = 8. Đây là bằng chứng cập nhật tồn kho bất đồng bộ.'),
    ('07 Lỗi số lượng bằng không','POST','/api/orders',{'productId':'{{productId}}','quantity':0},400,'Dữ liệu sai phải trả 400 Bad Request.'),
    ('08 Lỗi vượt tồn kho','POST','/api/orders',{'productId':'{{productId}}','quantity':99},409,'Thiếu tồn kho phải trả 409 Conflict.'),
    ('09 Lỗi sản phẩm không tồn tại','POST','/api/orders',{'productId':9223372036854775807,'quantity':1},404,'gRPC NOT_FOUND được chuyển thành REST 404.'),
    ('10 Xem danh sách đơn','GET','/api/orders',None,200,'Danh sách đơn, gồm đơn demo vừa tạo.'),
    ('11 Cập nhật sản phẩm demo','PUT','/api/products/{{productId}}',{'name':'San pham demo da cap nhat','price':300000,'stock':20},200,'Chỉ chạy sau khi chụp bước 06. Giá 300000, tồn kho 20.'),
    ('12 Xóa sản phẩm demo','DELETE','/api/products/{{productId}}',None,204,'Tùy chọn dọn dữ liệu sau khi chụp đủ ảnh. Body trống với HTTP 204 là đúng.'),
]
items=[]
markdown=['# API dùng để chụp ảnh Postman','',
    'Các lệnh cURL bên dưới dùng để dán vào Postman, không chạy trong PowerShell.',
    'Chọn Import, dán nguyên một lệnh cURL rồi Import và Send. Chạy theo thứ tự.',
    'Cách thuận tiện hơn: import `chup-anh.postman_collection.json`; collection tự lưu productId và orderId.',
    '', 'Nếu chỉ import từng lệnh cURL, thay `{{productId}}` bằng id từ bước 02 và `{{orderId}}` bằng id từ bước 04 trước khi gửi.',
    'Không tự điền một ID ví dụ cố định vì mỗi lần chạy database có thể trả ID khác nhau.',
    '', 'Chụp cả method, URL, Body (với POST/PUT), HTTP status và JSON response. Lưu ảnh ở thư mục gốc tx2 theo yêu cầu.',
    'Sau bước 04 chỉ chụp trạng thái PENDING; bước 05 chụp CONFIRMED; bước 06 chụp stock giảm từ 10 xuống 8.',
    'Bấm Send bước tạo đơn một lần. Muốn chạy lại cả chuỗi, bắt đầu từ bước 02 để tạo sản phẩm mới.', '']
for index,(name,method,path,body,status,description) in enumerate(rows,1):
    request={'method':method,'header':[],'url':'{{baseUrl}}'+path,'description':description}
    raw=None
    if body is not None:
        raw=json.dumps(body,ensure_ascii=False).replace('"{{productId}}"','{{productId}}')
        request['header']=[{'key':'Content-Type','value':'application/json'}]
        request['body']={'mode':'raw','raw':raw,'options':{'raw':{'language':'json'}}}
    tests=[f'pm.test("HTTP {status}", () => pm.response.to.have.status({status}));']
    if index==2:
        tests += ['const p = pm.response.json();','pm.collectionVariables.set("productId", p.id);','pm.collectionVariables.unset("orderId");','pm.test("Ton kho ban dau 10", () => pm.expect(p.stock).to.eql(10));']
    if index==3:tests += ['pm.test("Stock truoc khi dat = 10", () => pm.expect(pm.response.json().stock).to.eql(10));']
    if index==4:
        tests += ['const o = pm.response.json();','pm.collectionVariables.set("orderId", o.id);','pm.test("Tong tien 500000", () => pm.expect(o.totalPrice).to.eql(500000));','pm.test("Tiep nhan PENDING", () => pm.expect(o.status).to.eql("PENDING"));']
    if index==5:tests += ['pm.test("Da xac nhan CONFIRMED", () => pm.expect(pm.response.json().status).to.eql("CONFIRMED"));']
    if index==6:tests += ['pm.test("Stock sau Kafka = 8", () => pm.expect(pm.response.json().stock).to.eql(8));']
    if index==11:tests += ['pm.test("Gia cap nhat 300000", () => pm.expect(pm.response.json().price).to.eql(300000));','pm.test("Ton kho cap nhat 20", () => pm.expect(pm.response.json().stock).to.eql(20));']
    item={'name':name,'request':request,'event':[{'listen':'test','script':{'type':'text/javascript','exec':tests}}]}
    if index==5:item['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':['setTimeout(() => {}, 2000);']}})
    items.append(item)
    command=f'curl --request {method} "{base+path}"'
    if raw is not None:command+=' --header "Content-Type: application/json" --data-raw '+shlex.quote(raw)
    markdown += [f'## {name}','',description,f'Kỳ vọng HTTP **{status}**. Gợi ý tên ảnh: `postman-{index:02d}.png`.','', '```bash',command,'```','']
collection={'info':{'name':'HỆ THỐNG E-COMMERCE MICROSERVICES - Chụp ảnh API','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
    'description':'API chụp ảnh bằng Postman UI. Đích localhost:18081 (Minikube). Chạy từng request theo thứ tự và chụp kết quả thật. Bước 02 và 04 tự lưu ID. Bước 11-12 thực hiện sau khi đã chụp stock=8.'},
    'variable':[{'key':'baseUrl','value':base},{'key':'productId','value':''},{'key':'orderId','value':''}], 'item':items}
(root/'postman/chup-anh.postman_collection.json').write_text(json.dumps(collection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'postman/LENH_CURL_CHUP_ANH.md').write_text('\n'.join(markdown),encoding='utf-8')
print(f'Generated {len(items)} manual screenshot requests and cURL instructions')
