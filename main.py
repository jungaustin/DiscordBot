from typing import Final
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
from dotenv import load_dotenv
from discord import Intents, Client, Message, app_commands, Interaction, Embed
from discord.ext import commands
from responses import get_response, get_waifu
from blackjack import play_blackjack, combine_images, hit, stand, check_response, send_hand, count_val
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
        if not is_private:
            async with message.channel.typing():
                response: str = get_response(user_message, str(message.author))
                if (response != "*dnr*"):
                    await message.channel.send(response)
                else:
                    print("dnr")
        else:
            response: str = get_response(user_message, str(message.author))
            if (response != "*dnr*"):
                await message.author.send(response)
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

@bot.hybrid_command()
async def bj(ctx: commands.Context, points:int = 0):
    currPoints = numPoints(ctx)
    if(points > currPoints):
        await ctx.send("You do not have enough points. This game will be played with no stakes.")
        points = 0
    if(points < 0):
        await ctx.send("You can't do negative betting. This game will be played with no stakes.")
        points = 0
    natural_blackjack = False
    player = computer = deck_id = None
    try:
        player, computer, deck_id = play_blackjack()
        done = False
        msg = ""
        player_count = count_val(player)
        computer_count = count_val(computer)
        if (player_count == 21 and computer_count == 21):
            done = True
            natural_blackjack = True
            msg = "Both the Dealer and the Player have natural Blackjacks!"
            points = 0
        elif(player_count == 21):
            done = True
            natural_blackjack = True
            msg = "You have a natural Blackjack! You win 2.5x {}}"
            points = int(points*2.5)
        elif (computer_count == 21):
            done = True
            natural_blackjack = True
            msg = "Dealer has a natural Blackjack. You Lose."
            points *= -1
        await send_hand(ctx, player, "Player", done)
        await send_hand(ctx, computer, "Computer", done)
        if (msg != ""):
            await ctx.send(msg)
        while not done:
            await ctx.send("Do you want to **Hit** or **Stand**? (Reply with 'h' or 's')")
            player, computer, deck_id, done = await check_response(bot, ctx, player, computer, deck_id)
            await send_hand(ctx, player, "Player")
            await send_hand(ctx, computer, "Computer", done)
        player_count = count_val(player)
        computer_count = count_val(computer)
        if(computer_count > 21 or (player_count > computer_count and player_count <= 21)):
            await ctx.send("You Win!!!")
        elif(player_count > 21 or (player_count < computer_count and computer_count <= 21)):
            await ctx.send("You Lose :3. Try again!")
            if not natural_blackjack:
                points *= -1
        else:
            await ctx.send("No one wins, and your points will be returned.")
            points = 0
        add_points(ctx, points)
        await bot.get_command('points').invoke(ctx)
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

def numPoints(ctx: commands.Context):
    curr_server, connection, cursor, currUser = initialize(ctx)
    connection.commit()
    connection.close()
    return currUser[2]

@bot.hybrid_command()
async def points(ctx: commands.Context):
    points = numPoints(ctx)
    await ctx.send(f'You currently have {points} points!')

def add_points(ctx, num:int):
    curr_server, connection, cursor, currUser = initialize(ctx)
    if currUser:
        user_id, user, points, check_in_date = currUser
        points += num
        cursor.execute(f'''
                        UPDATE {curr_server}
                        SET
                            points = ?
                        WHERE user_id = ?
                        ''', (points, user_id))
    connection.commit()
    connection.close()
    return points

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

# Step 4: Handling incoming messages
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

# #Delete for above later
# @bot.event
# async def on_message(message: Message) -> None:
#     if message.content.startswith(bot.command_prefix):
#         await bot.process_commands(message)
#         return

#Step 5: Main Entry Point
def main() -> None:
    bot.run(token=TOKEN)

if __name__ == '__main__':
    main()
