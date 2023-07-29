import os
from discord.ext import commands
import discord
from loguru import logger
import json

with open("data/config.json") as f:
    data = json.load(f)

token = data["token"]
intents = discord.Intents.default()
bot = discord.Bot(intents=intents, help_command=None)

def load_cogs():
    for file in os.listdir("cogs"):
        if file.endswith("slash.py"):
            name = file[:-3]
            bot.load_extension(f"cogs.{name}")
            logger.info(f"Loaded cogs.{name}")



load_cogs()

bot.run(token)
