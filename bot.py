import asyncio
import json
import logging
import os
from pathlib import Path

import discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
CONFIG_PATH = Path("config.json")
UP = "<:ZH_up:1575164531884425256>"
DOWN = "<:ZH_down:1575164566822977648>"
OTHER = "<:ZH_other:1575164741351907468>"


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit("Missing config.json. Copy config.example.json and edit it.")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


async def tcp_check(host: str, port: int, timeout: float) -> bool:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError, TimeoutError):
        return False


class StatusBot(discord.Client):
    def __init__(self, config):
        super().__init__(intents=discord.Intents.none())
        self.config = config
        self.failures = {node["name"]: 0 for node in config["nodes"]}
        self.states = {node["name"]: "unknown" for node in config["nodes"]}

    async def on_ready(self):
        logging.info("Connected as %s", self.user)
        self.loop.create_task(self.monitor_loop())

    async def monitor_loop(self):
        await self.wait_until_ready()
        channel = self.get_channel(int(self.config["channel_id"]))
        if channel is None:
            channel = await self.fetch_channel(int(self.config["channel_id"]))
        message = await channel.fetch_message(int(self.config["message_id"]))
        while not self.is_closed():
            lines = []
            for node in self.config["nodes"]:
                name, host, port = node["name"], node["host"], int(node["port"])
                ok = await tcp_check(host, port, float(self.config["timeout_seconds"]))
                if ok:
                    self.failures[name] = 0
                    self.states[name] = "operational"
                else:
                    self.failures[name] += 1
                    if self.failures[name] >= int(self.config["failures_before_down"]):
                        self.states[name] = "down"

                state = self.states[name]
                emoji = UP if state == "operational" else DOWN if state == "down" else OTHER
                label = "Operational" if state == "operational" else "Down" if state == "down" else "Checking"
                lines.append(f"{emoji} | {name} - {label}")

            try:
                await message.edit(content="\n".join(lines))
            except discord.HTTPException:
                logging.exception("Could not update status message")
            await asyncio.sleep(int(self.config["interval_seconds"]))


config = load_config()
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise SystemExit("DISCORD_TOKEN environment variable is missing.")

StatusBot(config).run(token)
