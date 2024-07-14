import discord
from discord.ext import commands
import requests

with open('auth_token.txt', 'r') as file:
    TOKEN = file.read().strip()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def get_motivational_quote(): #! Motivate
    url = "https://zenquotes.io/api/random"
    response = requests.get(url)
    return response.json()[0]['q']

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='motivate') #! Motivate
async def motivate(ctx):
    try:
        quote = get_motivational_quote()
        await ctx.send(quote)
    except requests.exceptions.RequestException as e:
        await ctx.send("Error fetching motivational quote, API not responsive")

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(name='help')
async def help_command(ctx):
    help_text = """
    **Here are the available commands:**
    - `!motivate`: Get a motivational quote.
    - `!ping`: Check the bot's responsiveness.
    - `!help`: Show this help message.
    """
    await ctx.send(help_text)


bot.run(TOKEN)

