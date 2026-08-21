import logging


def thiet_lap_logging() -> None:
    """Cấu hình ghi log cho toàn bộ ứng dụng."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
