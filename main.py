from typing import Final
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
from dotenv import load_dotenv
from discord import Intents, Client, Message, app_commands, Interaction, Embed
from discord.ext import commands
from responses import get_response, get_waifu
import json
import sqlite3
from datetime import datetime



talk_to_ai = False

#Step 0: Load Out Token from Somewhere Safe
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')


#Step 1: Bot Setup
intents: Intents = Intents.all()
intents.message_content = True  # NOQA
#client: Client = Client(intents=intents)
bot: commands.Bot = commands.Bot(command_prefix="|", intents = intents)

#Step 2: Message Functionality
async def send_message(message : Message, user_message : str) -> None:
    if not user_message:
        print("Message was empty because intents were not enabled")
        return
    
    if is_private := user_message[0] == '!':
        user_message = user_message[1:]
        
    try:
        response: str = get_response(user_message, str(message.author))
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

@bot.hybrid_command()
async def greet(ctx: commands.Context):
    await ctx.send("Hello, world!")

@bot.hybrid_command()
async def getwaifu(ctx: commands.Context):
    try:
        data = get_waifu()
        embed = Embed(
                # title = "Title",
                # description = "Body of the embed. This is the description"
                )
        embed.set_image(url = data['images'][0]['url'])
        # embed.set_footer(text = 'This is a footer')
        # embed.set_author(name = 'Author name')
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)

def initialize(ctx: commands.Context):
    curr_server = 'dailies_' + str(ctx.guild.id)
    connection = sqlite3.connect('dailies.db')
    cursor = connection.cursor()
    cursor.execute(f'''
                   CREATE TABLE IF NOT EXISTS {curr_server}(
                       user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user TEXT NOT NULL,
                       points INTEGER NOT NULL DEFAULT 0,
                       check_in_date TEXT)
                   ''')
    cursor.execute(f'''
                   SELECT * FROM {curr_server} WHERE user = ?
                   ''', (ctx.author.name,))
    currUser = cursor.fetchone()
    if not currUser:
        cursor.execute(f'''
                    INSERT INTO {curr_server} (user)
                    VALUES(?)
                    ''', (ctx.author.name,))
        cursor.execute(f'''
                    SELECT * FROM {curr_server} WHERE user = ?
                    ''', (ctx.author.name,))
        currUser = cursor.fetchone()
    return curr_server, connection, cursor, currUser
@bot.hybrid_command()
async def points(ctx: commands.Context):
    curr_server, connection, cursor, currUser = initialize(ctx)
    await ctx.send(f'You currently have {currUser[2]} points!')
    connection.commit()
    connection.close()
    
@bot.hybrid_command()
async def dailies(ctx: commands.Context):
    curr_server, connection, cursor, currUser = initialize(ctx)
    if currUser:
        user_id, user, points, check_in_date = currUser
        if check_in_date is None or check_in_date != datetime.now().strftime('%Y-%m-%d'):
            points += 100
            check_in_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(f'''
                            UPDATE {curr_server}
                            SET
                                points = ?,
                                check_in_date = ?
                            WHERE user_id = ?
                           ''', (points, check_in_date, user_id))
            await ctx.send(f"Hello {user}. You have successfully checked in! You currently have {points} points")
        else:
            await ctx.send(f"Hello {user}. You have already checked in for today.")
            
    
    connection.commit()
    connection.close()

@bot.hybrid_command()
async def gpton(ctx: commands.Context):
    global talk_to_ai
    talk_to_ai = True
    await ctx.send("Sylvester Bot is now active!")
@bot.hybrid_command()
async def gptoff(ctx: commands.Context):
    global talk_to_ai
    talk_to_ai = False
    await ctx.send("Sylvester Bot is now inactive!")
@bot.hybrid_command()
async def gpttoggle(ctx: commands.Context):
    global talk_to_ai
    talk_to_ai = not talk_to_ai
    if talk_to_ai:
        await ctx.send("Sylvester Bot is now active!")
    else:
        await ctx.send("Sylvester Bot is now inactive!")
    
# @bot.hybrid_command()
# async def lastLeagueMatch(ctx: commands.Context, username: str):
#     data = last_league_match(username)

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
    if talk_to_ai:
        if message.author == bot.user:
            return
        if (message.channel.id != 1264845768108544051) and (message.channel.id !=1264743004002848778):
            return
        
        # return 
        # comment out later
        username: str = str(message.author)
        user_message: str = message.content
        channel: str = str(message.channel)
        print(f'[{channel}] {username}: "{user_message}"')
        await send_message(message, user_message)
    
#Step 5: Main Entry Point
def main() -> None:
    bot.run(token=TOKEN)

if __name__ == '__main__':
    main()
