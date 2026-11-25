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

Nodes are checked by sending a UDP probe to each configured tunnel endpoint (`host` and `port`). The bot marks a node operational only when it receives a UDP response before the configured timeout, and marks it down after the configured number of consecutive failed probes.

**Important:** UDP has no connection handshake. The service behind the tunnel must reply to the probe packet (`ZATCHHOST_STATUS_PING`) for this check to work. A silent UDP service will be reported as down even if its tunnel is running. This checks the configured UDP service's response, not full system health.
