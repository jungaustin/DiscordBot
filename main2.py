from typing import Final
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
from dotenv import load_dotenv
from discord import Intents, Client, Message, app_commands, Interaction, Embed, File
from discord.ext import commands
import json
import sqlite3
from blackjack import play_blackjack, combine_images
from PIL import Image
from io import BytesIO
import requests
import asyncio


#Step 0: Load Out Token from Somewhere Safe
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')


#Step 1: Bot Setup
intents: Intents = Intents.all()
intents.message_content = True  # NOQA
#client: Client = Client(intents=intents)
bot: commands.Bot = commands.Bot(command_prefix="|", intents = intents)


@bot.hybrid_command()
async def blackjack(ctx: commands.Context):
    try:
        player, computer = play_blackjack()
        player_hand_image_binary = combine_images(player)
        embed = Embed(title="Player's Cards")
        embed.set_image(url="attachment://blackjack_combined.png")
        await ctx.send(file=File(fp=player_hand_image_binary, filename='blackjack_combined.png'), embed=embed)
        computer_image_binary = combine_images(computer, True)
        embed = Embed(title="Computer's Cards")
        embed.set_image(url="attachment://blackjack_combined.png")
        await ctx.send(file=File(fp=computer_image_binary, filename='blackjack_combined.png'), embed=embed)
        await ctx.send("Do you want to **Hit** or **Stand**? (Reply with 'h' or 's')")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['h', 's']
        try:
            # Wait for the player's response for 30 seconds
            message = await bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("Time is up! Automatically Stood!")
            return

    except Exception as e:
        print(e)
#Step 3: Handling the startup for the bot
@bot.event 
async def on_ready() -> None:
    print(f'{bot.user} is now running!')
    try:
        # Sync commands globally or for a specific guild
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        commands_list = bot.tree.get_commands()
        print("Commands:", [command.name for command in commands_list])
    except Exception as e:
        print(f"Error syncing commands: {e}")

#Step 4: Handling incoming messages
@bot.event
async def on_message(message: Message) -> None:
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return
    
#Step 5: Main Entry Point
def main() -> None:
    bot.run(token=TOKEN)

if __name__ == '__main__':
    main()
