# Hướng dẫn chạy HỆ THỐNG E-COMMERCE MICROSERVICES

Dành cho người mới dùng Windows. Sau khi cài Docker Desktop một lần, bạn chỉ cần nháy đúp **run.bat** để khởi động toàn bộ hệ thống và mở giao diện trên trình duyệt.

## 1. Chuẩn bị máy tính

- Dùng Windows 64 bit được Docker Desktop hỗ trợ. Máy Windows Intel/AMD thông thường chọn bản **Windows x86_64** trên trang tải chính thức.
- Docker yêu cầu tối thiểu 8 GB RAM; với bài này nên dùng máy 16 GB RAM, để Docker sử dụng khoảng 4 GB RAM trở lên và dành khoảng 10 GB ổ trống cho image, bộ nhớ đệm build và dữ liệu. Đây là mức khuyến nghị cho bài thực hành.
- Cần Internet trong lần chạy đầu để tải image Docker và thư viện Java.
- Trong Task Manager → Performance → CPU, kiểm tra **Virtualization: Enabled**. Nếu là Disabled, bật Intel VT-x/AMD-V trong BIOS/UEFI theo hướng dẫn của hãng máy.

Yêu cầu Windows/WSL và bộ cài được cập nhật tại [trang Docker Desktop chính thức](https://docs.docker.com/desktop/setup/install/windows-install/).

**Môi trường bắt buộc:** Docker Desktop, gồm Docker Engine và Docker Compose. Java 17, Maven, MySQL và Kafka đã được cấu hình chạy trong Docker; bạn không phải cài riêng các phần mềm này. Minikube và Postman chỉ dùng khi làm phần nâng cao.

## 2. Cài môi trường lần đầu

### Bước 1 — Cài WSL 2 nếu máy chưa có

1. Mở Start, tìm **PowerShell**, nhấn chuột phải → **Run as administrator**.
2. Dán lệnh sau rồi Enter:

```powershell
wsl --install --no-distribution
```

3. Khởi động lại máy nếu Windows yêu cầu. Mở lại PowerShell, cập nhật WSL:

```powershell
wsl --update
wsl --version
```

Docker hiện yêu cầu WSL 2.1.5 trở lên. Không cần tự cài Ubuntu để chạy bài này. Nếu máy đã có WSL, chỉ cần kiểm tra/cập nhật. Xem [các lệnh WSL của Microsoft](https://learn.microsoft.com/en-us/windows/wsl/basic-commands) khi gặp lỗi cài đặt.

### Bước 2 — Cài Docker Desktop

1. Tải bộ cài từ [Docker Desktop cho Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
2. Chạy bộ cài, chọn backend **WSL 2** nếu được hỏi và hoàn tất cài đặt.
3. Khởi động lại Windows nếu bộ cài yêu cầu.
4. Mở **Docker Desktop**, hoàn tất màn hình thiết lập lần đầu và chờ **Engine running**.
5. Trong Settings → General, dùng **WSL 2 based engine** nếu có tùy chọn. Hệ thống cần **Linux containers**; nếu Docker đang ở Windows containers, chuyển sang Linux containers từ menu Docker.

Không cần tạo tài khoản MySQL hoặc khởi động MySQL có sẵn trên Windows.

## 3. Lấy mã nguồn

Có thể dùng một trong hai cách:

- Nhận thư mục bài nộp/ZIP/RAR: **giải nén toàn bộ**, rồi mở thư mục có `run.bat`. Không chạy trực tiếp bên trong cửa sổ xem ZIP/RAR.
- Trên GitHub: chọn **Code → Download ZIP**, giải nén rồi mở thư mục có `run.bat`. Nếu đã cài Git, có thể dùng `git clone` thay cho Download ZIP.

Trong bản bài nộp, `run.bat` nằm cạnh `code/`. Trong bản clone Git, `run.bat` nằm cạnh `pom.xml`, `compose.run.yml` và `scripts/`. Cả hai vị trí đều chạy được; cần giữ nguyên cấu trúc thư mục.

## 4. Khởi động bằng một lần nháy đúp

1. Đảm bảo Docker Desktop đã chạy.
2. **Nháy đúp `run.bat`**. Không cần Run as administrator.
3. Giữ cửa sổ đang mở trong lúc tải thư viện, build Java, khởi động MySQL, Kafka và ba dịch vụ Java. Lần đầu có thể mất vài phút hoặc lâu hơn tùy mạng/máy; các lần sau tận dụng bộ nhớ đệm.
4. Chờ dòng **`READY: http://localhost:18080`**. Trình duyệt sẽ tự mở giao diện.
5. Nếu cổng 18080 đang bận hoặc bị Windows dành riêng, chương trình tự chọn cổng khác trong khoảng 18080–18100. **Dùng đúng địa chỉ sau chữ READY**.

`run.bat` kiểm tra Docker/Compose, build từ mã nguồn, chờ các container khỏe và kiểm tra API trước khi thông báo READY. Nếu lỗi, cửa sổ giữ lại thông báo và đường dẫn log để bạn đọc.

## 5. Dùng thử giao diện

1. Mở trang theo địa chỉ READY. Bạn sẽ thấy tên **HỆ THỐNG E-COMMERCE MICROSERVICES**.
2. Chọn một sản phẩm còn hàng, nhập số lượng hợp lệ, nhấn đặt hàng.
3. Đơn hàng ban đầu có trạng thái `PENDING`; chờ hệ thống xử lý Kafka rồi tải lại danh sách nếu cần để xem `CONFIRMED` hoặc `REJECTED`.
4. Xem lại danh sách sản phẩm để kiểm tra tồn kho. Nếu cần thêm/sửa sản phẩm, dùng API trong Postman theo README; giao diện hiện tại tập trung vào chọn sản phẩm và đặt hàng.

API danh sách sản phẩm: `http://localhost:18080/api/products`. Nếu chương trình chọn cổng khác, thay `18080` bằng cổng READY.

## 6. Dừng, chạy lại và xem lỗi

Đóng cửa sổ `run.bat` hoặc trình duyệt **không dừng hệ thống**. Các container vẫn chạy nền.

Để chạy các lệnh dưới đây: mở thư mục có `run.bat`, bấm thanh địa chỉ của File Explorer, gõ `powershell` rồi Enter. Sau đó dán lệnh cần dùng:

| Việc cần làm | Lệnh |
| --- | --- |
| Khởi động/chạy lại | `.\run.bat` |
| Dừng hệ thống, giữ dữ liệu | `.\run.bat stop` |
| Xem trạng thái container và cổng Gateway | `.\run.bat status` |
| Xem 100 dòng log gần nhất của các dịch vụ | `.\run.bat logs` |
| Chỉ kiểm tra Docker và cấu hình | `.\run.bat check` |
| Chạy mà không tự mở trình duyệt | `.\run.bat start -NoBrowser` |

Dữ liệu được lưu trong Docker volumes và được giữ khi dừng/chạy lại. Không xóa volumes trong Docker Desktop nếu muốn giữ sản phẩm, đơn hàng. Mật khẩu trong cấu hình là mật khẩu demo dùng cục bộ. Nếu đã có dữ liệu và file `.env`, giữ nguyên mật khẩu khi chạy lại.

Log bộ chạy nằm trong `code/logs/` của bản bài nộp hoặc `logs/` của bản Git. File `launcher-state.json` ghi địa chỉ của lần chạy thành công gần nhất; `run.bat status` cho biết trạng thái hiện tại.

## 7. Xử lý lỗi thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| `Docker Desktop is missing` | Cài Docker Desktop ở bước 2. Nếu vừa cài, mở lại thư mục/terminal rồi chạy lại. |
| `Docker Engine is not ready` | Mở Docker Desktop, hoàn tất thiết lập lần đầu, chờ Engine running rồi chạy lại. |
| Docker báo WSL/virtualization | Bật ảo hóa CPU, cập nhật WSL, khởi động lại máy; xem liên kết Microsoft/Docker ở trên. |
| `switch ... to Linux containers` | Chuyển Docker Desktop sang Linux containers. |
| Tải image/thư viện thất bại | Kiểm tra Internet, proxy/VPN và dung lượng ổ đĩa; xem log rồi chạy lại. Docker sẽ dùng lại phần tải/build đã lưu. |
| Container `unhealthy`, thoát hoặc bị OOM | Chạy `run.bat logs`, kiểm tra dung lượng/RAM của Docker. Đóng các ứng dụng nặng hoặc tăng RAM cho WSL/Docker theo tài liệu Docker. |
| Báo đăng nhập MySQL thất bại | Nếu dùng dữ liệu cũ, kiểm tra mật khẩu `.env` có khớp lần khởi tạo trước không. Đổi biến mật khẩu không tự đổi mật khẩu trong database cũ. |
| Không mở được web | Chạy `run.bat status`, dùng đúng cổng được in ra. Thử chạy lại `run.bat`. |
| Không thấy file `scripts/run.ps1` | Giải nén/tải đủ mã nguồn; giữ nguyên `code/` cùng `run.bat` trong bản bài nộp. |
| `unknown flag: --wait` / `--progress` | Cập nhật Docker Desktop để có Docker Compose mới, sau đó mở lại terminal và chạy lại. |

Nếu cần gửi lỗi cho người hỗ trợ, gửi file `launcher-...log` mới nhất. Kiểm tra nội dung log trước khi chia sẻ nếu bạn đã cấu hình thông tin riêng.

## 8. Chạy nâng cao

Xem [README.md](README.md) để build/test bằng JDK 17 và Maven, dùng Postman, hoặc triển khai Minikube. Đây là các cách dành cho phát triển/kiểm thử, không cần làm để sử dụng `run.bat`.

Bản Compose của `run.bat` dùng cổng mặc định 18080. Bản Minikube trong bài dùng port-forward 18081 và có dữ liệu riêng. Chỉ cần chọn một cách chạy; `run.bat` quản lý các container Compose của bài, không quản lý Minikube.
