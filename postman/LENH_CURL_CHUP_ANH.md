# API dùng để chụp ảnh Postman

Các lệnh cURL bên dưới dùng để dán vào Postman, không chạy trong PowerShell.
Chọn Import, dán nguyên một lệnh cURL rồi Import và Send. Chạy theo thứ tự.
Cách thuận tiện hơn: import `chup-anh.postman_collection.json`; collection tự lưu productId và orderId.

Nếu chỉ import từng lệnh cURL, thay `{{productId}}` bằng id từ bước 02 và `{{orderId}}` bằng id từ bước 04 trước khi gửi.
Không tự điền một ID ví dụ cố định vì mỗi lần chạy database có thể trả ID khác nhau.

Chụp cả method, URL, Body (với POST/PUT), HTTP status và JSON response. Lưu ảnh ở thư mục gốc tx2 theo yêu cầu.
Sau bước 04 chỉ chụp trạng thái PENDING; bước 05 chụp CONFIRMED; bước 06 chụp stock giảm từ 10 xuống 8.
Bấm Send bước tạo đơn một lần. Muốn chạy lại cả chuỗi, bắt đầu từ bước 02 để tạo sản phẩm mới.

## 01 Danh sách sản phẩm

Danh sách sản phẩm hiện có.
Kỳ vọng HTTP **200**. Gợi ý tên ảnh: `postman-01.png`.

```bash
curl --request GET "http://localhost:18081/api/products"
```

## 02 Tạo sản phẩm demo

Ghi lại id sản phẩm trả về. Collection tự lưu productId.
Kỳ vọng HTTP **201**. Gợi ý tên ảnh: `postman-02.png`.

```bash
curl --request POST "http://localhost:18081/api/products" --header "Content-Type: application/json" --data-raw '{"name": "San pham demo Postman", "price": 250000, "stock": 10}'
```

## 03 Xem sản phẩm trước khi đặt

Tồn kho stock = 10.
Kỳ vọng HTTP **200**. Gợi ý tên ảnh: `postman-03.png`.

```bash
curl --request GET "http://localhost:18081/api/products/{{productId}}"
```

## 04 Tạo đơn hàng

Bấm Send một lần. totalPrice = 500000; ban đầu status = PENDING. Collection tự lưu orderId.
Kỳ vọng HTTP **201**. Gợi ý tên ảnh: `postman-04.png`.

```bash
curl --request POST "http://localhost:18081/api/orders" --header "Content-Type: application/json" --data-raw '{"productId": {{productId}}, "quantity": 2}'
```

## 05 Kiểm tra xác nhận đơn

Đợi khoảng 2 giây sau bước 04. Nếu còn PENDING, bấm Send lại đến CONFIRMED.
Kỳ vọng HTTP **200**. Gợi ý tên ảnh: `postman-05.png`.

```bash
curl --request GET "http://localhost:18081/api/orders/{{orderId}}"
```

## 06 Kiểm tra tồn kho sau Kafka

Sau khi đơn CONFIRMED, stock = 8. Đây là bằng chứng cập nhật tồn kho bất đồng bộ.
Kỳ vọng HTTP **200**. Gợi ý tên ảnh: `postman-06.png`.

```bash
curl --request GET "http://localhost:18081/api/products/{{productId}}"
```

## 07 Lỗi số lượng bằng không

Dữ liệu sai phải trả 400 Bad Request.
Kỳ vọng HTTP **400**. Gợi ý tên ảnh: `postman-07.png`.

```bash
curl --request POST "http://localhost:18081/api/orders" --header "Content-Type: application/json" --data-raw '{"productId": {{productId}}, "quantity": 0}'
```

## 08 Lỗi vượt tồn kho

Thiếu tồn kho phải trả 409 Conflict.
Kỳ vọng HTTP **409**. Gợi ý tên ảnh: `postman-08.png`.

```bash
curl --request POST "http://localhost:18081/api/orders" --header "Content-Type: application/json" --data-raw '{"productId": {{productId}}, "quantity": 99}'
```

## 09 Lỗi sản phẩm không tồn tại

gRPC NOT_FOUND được chuyển thành REST 404.
Kỳ vọng HTTP **404**. Gợi ý tên ảnh: `postman-09.png`.

```bash
curl --request POST "http://localhost:18081/api/orders" --header "Content-Type: application/json" --data-raw '{"productId": 9223372036854775807, "quantity": 1}'
```

## 10 Xem danh sách đơn

Danh sách đơn, gồm đơn demo vừa tạo.
Kỳ vọng HTTP **200**. Gợi ý tên ảnh: `postman-10.png`.

```bash
curl --request GET "http://localhost:18081/api/orders"
```

## 11 Cập nhật sản phẩm demo

Chỉ chạy sau khi chụp bước 06. Giá 300000, tồn kho 20.
Kỳ vọng HTTP **200**. Gợi ý tên ảnh: `postman-11.png`.

```bash
curl --request PUT "http://localhost:18081/api/products/{{productId}}" --header "Content-Type: application/json" --data-raw '{"name": "San pham demo da cap nhat", "price": 300000, "stock": 20}'
```

## 12 Xóa sản phẩm demo

Tùy chọn dọn dữ liệu sau khi chụp đủ ảnh. Body trống với HTTP 204 là đúng.
Kỳ vọng HTTP **204**. Gợi ý tên ảnh: `postman-12.png`.

```bash
curl --request DELETE "http://localhost:18081/api/products/{{productId}}"
```
