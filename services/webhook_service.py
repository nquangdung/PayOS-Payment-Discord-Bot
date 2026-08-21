import asyncio
import logging
from datetime import datetime

import discord
from flask import Flask, jsonify, request

from constants.config import KENH_NHAN_VIEN
from services.payos_service import xac_thuc_chu_ky_webhook

app = Flask(__name__)


def dang_ky_webhook(bot: discord.ext.commands.Bot) -> Flask:
    """Đăng ký route /webhook, dùng `bot` để gửi thông báo về kênh nhân viên."""

    @app.route('/webhook', methods=['POST'])
    def webhook_payos():
        try:
            du_lieu_webhook = request.get_json()
            chu_ky = request.headers.get('x-payos-signature')

            if not chu_ky or not xac_thuc_chu_ky_webhook(du_lieu_webhook, chu_ky):
                logging.error("Chữ ký webhook không hợp lệ")
                return jsonify({"loi": "Chữ ký không hợp lệ"}), 401

            ma_giao_dich = du_lieu_webhook.get('data', {}).get('orderCode')
            trang_thai = du_lieu_webhook.get('data', {}).get('status')

            kenh_nhan_vien = bot.get_channel(KENH_NHAN_VIEN)
            if kenh_nhan_vien:
                embed = discord.Embed(
                    title="📢 Cập Nhật Giao Dịch",
                    color=discord.Color.blue(),
                    description=f"Giao dịch `{ma_giao_dich}`: **{trang_thai}**",
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text="Hệ thống PayOS")
                asyncio.run_coroutine_threadsafe(kenh_nhan_vien.send(embed=embed), bot.loop)

            return jsonify({"thong_bao": "Webhook đã nhận"}), 200
        except Exception as e:
            logging.error(f"Lỗi xử lý webhook: {e}")
            return jsonify({"loi": str(e)}), 500

    return app
