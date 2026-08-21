# PayOS Payment Bot

A Discord bot that creates and tracks [PayOS](https://payos.vn/) payment links, with a Flask webhook to receive real-time payment status updates.

🇻🇳 Vietnamese version: [README.vi.md](./README.vi.md)

## Features

- `/thanhtoan <amount>` — creates a PayOS payment link (QR code + checkout URL), then polls the payment status until it's paid, cancelled, failed, or times out.
- `/huygiaodich <order_code>` — cancels an existing payment request.
- `POST /webhook` — receives PayOS webhook events (signature-verified) and posts an update embed to a staff channel.
- Basic anti-abuse protections: per-user cooldown between attempts, and a cap on concurrent open transactions per user.

## Project Structure

```
payos_bot/
├── main.py                       # Entry point: builds the bot + Flask app, runs both
├── constants/
│   └── config.py                 # Env vars and constants (min amount, timeouts, etc.)
├── utils/
│   └── logging_config.py         # Logging setup
├── model/
│   └── transaction_store.py      # In-memory transaction/rate-limit state
├── services/
│   ├── payos_service.py          # PayOS API calls, signature creation/verification
│   └── webhook_service.py        # Flask app + /webhook route
└── command/
    └── payment_commands.py       # Discord slash commands (/thanhtoan, /huygiaodich)
```

Module responsibilities:

| Layer | Responsibility |
|---|---|
| `constants` | All configuration values — nothing else should read `os.getenv` directly. |
| `utils` | Cross-cutting helpers (currently just logging). |
| `model` | In-memory state for open transactions and rate limiting. |
| `services` | External I/O: calling the PayOS API, verifying/creating HMAC signatures, the Flask webhook. |
| `command` | Discord-facing slash commands, built on top of `model` + `services`. |

## Requirements

- Python 3.9+
- A Discord bot application with the `applications.commands` scope enabled
- A PayOS merchant account (Client ID, API Key, Checksum Key)

## Installation

```bash
git clone <your-repo-url>
cd payos_bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install discord.py requests python-dotenv flask beautifulsoup4
```

## Configuration

Create a `.env` file in the project root:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
STAFF_CHANNEL_ID=your_channel_id
PAYOS_CLIENT_ID=your_payos_client_id
PAYOS_API_KEY=your_payos_api_key
PAYOS_CHECKSUM_KEY=your_payos_checksum_key
```

| Variable | Description |
|---|---|
| `DISCORD_BOT_TOKEN` | Discord bot token from the [Developer Portal](https://discord.com/developers/applications) |
| `STAFF_CHANNEL_ID` | Channel ID where webhook status updates are posted |
| `PAYOS_CLIENT_ID` | PayOS Client ID |
| `PAYOS_API_KEY` | PayOS API Key |
| `PAYOS_CHECKSUM_KEY` | PayOS Checksum Key (used to sign/verify requests and webhooks) |

Other tunables live in `constants/config.py`:

- `SO_TIEN_TOI_THIEU` — minimum payment amount (default 2,000 VND)
- `THOI_GIAN_CHO` — how long to poll a payment before auto-cancelling (default 300s)
- `THOI_GIAN_GIOI_HAN` — cooldown between attempts per user (default 60s)
- `SO_LAN_TOI_DA_MOI_NGUOI` — max concurrent open transactions per user (default 3)
- `WEBHOOK_HOST` / `WEBHOOK_PORT` — Flask bind address/port (default `0.0.0.0:5500`)

## Running

```bash
python main.py
```

This starts:
1. The Discord bot, in a background thread.
2. The Flask webhook server (`/webhook`), on the main thread.

Point your PayOS webhook URL to `http://<your-server>:5500/webhook` (behind a reverse proxy with HTTPS in production).

## Notes

- Transaction state is kept **in memory** — it resets if the process restarts. For production use with multiple workers, back this with Redis or a database instead of `model/transaction_store.py`'s dict.
- The bank account name/number fields in the payment embed (`command/payment_commands.py`) are left blank — fill them in with your actual account details, or pull them from the PayOS response if available.
- Logs are written to `bot.log` as well as stdout.

## License

This project is open source and released under the **GNU General Public License v3.0 (GPL-3.0)**.
