# HỆ THỐNG E-COMMERCE MICROSERVICES

Bài thực hành Java Web của **Giàng Seo Chính — 2023602847**. Hệ thống quản lý sản phẩm và đơn hàng bằng Spring Boot, giao tiếp đồng bộ qua gRPC và xử lý sự kiện tồn kho qua Kafka.

## Chạy nhanh trên Windows

**Chỉ cần cài Docker Desktop và để Docker Engine chạy ở chế độ Linux containers.** Java, Maven, MySQL và Kafka được chạy trong Docker.

1. Tải/clone mã nguồn và giải nén toàn bộ nếu tải ZIP/RAR.
2. Đọc [hướng dẫn cài môi trường và chạy cho người mới](HUONG_DAN_CHAY.md).
3. Nháy đúp **`run.bat`**.
4. Chờ dòng `READY: http://localhost:18080`; trình duyệt sẽ tự mở giao diện. Nếu cổng mặc định đang bận, dùng cổng thay thế được in sau chữ `READY`.

Lần đầu cần Internet để Docker tải image và thư viện Java. Những lần sau dùng lại bộ nhớ đệm build. Bộ chạy chờ các container khỏe và kiểm tra Gateway cùng API sản phẩm/đơn hàng trước khi báo thành công.

Các lệnh dưới đây chạy trong PowerShell tại thư mục chứa `run.bat`:

```powershell
.\run.bat                       # Build, khởi động toàn bộ và mở giao diện
.\run.bat stop                  # Dừng các container của bài, giữ dữ liệu
.\run.bat status                # Xem trạng thái và địa chỉ Gateway
.\run.bat logs                  # Xem log gần nhất
.\run.bat check                 # Kiểm tra Docker/Compose/cấu hình
.\run.bat start -NoBrowser      # Khởi động nhưng không tự mở trình duyệt
```

Đóng cửa sổ hoặc trình duyệt không dừng container. Dùng `run.bat stop` để dừng. Dữ liệu MySQL và Kafka nằm trong Docker volumes, được giữ khi chạy lại.

`run.bat` hoạt động ở cả hai cấu trúc: thư mục bài nộp có `code/`, hoặc thư mục repository có `pom.xml` ngay cạnh `run.bat`. Các lệnh phát triển bên dưới chạy tại thư mục chứa `pom.xml` — nếu đang ở thư mục bài nộp thì vào `code/` trước.

## Kiến trúc

```text
Trình duyệt / Postman
        |
    API Gateway ---- REST ----> Product Service ----> product_db (MySQL)
        |                            ^
        |                            | gRPC: kiểm tra sản phẩm
        +----------- REST ----> Order Service ------> order_db (MySQL)
                                     |
                           Kafka: order-events
                                     |
                              Product Service
                                     |
                          Kafka: inventory-results
                                     |
                               Order Service
```

- Product Service cung cấp CRUD sản phẩm, gRPC server và consumer cập nhật tồn kho.
- Order Service gọi gRPC để kiểm tra sản phẩm, lưu đơn hàng và phát sự kiện qua transactional outbox. Khi Kafka tạm ngừng, sự kiện được giữ trong database để gửi lại.
- Đơn hàng chuyển từ `PENDING` sang `CONFIRMED` hoặc `REJECTED` sau khi nhận kết quả xử lý tồn kho.
- Cập nhật tồn kho có điều kiện và ghi nhận sự kiện đã xử lý giúp tránh bán vượt số lượng, tránh trừ kho lặp khi Kafka giao lại sự kiện.
- Gateway định tuyến API, phục vụ giao diện và chỉ retry các yêu cầu đọc được cấu hình; không tự retry thao tác tạo đơn.

| Công nghệ | Phiên bản/công dụng |
| --- | --- |
| Java | 17 |
| Spring Boot | 3.5.4 |
| Spring Cloud | 2025.0.0, API Gateway |
| MySQL | 8.0, hai database độc lập theo dịch vụ |
| Apache Kafka | 3.9.1, KRaft |
| gRPC / Protobuf | Contract chung trong `proto/` |
| Docker Compose | Chạy toàn bộ hệ thống cục bộ |
| Kubernetes / Minikube | Manifest triển khai, health probes, rolling update |
| GitLab CI/CD | Cấu hình build, kiểm thử, push image và triển khai |

## Cấu trúc repository

```text
.
|-- run.bat                    Bộ chạy Windows
|-- HUONG_DAN_CHAY.md           Hướng dẫn dành cho người mới
|-- pom.xml                    Maven multi-module
|-- proto/                     Contract gRPC
|-- common/                    Event DTO, xử lý lỗi, transactional outbox
|-- product-service/           REST + gRPC server + Kafka consumer
|-- order-service/             REST + gRPC client + xử lý đơn hàng
|-- api-gateway/               Gateway và giao diện web
|-- database/                  SQL khởi tạo database
|-- compose.run.yml            Chạy bằng Docker, build từ source
|-- Dockerfile.source          Maven builder + Java runtime
|-- docker-compose.yml         Chế độ phát triển, mở thêm cổng dịch vụ
|-- Dockerfile                 Runtime dùng JAR đã build, phục vụ CI/dev
|-- postman/                   Collection và environment
|-- k8s/                       Manifest Kubernetes
|-- scripts/                   Bộ chạy, build, kiểm thử, triển khai
|-- evidence/                  Kết quả kiểm thử đã lưu
`-- .gitlab-ci.yml             Pipeline GitLab
```

`logs/`, các thư mục `target/`, file `.env` cục bộ và cache không đưa lên Git. Báo cáo Word, đề bài và ảnh gốc được quản lý ngoài repository mã nguồn trong bản bài nộp.

## Cấu hình chạy bằng run.bat

`scripts/run.ps1` dùng `compose.run.yml` và `Dockerfile.source` để build ngay trong Docker. Chế độ này chỉ công bố Gateway trên `127.0.0.1`, cổng mặc định `18080`; MySQL, Kafka, REST/gRPC nội bộ dùng mạng Docker.

Không cần tạo `.env` để chạy với cấu hình demo. Nếu muốn tùy chỉnh, sao chép `.env.example` thành `.env`. `GATEWAY_PORT` đổi cổng web; nếu cổng bận, bộ chạy chọn cổng trống trong khoảng 18080–18100 và in địa chỉ thực tế. Nếu đã có dữ liệu, giữ mật khẩu database khớp lần khởi tạo trước.

Hai file Compose cùng dùng project `tx2-ecommerce` và các volumes của bài. Chọn một chế độ tại một thời điểm; chuyển chế độ bằng cách dừng cấu hình đang chạy trước. Cổng MySQL/Kafka trong `.env.example` chỉ áp dụng cho chế độ phát triển bên dưới.

Log bộ chạy nằm ở `logs/launcher-...log`. File `logs/launcher-state.json` lưu địa chỉ lần khởi động thành công gần nhất. Đây là cấu hình demo cục bộ; cần cấu hình bảo mật riêng trước khi triển khai ra Internet.

## API và Postman

Địa chỉ mặc định khi dùng `run.bat`: `http://localhost:18080`. Nếu bộ chạy chọn cổng khác, thay `baseUrl` trong Postman cho đúng.

| Method | Đường dẫn | Chức năng |
| --- | --- | --- |
| GET | `/api/products` | Danh sách sản phẩm |
| GET | `/api/products/{id}` | Chi tiết sản phẩm |
| POST | `/api/products` | Thêm sản phẩm |
| PUT | `/api/products/{id}` | Cập nhật sản phẩm |
| DELETE | `/api/products/{id}` | Xóa sản phẩm |
| POST | `/api/orders` | Tạo đơn hàng |
| GET | `/api/orders` | Danh sách đơn hàng |
| GET | `/api/orders/{id}` | Chi tiết và trạng thái đơn |
| GET | `/actuator/health` | Sức khỏe Gateway |

Các API danh sách nhận `page` và `size`, với `size` tối đa 100. Sản phẩm nhận `name`, `price`, `stock`; đơn hàng nhận `productId`, `quantity`. Ví dụ tạo đơn:

```json
{
  "productId": 1,
  "quantity": 1
}
```

Thay `productId` bằng ID tồn tại và chọn số lượng phù hợp. API tạo đơn có thể trả `201` với trạng thái `PENDING`; đọc lại đơn sau khi Kafka xử lý để xem kết quả cuối.

Trong Postman, import [collection kiểm thử](postman/tx2.postman_collection.json) và [environment Compose](postman/local.postman_environment.json), chọn environment rồi kiểm tra biến `baseUrl`. Collection chụp ảnh riêng nằm ở [chup-anh.postman_collection.json](postman/chup-anh.postman_collection.json); kiểm tra `baseUrl` trước khi chạy vì ảnh báo cáo dùng bản Minikube cổng 18081.

## Phát triển và kiểm thử bằng JDK/Maven

Phần này cần **JDK 17**, **Maven 3.9.x** và Docker Desktop. Không bắt buộc khi chỉ dùng `run.bat`.

```powershell
java -version
mvn -version
mvn -B clean verify -ntp
```

Để chạy chế độ phát triển bằng JAR build trên máy:

```powershell
docker compose -f compose.run.yml stop
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1
```

`docker-compose.yml` mở thêm các cổng cục bộ để kết nối công cụ phát triển:

| Thành phần | Cổng mặc định trên máy |
| --- | --- |
| Gateway | 18080 |
| Product REST / gRPC | 8081 / 9090 |
| Order REST | 8082 |
| MySQL | 3310 |
| Kafka | 29092 |

Kiểm tra các cổng này không bị ứng dụng khác chiếm trước khi dùng chế độ phát triển. Để quay lại bộ chạy đơn giản, chạy `docker compose stop` rồi `run.bat`.

Nếu đã cài Python 3, có thể chạy kiểm thử API tích hợp sau khi hệ thống sẵn sàng:

```powershell
python scripts/verify-system.py --base-url http://localhost:18080 --output logs/system-tests.json
```

Script tạo sản phẩm/đơn hàng thử nghiệm và kiểm tra nghiệp vụ, gồm tình huống đặt hàng đồng thời. Tùy chọn `--resilience` còn tạm dừng Kafka/Product Service, chỉ dùng trên stack phát triển cục bộ với `docker-compose.yml` khi chủ động kiểm thử phục hồi. Kết quả kiểm thử cũ trong `evidence/` là minh chứng tại lần chạy đã ghi, không thay thế kết quả trên máy mới.

## Triển khai Minikube

Phần này cần thêm Minikube. Nên dừng stack Compose để dành RAM trước khi triển khai; Minikube dùng database và Kafka riêng.

```powershell
.\run.bat stop
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy-minikube.ps1
minikube kubectl -- -n tx2-ecommerce get pods,services
minikube kubectl -- -n tx2-ecommerce port-forward service/api-gateway 18081:8080
```

Giữ terminal port-forward mở và truy cập `http://localhost:18081`. Có thể dùng `scripts/open-minikube.ps1` thay cho lệnh port-forward để chạy nền. Namespace của bài là `tx2-ecommerce`.

## CI/CD

[.gitlab-ci.yml](.gitlab-ci.yml) định nghĩa ba giai đoạn: Maven build/test → build và push ba image → triển khai Minikube. Job triển khai cần GitLab Runner Windows có tag `minikube-windows`, quyền truy cập Docker/Minikube và registry theo cấu hình trong pipeline.

GitHub hiển thị mã nguồn/README nhưng không tự chạy file GitLab CI. Pipeline trên GitLab cần repository, runner và quyền truy cập tương ứng được thiết lập; không coi việc có file cấu hình là bằng chứng pipeline đã chạy thành công.

## Đưa thay đổi lên Git

Repository của bản bài nộp nằm trong **`code/`**. Khi mở PowerShell ở ngoài `code/`, vào thư mục này trước; khi đã ở bản clone có `pom.xml` ngay tại gốc thì không chạy thêm `cd code`.

```powershell
git status
git add README.md HUONG_DAN_CHAY.md run.bat scripts/run.ps1 Dockerfile.source compose.run.yml .gitattributes
git diff --cached --stat
git commit -m "Add one-click Docker launcher and setup guide"
git push
```

Lệnh `git add` trên chỉ chọn bộ chạy và tài liệu mới. Nếu muốn đưa cả các thay đổi giao diện/báo cáo kiểm thử trước đó lên Git, xem `git status` và chọn thêm các file tương ứng.

README được lưu UTF-8, Markdown chuẩn và dùng liên kết tương đối. Không dùng `Out-File`/`>>` mặc định của Windows PowerShell 5.1 để nối nội dung vào README vì có thể trộn UTF-16 với UTF-8. Nên sửa bằng trình soạn thảo và chọn **UTF-8** khi lưu. File `.gitattributes` quy định xuống dòng phù hợp cho Markdown, PowerShell và batch.
