from typing import Final
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
from dotenv import load_dotenv
from discord import Intents, Client, Message, app_commands, Interaction, Embed
from discord.ext import commands
from responses import get_response, get_waifu

#Step 0: Load Out Token from Somewhere Safe
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

#Step 1: Bot Setup
intents: Intents = Intents.all()
intents.message_content = True  # NOQA
#client: Client = Client(intents=intents)
bot: commands.Bot = commands.Bot(command_prefix="/", intents = intents)

#Step 2: Message Functionality
async def send_message(message : Message, user_message : str) -> None:
    if not user_message:
        print("Message was empty because intents were not enabled")
        return
    
    if is_private := user_message[0] == '?':
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
    print("in command")
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
    if message.author == bot.user:
        return
    if (message.channel.id != 1264845768108544051) and (message.channel.id !=1264743004002848778):
        return
    if message.content.startswith('/'):
        await bot.process_commands(message)
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
    #bot.run(token=TOKEN)

if __name__ == '__main__':
    main()