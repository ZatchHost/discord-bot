# ZatchHost Discord Status Bot

A small Discord bot that periodically checks configured hosting nodes and updates a single status message.

## Requirements

- Python 3.11+
- A Discord bot token
- A channel where the bot can view and edit messages

## Setup

1. Copy `config.example.json` to `config.json` and configure nodes and Discord IDs.
2. Set `DISCORD_TOKEN` in your environment.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Run: `python bot.py`

Keep `config.json` and your token private. Do not commit credentials.

## Checks

Nodes use ICMP ping checks against their configured tunnel hostname or IP address (`host`). A node is marked down only after the configured consecutive failures. This verifies that the tunnel endpoint responds to ping; it does not verify that Proxmox or services behind the tunnel are healthy. The machine running the bot must have the system `ping` utility installed and be allowed to send ICMP packets.
