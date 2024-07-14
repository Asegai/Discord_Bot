import discord
from discord.ext import commands
import requests

with open('auth_token.txt', 'r') as file:
    TOKEN = file.read().strip()

with open('api_ninjas_key.txt', 'r') as file:
    api_ninjas_key = file.read().strip()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def get_motivational_quote():
    url = "https://zenquotes.io/api/random"
    response = requests.get(url)
    return response.json()[0]['q']

def get_dad_joke():
    api_url = f'https://api.api-ninjas.com/v1/dadjokes'
    response = requests.get(api_url, headers={'X-Api-Key': api_ninjas_key})
    if response.status_code == requests.codes.ok:
        return response.json()[0]['joke']
    else:
        return "Error fetching dad joke, API not responsive"

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='motivate')
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
    - `!dadjoke`: Get a dad joke.
    """
    await ctx.send(help_text)

@bot.command(name='dadjoke')
async def dadjoke(ctx):
    try:
        joke = get_dad_joke()
        await ctx.send(joke)
    except requests.exceptions.RequestException as e:
        await ctx.send("Error fetching dad joke, API not responsive")

# Slash command for motivate
@bot.tree.command(name="motivate", description="Get a motivational quote")
async def slash_motivate(interaction: discord.Interaction):
    try:
        quote = get_motivational_quote()
        await interaction.response.send_message(quote)
    except requests.exceptions.RequestException as e:
        await interaction.response.send_message("Error fetching motivational quote, API not responsive")

# Slash command for dadjoke
@bot.tree.command(name="dadjoke", description="Get a dad joke")
async def slash_dadjoke(interaction: discord.Interaction):
    try:
        joke = get_dad_joke()
        await interaction.response.send_message(joke)
    except requests.exceptions.RequestException as e:
        await interaction.response.send_message("Error fetching dad joke, API not responsive")

bot.run(TOKEN)
