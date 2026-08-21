import asyncio
import logging
import random
import time
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from constants.config import SO_TIEN_TOI_THIEU, THOI_GIAN_CHO, THOI_GIAN_GIOI_HAN
from model.transaction_store import (
    bat_dau_giao_dich,
    da_vuot_qua_gioi_han_giao_dich,
    kiem_tra_gioi_han_thoi_gian,
    ket_thuc_giao_dich,
)
from services.payos_service import goi_api, tao_chu_ky_thanh_toan


def dang_ky_lenh(bot: commands.Bot) -> None:
    """Đăng ký các slash command thanh toán lên bot.tree."""

    @bot.tree.command(name="thanhtoan", description="Tạo giao dịch thanh toán (tối thiểu 2,000 VNĐ)")
    @app_commands.describe(sotien="Số tiền thanh toán (VNĐ)")
    async def thanh_toan(interaction: discord.Interaction, sotien: float):
        try:
            await interaction.response.defer(ephemeral=False)
        except discord.errors.NotFound:
            logging.error("Tương tác không hợp lệ (404)")
            return

        ten_nguoi_dung = str(interaction.user)
        try:
            # Kiểm tra giới hạn thời gian
            if kiem_tra_gioi_han_thoi_gian(ten_nguoi_dung):
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="⏳ Đang Trong Thời Gian Giới Hạn",
                        description=f"Vui lòng chờ {THOI_GIAN_GIOI_HAN} giây trước khi thử lại.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            # Kiểm tra số lượng giao dịch
            if da_vuot_qua_gioi_han_giao_dich(ten_nguoi_dung):
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="⚠️ Vượt Quá Giới Hạn Giao Dịch",
                        description="Bạn đang có quá nhiều giao dịch. Hoàn tất hoặc hủy giao dịch hiện tại.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            bat_dau_giao_dich(ten_nguoi_dung)

            sotien = int(sotien)
            if sotien < SO_TIEN_TOI_THIEU:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="⚠️ Số Tiền Không Hợp Lệ",
                        description=f"Số tiền tối thiểu là {SO_TIEN_TOI_THIEU:,} VNĐ.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            ma_giao_dich = random.randint(1000000000, 9999999999)
            noi_dung = f"GD{ma_giao_dich}"

            # Tạo payload thanh toán
            du_lieu_thanh_toan = {
                "orderCode": ma_giao_dich,
                "amount": sotien,
                "description": noi_dung,
                "items": [{"name": noi_dung, "quantity": 1, "price": sotien}],
                "cancelUrl": "",  # Thay bằng URL thực tế
                "returnUrl": ""  # Thay bằng URL thực tế
            }
            du_lieu_thanh_toan["signature"] = tao_chu_ky_thanh_toan(du_lieu_thanh_toan)

            # Gọi API tạo link thanh toán
            phan_hoi_link_thanh_toan = goi_api("POST", "/v2/payment-requests", du_lieu_thanh_toan)
            if not phan_hoi_link_thanh_toan or 'data' not in phan_hoi_link_thanh_toan:
                raise Exception(f"Lỗi tạo link thanh toán: {phan_hoi_link_thanh_toan}")

            if phan_hoi_link_thanh_toan.get('code') != '00':
                raise Exception(f"Lỗi PayOS: {phan_hoi_link_thanh_toan.get('desc')}")

            url_thanh_toan = phan_hoi_link_thanh_toan['data'].get('checkoutUrl')
            qr_code = phan_hoi_link_thanh_toan['data'].get('qrCode')
            if not url_thanh_toan:
                raise Exception("Không nhận được URL thanh toán")

            # Tạo embed thanh toán
            embed = discord.Embed(
                title="💳 Yêu Cầu Thanh Toán",
                description="Vui lòng thanh toán theo thông tin dưới đây. Quét mã QR hoặc nhấn link để thanh toán.",
                color=discord.Color.from_rgb(47, 128, 237),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name="Hệ Thống Thanh Toán", icon_url="https://i.imgur.com/your-logo.png")
            embed.set_thumbnail(url="https://i.imgur.com/payment-icon.png")
            embed.add_field(name="🏦 Ngân Hàng", value="Ngân hàng TMCP Quân đội (MB)", inline=True)
            embed.add_field(name="👤 Chủ Tài Khoản", value="", inline=True)
            embed.add_field(name="💳 Số Tài Khoản", value="", inline=False)  # Cập nhật từ phản hồi mẫu
            embed.add_field(name="💰 Số Tiền", value=f"{sotien:,} VNĐ", inline=True)
            embed.add_field(name="📝 Nội Dung", value=f"`{noi_dung}`", inline=True)
            embed.add_field(name="🔗 Link Thanh Toán", value=f"[Thanh Toán Ngay]({url_thanh_toan})", inline=False)
            embed.add_field(
                name="📋 Hướng Dẫn",
                value=f"- Tối thiểu: {SO_TIEN_TOI_THIEU:,} VNĐ.\n- Quét mã QR bằng ứng dụng ngân hàng.\n- Đảm bảo ghi đúng nội dung chuyển khoản.",
                inline=False
            )
            embed.set_footer(text="🔒 Bảo mật bởi PayOS | Hỗ trợ: ")
            if qr_code:
                embed.set_image(url=qr_code)  # Dùng QR code từ phản hồi PayOS

            await interaction.followup.send(embed=embed, ephemeral=False)

            # Kiểm tra trạng thái thanh toán
            await kiem_tra_trang_thai_thanh_toan(interaction, ma_giao_dich, sotien)

        except Exception as e:
            embed_loi = discord.Embed(
                title="❌ Lỗi Thanh Toán",
                description=f"Đã xảy ra lỗi: {str(e)}\nVui lòng thử lại hoặc liên hệ hỗ trợ.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_loi, ephemeral=True)
        finally:
            ket_thuc_giao_dich(ten_nguoi_dung)

    @bot.tree.command(name="huygiaodich", description="Hủy một giao dịch thanh toán")
    @app_commands.describe(ma_giao_dich="Mã giao dịch cần hủy")
    async def huy_giao_dich(interaction: discord.Interaction, ma_giao_dich: int):
        await interaction.response.defer(ephemeral=True)
        try:
            thong_tin_link_thanh_toan = goi_api(
                "POST",
                f"/v2/payment-requests/{ma_giao_dich}/cancel",
                {"cancellationReason": "Người dùng yêu cầu hủy"}
            )
            if not thong_tin_link_thanh_toan or 'data' not in thong_tin_link_thanh_toan:
                raise Exception(f"Lỗi hủy giao dịch: {thong_tin_link_thanh_toan}")

            if thong_tin_link_thanh_toan['data'].get('status') == 'CANCELLED':
                embed = discord.Embed(
                    title="✅ Đã Hủy Giao Dịch",
                    description=f"Giao dịch `{ma_giao_dich}` đã được hủy.",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Hệ thống PayOS")
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                raise Exception(f"Lỗi trạng thái hủy: {thong_tin_link_thanh_toan['data'].get('status')}")
        except Exception as e:
            embed_loi = discord.Embed(
                title="❌ Lỗi Hủy Giao Dịch",
                description=f"Đã xảy ra lỗi: {e}\nVui lòng kiểm tra mã giao dịch.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed_loi, ephemeral=True)


async def kiem_tra_trang_thai_thanh_toan(interaction: discord.Interaction, ma_giao_dich: int, sotien: int) -> None:
    """Vòng lặp kiểm tra trạng thái thanh toán định kỳ cho đến khi có kết quả hoặc hết thời gian chờ."""
    thoi_gian_bat_dau = time.time()
    while True:
        try:
            thong_tin_thanh_toan = goi_api("GET", f"/v2/payment-requests/{ma_giao_dich}")
            if not thong_tin_thanh_toan or 'data' not in thong_tin_thanh_toan:
                raise Exception(f"Lỗi lấy trạng thái thanh toán: {thong_tin_thanh_toan}")

            trang_thai_thanh_toan = thong_tin_thanh_toan['data'].get('status')
            if trang_thai_thanh_toan == "PAID":
                embed_thanh_cong = discord.Embed(
                    title="🎉 Thanh Toán Thành Công",
                    description=f"Giao dịch `{ma_giao_dich}` với **{sotien:,} VNĐ** đã hoàn tất.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed_thanh_cong.set_thumbnail(url="https://i.imgur.com/success-icon.png")
                embed_thanh_cong.set_footer(text="Cảm ơn bạn! | Hệ thống PayOS")
                await interaction.followup.send(embed=embed_thanh_cong, ephemeral=False)
                return
            elif trang_thai_thanh_toan in ["CANCELLED", "FAILED", "EXPIRED"]:
                embed_trang_thai = discord.Embed(
                    title="⚠️ Trạng Thái Giao Dịch",
                    description=f"Giao dịch `{ma_giao_dich}` đã `{trang_thai_thanh_toan.lower()}`.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed_trang_thai, ephemeral=True)
                return
            elif time.time() - thoi_gian_bat_dau > THOI_GIAN_CHO:
                try:
                    goi_api("POST", f"/v2/payment-requests/{ma_giao_dich}/cancel", {"cancellationReason": "Hết thời gian chờ"})
                except Exception as e:
                    logging.error(f"Lỗi hủy giao dịch hết thời gian {ma_giao_dich}: {e}")
                embed_het_thoi_gian = discord.Embed(
                    title="⏰ Hết Thời Gian",
                    description=f"Giao dịch `{ma_giao_dich}` đã bị hủy do hết thời gian chờ.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed_het_thoi_gian, ephemeral=True)
                return
        except Exception as e:
            logging.error(f"Lỗi kiểm tra trạng thái cho {ma_giao_dich}: {e}")
        await asyncio.sleep(5)
