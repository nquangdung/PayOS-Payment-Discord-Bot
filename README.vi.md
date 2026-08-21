# PayOS Payment Bot

Bot Discord tạo và theo dõi link thanh toán [PayOS](https://payos.vn/), kèm webhook Flask để nhận cập nhật trạng thái thanh toán theo thời gian thực.

🇬🇧 Bản tiếng Anh: [README.md](./README.md)

## Tính năng

- `/thanhtoan <sotien>` — tạo link thanh toán PayOS (mã QR + link checkout), sau đó tự động kiểm tra trạng thái cho đến khi thanh toán thành công, bị hủy, thất bại hoặc hết thời gian chờ.
- `/huygiaodich <ma_giao_dich>` — hủy một giao dịch đang chờ thanh toán.
- `POST /webhook` — nhận sự kiện webhook từ PayOS (đã xác thực chữ ký) và gửi embed thông báo vào kênh nhân viên.
- Chống lạm dụng cơ bản: giới hạn thời gian giữa các lần thử của mỗi người dùng, và giới hạn số giao dịch đang mở đồng thời.

## Cấu trúc thư mục

```
payos_bot/
├── main.py                       # Điểm khởi chạy: dựng bot + Flask app, chạy song song
├── constants/
│   └── config.py                 # Biến môi trường và hằng số (số tiền tối thiểu, thời gian chờ,...)
├── utils/
│   └── logging_config.py         # Thiết lập logging
├── model/
│   └── transaction_store.py      # Trạng thái giao dịch/giới hạn trong bộ nhớ
├── services/
│   ├── payos_service.py          # Gọi API PayOS, tạo/xác thực chữ ký HMAC
│   └── webhook_service.py        # Flask app + route /webhook
└── command/
    └── payment_commands.py       # Slash command Discord (/thanhtoan, /huygiaodich)
```

Vai trò từng lớp:

| Lớp | Trách nhiệm |
|---|---|
| `constants` | Toàn bộ giá trị cấu hình — không nơi nào khác nên gọi `os.getenv` trực tiếp. |
| `utils` | Tiện ích dùng chung nhiều nơi (hiện tại chỉ có logging). |
| `model` | Trạng thái trong bộ nhớ cho giao dịch đang mở và giới hạn tần suất. |
| `services` | Xử lý I/O bên ngoài: gọi API PayOS, tạo/xác thực chữ ký HMAC, webhook Flask. |
| `command` | Các slash command Discord, xây dựng dựa trên `model` + `services`. |

## Yêu cầu

- Python 3.9 trở lên
- Ứng dụng bot Discord đã bật scope `applications.commands`
- Tài khoản merchant PayOS (Client ID, API Key, Checksum Key)

## Cài đặt

```bash
git clone <your-repo-url>
cd payos_bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install discord.py requests python-dotenv flask beautifulsoup4
```

## Cấu hình

Tạo file `.env` ở thư mục gốc dự án:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
STAFF_CHANNEL_ID=your_channel_id
PAYOS_CLIENT_ID=your_payos_client_id
PAYOS_API_KEY=your_payos_api_key
PAYOS_CHECKSUM_KEY=your_payos_checksum_key
```

| Biến | Mô tả |
|---|---|
| `DISCORD_BOT_TOKEN` | Token bot Discord lấy từ [Developer Portal](https://discord.com/developers/applications) |
| `STAFF_CHANNEL_ID` | ID kênh nơi các cập nhật từ webhook sẽ được gửi vào |
| `PAYOS_CLIENT_ID` | Client ID của PayOS |
| `PAYOS_API_KEY` | API Key của PayOS |
| `PAYOS_CHECKSUM_KEY` | Checksum Key của PayOS (dùng để ký/xác thực request và webhook) |

Các thông số khác nằm trong `constants/config.py`:

- `SO_TIEN_TOI_THIEU` — số tiền thanh toán tối thiểu (mặc định 2.000 VNĐ)
- `THOI_GIAN_CHO` — thời gian tối đa chờ kiểm tra thanh toán trước khi tự hủy (mặc định 300 giây)
- `THOI_GIAN_GIOI_HAN` — thời gian giới hạn giữa các lần thử của mỗi người dùng (mặc định 60 giây)
- `SO_LAN_TOI_DA_MOI_NGUOI` — số giao dịch đang mở tối đa cho mỗi người dùng (mặc định 3)
- `WEBHOOK_HOST` / `WEBHOOK_PORT` — địa chỉ/cổng chạy Flask (mặc định `0.0.0.0:5500`)

## Chạy chương trình

```bash
python main.py
```

Lệnh này sẽ khởi động:
1. Bot Discord, chạy trên một thread nền.
2. Server webhook Flask (`/webhook`), chạy trên thread chính.

Trỏ URL webhook của PayOS về `http://<server-cua-ban>:5500/webhook` (nên đặt sau reverse proxy có HTTPS khi triển khai thực tế).

## Lưu ý

- Trạng thái giao dịch được lưu **trong bộ nhớ (RAM)** — sẽ mất khi tiến trình khởi động lại. Nếu triển khai thực tế với nhiều worker, nên thay `model/transaction_store.py` bằng Redis hoặc database thay vì dict.
- Các trường tên/số tài khoản ngân hàng trong embed thanh toán (`command/payment_commands.py`) hiện đang để trống — hãy điền thông tin tài khoản thực tế, hoặc lấy từ phản hồi PayOS nếu có.
- Log được ghi ra cả file `bot.log` và stdout.

## Giấy Phép

Dự án được phát hành theo **GNU General Public License v3.0 (GPL-3.0)**.
