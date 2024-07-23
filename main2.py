from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

# Load token from .env file
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True  # Enable the privileged message content intent

bot = commands.Bot(command_prefix="||", intents=intents)

@bot.hybrid_command()
async def ping(ctx: commands.Context):
    await ctx.send("pong")

# @bot.tree.command(name="say")
# @app_commands.describe(message="what to say")
# async def say(interaction: discord.Interaction, message: str):
#     await interaction.response.send_message(f"{interaction.user.mention} said: {message}")

@bot.event
async def on_ready():
    print("Bot is ready")
    try:
        # Sync commands to a specific guild for faster testing
        guild = discord.Object(id='720796796762325005')  # replace with your guild id
        #await bot.tree.sync(guild=guild)
        synced = await bot.tree.sync(guild=guild)
    except Exception as e:
        print(e)

bot.run(TOKEN)
