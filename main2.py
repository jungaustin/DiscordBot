from typing import Final
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
from dotenv import load_dotenv
from discord import Intents, Client, Message, app_commands, Interaction, Embed, File
from discord.ext import commands
import json
import sqlite3
from blackjack import play_blackjack, combine_images, hit, stand, check_response, send_hand, count_val
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
        player, computer, deck_id = play_blackjack()
        await send_hand(ctx, player, "Player")
        await send_hand(ctx, computer, "Computer")
        done = False
        while not done:
            await ctx.send("Do you want to **Hit** or **Stand**? (Reply with 'h' or 's')")
            player, computer, deck_id, done = await check_response(bot, ctx, player, computer, deck_id)
            await send_hand(ctx, player, "Player")
            await send_hand(ctx, computer, "Computer", done)
    except Exception as e:
        print(e)
    player_count = count_val(player)
    computer_count = count_val(computer)
    if(computer_count > 21 or (player_count > computer_count and player_count <= 21)):
        await ctx.send("You Win!!!")
    elif(player_count > 21 or (player_count < computer_count and computer_count <= 21)):
        await ctx.send("You Lose")
    else:
        await ctx.send("Tie!!!")
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
