import os
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

# Cấu hình PayOS
MA_CLIENT = os.getenv("PAYOS_CLIENT_ID")
KHOA_API = os.getenv("PAYOS_API_KEY")
KHOA_KIEM_TRA = os.getenv("PAYOS_CHECKSUM_KEY")
KENH_NHAN_VIEN = int(os.getenv("STAFF_CHANNEL_ID"))
TOKEN_BOT = os.getenv("DISCORD_BOT_TOKEN")

# Kiểm tra biến môi trường
if not TOKEN_BOT:
    raise ValueError("TOKEN_BOT không được thiết lập trong biến môi trường")

# Giới hạn giao dịch
SO_LAN_TOI_DA_MOI_NGUOI = 3
THOI_GIAN_CHO = 300  # 5 phút
SO_TIEN_TOI_THIEU = 2000  # Tối thiểu 2,000 VNĐ
THOI_GIAN_GIOI_HAN = 60  # 60 giây giới hạn giữa các lần thử

# URL cơ bản của API
PAYOS_API_BASE = "https://api-merchant.payos.vn"

# Cấu hình webhook Flask
WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 5500
