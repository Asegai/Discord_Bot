import discord
from discord.ext import commands
from discord import app_commands
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import re
import os
import shutil


class MiscellaneousCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.api_ninjas_key = None
        self.current_trivia = {}
        self.category_map = {
            'science': 'sciencenature',
            'math': 'mathematics',
            'geography': 'geography',
            'entertainment': 'entertainment',
            'history': 'historyholidays',
            'games': 'toysgames'
        }
        self.scheduler.start()

    def get_motivational_quote(self):
        url = "https://zenquotes.io/api/random"
        response = requests.get(url)
        if response.status_code == requests.codes.ok:
            return response.json()[0]['q']
        else:
            return "Error fetching motivational quote, API not responsive"

    def get_dad_joke(self):
        api_url = f'https://api.api-ninjas.com/v1/dadjokes'
        response = requests.get(api_url, headers={'X-Api-Key': self.api_ninjas_key})
        if response.status_code == requests.codes.ok:
            return response.json()[0]['joke']
        else:
            return "Error fetching dad joke, API not responsive"

    def get_trivia_question(self, category):
        api_url = f'https://api.api-ninjas.com/v1/trivia?category={category}'
        response = requests.get(api_url, headers={'X-Api-Key': self.api_ninjas_key})
        if response.status_code == requests.codes.ok:
            return response.json()[0]
        else:
            return "Error fetching trivia question, API not responsive"

    def set_reminder(self, user_id, channel_id, message, remind_time):
        async def send_reminder():
            channel = self.bot.get_channel(channel_id)
            user = self.bot.get_user(user_id)
            await channel.send(f"{user.mention}, here is your reminder: {message}")

        self.scheduler.add_job(send_reminder, trigger=DateTrigger(run_date=remind_time))

    def parse_time(self, time_str):
        match = re.match(r"(\d+)([mhds])", time_str)
        if not match:
            raise ValueError("Invalid time format")

        amount, unit = int(match.group(1)), match.group(2)
        if unit == 'm':
            return datetime.now() + timedelta(minutes=amount)
        elif unit == 'h':
            return datetime.now() + timedelta(hours=amount)
        elif unit == 'd':
            return datetime.now() + timedelta(days=amount)
        elif unit == 's':
            return datetime.now() + timedelta(seconds=amount)
        else:
            raise ValueError("Invalid time unit")

    @commands.command(name='trivia')
    async def trivia(self, ctx, category: str = None):
        if category is None:
            await ctx.send("Please specify a category. Available categories: Science, Math, Geography, Entertainment, History, Games")
            return

        category_key = category.lower()
        if category_key not in self.category_map:
            await ctx.send("Invalid category. Available categories: Science, Math, Geography, Entertainment, History, Games")
            return

        trivia_data = self.get_trivia_question(self.category_map[category_key])
        if trivia_data is None:
            await ctx.send("Error fetching trivia question, API not responsive")
            return

        self.current_trivia['question'] = trivia_data['question']
        self.current_trivia['answer'] = trivia_data['answer']
        self.current_trivia['answered'] = False
        print(self.current_trivia['answer'])
        await ctx.send(f"Trivia question in {category.capitalize()} category: {trivia_data['question']}\nUse `!answer your_answer` to answer!")

    @commands.command(name='answer')
    async def answer(self, ctx, *, user_answer: str):
        if not self.current_trivia or self.current_trivia.get('answered', False):
            await ctx.send("There is no active trivia question or it has already been answered.")
            return

        correct_answer = self.current_trivia.get('answer', '').lower()
        correct_words = set(correct_answer.split())
        user_words = set(user_answer.lower().split())

        if correct_words & user_words:
            self.current_trivia['answered'] = True
            await ctx.send(f"Congratulations {ctx.author.mention}! You answered correctly. The answer is indeed '{correct_answer.capitalize()}'.")
        else:
            await ctx.send(f"Sorry {ctx.author.mention}, that's not the correct answer. Try again!")

    @commands.command(name='motivate')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def motivate(self, ctx):
        try:
            quote = self.get_motivational_quote()
            await ctx.send(quote)
        except requests.exceptions.RequestException:
            await ctx.send("Error fetching motivational quote, API not responsive")
        except commands.CommandOnCooldown as e:
            await ctx.send(f"This command is on cooldown. Please try again in {e.retry_after:.2f} seconds.")

    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send('Pong!')

    @commands.command(name='help')
    async def help_command(self, ctx):
        help_text = """
        **Here are the available commands:**
        - `!motivate`: Get a motivational quote. (or use the slash command)
        - `!ping`: Check the bot's responsiveness.
        - `!help`: Show this help message.
        - `!dadjoke`: Get a dad joke. (or use the slash command)
        - `!trivia <category>`: Get a trivia question from the specified category. (or use the slash command)
        - `!answer <your_answer>`: Answer the current trivia question.  (or use the slash command)
        - `!qrcode <url>`: Generate a QR code for the specified URL. (or use the slash command)
        - `!whatsthismean <word>`: Get the definition of a word. (or use the slash command)
        - `/remindme <message> <time>`: Set a reminder. Time format: <number><unit> (e.g. 10s, 5m, 1h, 2d) 
        - `!kick <member> [reason]`: Kick a user from the server.
        - `!silence <member> <time>`: Mute a user for a specified duration. Admin Only
        - `!unsilence <member>`: Unmute a user. Admin Only
        - `!ban <member> [reason]`: Ban a user from the server. Admin Only
        - `!unban <user_id> [reason]`: Unban a user from the server. Admin Only
        - `!lockdown`: Lockdown the server. Admin Only
        - `!unlock`: Unlock the server. Admin Only
        - `!music <song_name>`: Play a song from YouTube. (or use the slash command)
        - `!stop`: Stop playing music and disconnect from the voice channel. (or use the slash command)
        - `!pause`: pause the currently playing song. (or use the slash command)
        - `!resume`: resume the currently playing song if paused. (or use the slash command)
        - `/ninja_api_key <api_key>` : Set the Ninja API key you got from https://api-ninjas.com, No one else can see this command, Admin Only
        """
        await ctx.send(help_text)

    @commands.command(name='dadjoke')    
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dadjoke(self, ctx):
        try:
            joke = self.get_dad_joke()
            await ctx.send(joke)
        except requests.exceptions.RequestException:
            await ctx.send("Error fetching dad joke, API not responsive")
        except commands.CommandOnCooldown as e:
            await ctx.send(f"This command is on cooldown. Please try again in {e.retry_after:.2f} seconds.")

    @app_commands.command(name='ninja_api_key', description='Set the Ninja API key')
    @app_commands.describe(api_key="Your Ninja API key")
    @commands.has_permissions(administrator=True)
    async def set_ninja_api_key(self, interaction: discord.Interaction, api_key: str):
        self.api_ninjas_key = api_key
        await interaction.response.send_message("API key set successfully.")

    @app_commands.command(name='qrcode', description='Generate a QR code')
    @app_commands.describe(url = "URL that the QR code will link to")
    async def generate_qr(self, interaction: discord.Interaction, url: str):
        fmt = 'png'
        api_url = f'https://api.api-ninjas.com/v1/qrcode?data={url}&format={fmt}'
        response = requests.get(api_url, headers={'X-Api-Key': self.api_ninjas_key, 'Accept': 'image/png'}, stream=True)
        
        if response.status_code == requests.codes.ok:
            with open('qrcode.png', 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            
            await interaction.response.send_message(file=discord.File('qrcode.png'))
            os.remove('qrcode.png')
        else:
            await interaction.response.send_message(f"Error: {response.status_code} {response.text}")

    @app_commands.command(name='whatsthismean', description='Get the definition of a word')
    @app_commands.describe(word = "Word to look up")
    async def whatsthismean(self, interaction: discord.Interaction, word: str):
        api_url = 'https://api.api-ninjas.com/v1/dictionary?word={}'
        response = requests.get(api_url.format(word), headers={'X-Api-Key': self.api_ninjas_key})
        if response.status_code == requests.codes.ok:
            data = response.json()
            if data['valid']:
                definition = data['definition']
                await interaction.response.send_message(f"**{word.capitalize()}**: {definition}")
            else:
                await interaction.response.send_message(f"No definition found for the word: {word}")
        else:
            await interaction.response.send_message(f"Error: {response.status_code} - {response.text}")

    @app_commands.command(name="trivia", description="Get a trivia question")
    @app_commands.describe(category = "Category of the trivia question: Science, Math, Geography, Entertainment, History, or Games")
    async def slash_trivia(self, interaction: discord.Interaction, category: str):
        category_key = category.lower()
        if category_key not in self.category_map:
            await interaction.response.send_message("Invalid category. Available categories: Science, Math, Geography, Entertainment, History, Games")
            return

        trivia_data = self.get_trivia_question(self.category_map[category_key])
        if trivia_data is None:
            await interaction.response.send_message("Error fetching trivia question, API not responsive")
            return

        self.current_trivia['question'] = trivia_data['question']
        self.current_trivia['answer'] = trivia_data['answer']
        self.current_trivia['answered'] = False
        print(self.current_trivia['answer'])

        await interaction.response.send_message(f"Trivia question in {category.capitalize()} category: {trivia_data['question']}\nUse `/answer your_answer` to answer!")

    @app_commands.command(name="answer", description="Answer the current trivia question")
    @app_commands.describe(user_answer = "Your answer to the trivia question")
    async def slash_answer(self, interaction: discord.Interaction, user_answer: str):
        if not self.current_trivia or self.current_trivia.get('answered', False):
            await interaction.response.send_message("There is no active trivia question or it has already been answered.")
            return
        correct_answer = self.current_trivia.get('answer', '').lower()
        correct_words = set(correct_answer.split())
        user_words = set(user_answer.lower().split())

        if correct_words & user_words:
            self.current_trivia['answered'] = True
            await interaction.response.send_message(f"Congratulations {interaction.user.mention}! You answered correctly. The answer is indeed '{correct_answer.capitalize()}'.")
        else:
            await interaction.response.send_message(f"Sorry {interaction.user.mention}, that's not the correct answer. Try again!")

    @app_commands.command(name="remindme", description="Set a reminder")
    @app_commands.describe(message = "Message for the reminder", time = "Time duration for the reminder, e.g. 10s (10 seconds), 5m (5 minutes), 1h (1 hour), 2d (2 days)")
    async def remindme(self, interaction: discord.Interaction, message: str, time: str):
        try:
            remind_time = self.parse_time(time)
            self.set_reminder(interaction.user.id, interaction.channel_id, message, remind_time)
            await interaction.response.send_message(f"Reminder set for {time} with message: {message}")
        except ValueError as e:
            await interaction.response.send_message(str(e))

