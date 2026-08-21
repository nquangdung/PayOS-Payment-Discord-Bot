import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

import requests

from constants.config import KHOA_API, KHOA_KIEM_TRA, MA_CLIENT, PAYOS_API_BASE


def xac_thuc_chu_ky_webhook(du_lieu: Dict, chu_ky_nhan: str) -> bool:
    """Xác thực chữ ký webhook nhận từ PayOS."""
    try:
        chu_ky_tinh_toan = hmac.new(
            KHOA_KIEM_TRA.encode('utf-8'),
            json.dumps(du_lieu, separators=(',', ':')).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(chu_ky_tinh_toan, chu_ky_nhan)
    except Exception as e:
        logging.error(f"Lỗi xác thực chữ ký: {e}")
        return False


def tao_chu_ky_thanh_toan(du_lieu_thanh_toan: Dict) -> str:
    """Tạo chữ ký HMAC-SHA256 cho payload tạo link thanh toán."""
    body_string = json.dumps(du_lieu_thanh_toan, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        KHOA_KIEM_TRA.encode('utf-8'),
        body_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def goi_api(phuong_thuc: str, duong_dan: str, du_lieu: Optional[Dict] = None, so_lan_thu: int = 3) -> Optional[Dict[str, Any]]:
    """Gọi API PayOS kèm cơ chế retry (backoff theo cấp số nhân)."""
    headers = {
        "x-client-id": MA_CLIENT,
        "x-api-key": KHOA_API,
        "Content-Type": "application/json"
    }
    url = f"{PAYOS_API_BASE}{duong_dan}"
    for lan_thu in range(so_lan_thu):
        try:
            response = requests.request(phuong_thuc, url, json=du_lieu, headers=headers, timeout=10)
            response.raise_for_status()
            phan_hoi_json = response.json()
            logging.info(f"API {phuong_thuc} {url} - Trạng thái: {response.status_code}, Phản hồi: {phan_hoi_json}")
            if phan_hoi_json.get('code') != '00':
                logging.error(f"Lỗi API PayOS: {phan_hoi_json.get('desc')}")
                return None
            return phan_hoi_json
        except requests.RequestException as e:
            logging.error(f"API {phuong_thuc} lần thử {lan_thu + 1}/{so_lan_thu} thất bại cho {url}: {e}")
            if lan_thu == so_lan_thu - 1:
                return None
            time.sleep(2 ** lan_thu)
    return None
