import time
from typing import Any, Dict

from constants.config import SO_LAN_TOI_DA_MOI_NGUOI, THOI_GIAN_GIOI_HAN

# Theo dõi giao dịch đang thực hiện của từng người dùng
giao_dich_dang_thuc_hien: Dict[str, Dict[str, Any]] = {}


def kiem_tra_gioi_han_thoi_gian(ten_nguoi_dung: str) -> bool:
    """Trả về True nếu người dùng đang trong thời gian giới hạn giữa 2 lần thử."""
    if ten_nguoi_dung in giao_dich_dang_thuc_hien:
        thoi_gian_truoc = giao_dich_dang_thuc_hien[ten_nguoi_dung].get('lan_thu_truoc', 0)
        if time.time() - thoi_gian_truoc < THOI_GIAN_GIOI_HAN:
            return True
    return False


def da_vuot_qua_gioi_han_giao_dich(ten_nguoi_dung: str) -> bool:
    """Trả về True nếu người dùng đã đạt số lượng giao dịch đồng thời tối đa."""
    return (
        ten_nguoi_dung in giao_dich_dang_thuc_hien
        and giao_dich_dang_thuc_hien[ten_nguoi_dung]['so_lan'] >= SO_LAN_TOI_DA_MOI_NGUOI
    )


def bat_dau_giao_dich(ten_nguoi_dung: str) -> None:
    """Ghi nhận người dùng vừa bắt đầu một giao dịch mới."""
    if ten_nguoi_dung not in giao_dich_dang_thuc_hien:
        giao_dich_dang_thuc_hien[ten_nguoi_dung] = {'so_lan': 0, 'lan_thu_truoc': time.time()}
    giao_dich_dang_thuc_hien[ten_nguoi_dung]['so_lan'] += 1
    giao_dich_dang_thuc_hien[ten_nguoi_dung]['lan_thu_truoc'] = time.time()


def ket_thuc_giao_dich(ten_nguoi_dung: str) -> None:
    """Giảm số giao dịch đang mở của người dùng, xóa khỏi bộ nhớ nếu về 0."""
    if ten_nguoi_dung in giao_dich_dang_thuc_hien:
        giao_dich_dang_thuc_hien[ten_nguoi_dung]['so_lan'] -= 1
        if giao_dich_dang_thuc_hien[ten_nguoi_dung]['so_lan'] <= 0:
            del giao_dich_dang_thuc_hien[ten_nguoi_dung]
