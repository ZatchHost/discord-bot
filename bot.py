import asyncio
import json
import logging
import os
from pathlib import Path

import discord

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
CONFIG_PATH = Path("config.json")
UP = "<a:ZH_up:1575164531884425256>"
DOWN = "<a:ZH_down:1575164566822977648>"
OTHER = "<a:ZH_other:1575164741351907468>"


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit("Missing config.json. Copy config.example.json and edit it.")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


async def tcp_check(host: str, port: int, timeout: float) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
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
        self.monitor_task = None

    async def on_ready(self):
        logging.info("Connected as %s", self.user)
        if self.monitor_task is None or self.monitor_task.done():
            self.monitor_task = asyncio.create_task(self.monitor_loop())

    async def get_status_message(self, channel):
        message_id = int(self.config.get("message_id", 0))
        if message_id:
            try:
                return await channel.fetch_message(message_id)
            except discord.NotFound:
                logging.warning("Configured status message was deleted; creating a replacement.")

        message = await channel.send("Initializing node status...")
        self.config["message_id"] = message.id
        save_config(self.config)
        logging.info("Created status message with ID %s and saved it to config.json", message.id)
        return message

    async def monitor_loop(self):
        await self.wait_until_ready()
        channel = self.get_channel(int(self.config["channel_id"]))
        if channel is None:
            channel = await self.fetch_channel(int(self.config["channel_id"]))
        message = await self.get_status_message(channel)

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
                await message.edit(content="\n# 🚦 Services status\n_ _\n"+"\n".join(lines))
            except discord.HTTPException:
                logging.exception("Could not update status message")
            await asyncio.sleep(int(self.config["interval_seconds"]))


config = load_config()
token = os.getenv("DISCORD_TOKEN")
if not token:
    raise SystemExit("DISCORD_TOKEN environment variable is missing.")

StatusBot(config).run(token)
