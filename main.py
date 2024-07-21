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


with open('auth_token.txt', 'r') as file:
    TOKEN = file.read().strip()

with open('api_ninjas_key.txt', 'r') as file:
    api_ninjas_key = file.read().strip()


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
scheduler = AsyncIOScheduler()


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
    scheduler.start()
    print(f'{bot.user.name} has connected to Discord!')

current_trivia = {}
category_map = {
    'science': 'sciencenature',
    'math': 'mathematics',
    'geography': 'geography',
    'entertainment': 'entertainment',
    'history': 'historyholidays',
    'games': 'toysgames'
}

def get_trivia_question(category):
    api_url = f'https://api.api-ninjas.com/v1/trivia?category={category}'
    response = requests.get(api_url, headers={'X-Api-Key': api_ninjas_key})
    if response.status_code == requests.codes.ok:
        return response.json()[0]
    else:
        return None

@bot.command(name='trivia')
async def trivia(ctx, category: str = None):
    if category is None:
        await ctx.send("Please specify a category. Available categories: Science, Math, Geography, Entertainment, History, Games")
        return

    category_key = category.lower()
    if category_key not in category_map:
        await ctx.send("Invalid category. Available categories: Science, Math, Geography, Entertainment, History, Games")
        return

    trivia_data = get_trivia_question(category_map[category_key])
    if trivia_data is None:
        await ctx.send("Error fetching trivia question, API not responsive")
        return

    current_trivia['question'] = trivia_data['question']
    current_trivia['answer'] = trivia_data['answer']
    current_trivia['answered'] = False
    print(current_trivia['answer'])
    await ctx.send(f"Trivia question in {category.capitalize()} category: {trivia_data['question']}\nUse `!answer your_answer` to answer!")

@bot.command(name='answer')
async def answer(ctx, *, user_answer: str):
    if not current_trivia or current_trivia.get('answered', False):
        await ctx.send("There is no active trivia question or it has already been answered.")
        return 

    correct_answer = current_trivia.get('answer', '').lower()
    correct_words = set(correct_answer.split())
    user_words = set(user_answer.lower().split())

    if correct_words & user_words:
        current_trivia['answered'] = True
        await ctx.send(f"Congratulations {ctx.author.mention}! You answered correctly. The answer is indeed '{correct_answer.capitalize()}'.")
    else:
        await ctx.send(f"Sorry {ctx.author.mention}, that's not the correct answer. Try again!")

#! Slash command for qrcode
@bot.tree.command(name='qrcode', description='Generate a QR code')
@app_commands.describe(url = "URL that the QR code will link to")
async def generate_qr(interaction: discord.Interaction, url: str):
    fmt = 'png'
    api_url = f'https://api.api-ninjas.com/v1/qrcode?data={url}&format={fmt}'
    response = requests.get(api_url, headers={'X-Api-Key': api_ninjas_key, 'Accept': 'image/png'}, stream=True)
    
    if response.status_code == requests.codes.ok:
        with open('qrcode.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        
        await interaction.response.send_message(file=discord.File('qrcode.png'))
        os.remove('qrcode.png')
    else:
        await interaction.response.send_message(f"Error: {response.status_code} {response.text}")

@bot.command(name='qrcode')
async def generate_qr(ctx, url: str):
    fmt = 'png'
    api_url = f'https://api.api-ninjas.com/v1/qrcode?data={url}&format={fmt}'
    response = requests.get(api_url, headers={'X-Api-Key': api_ninjas_key, 'Accept': 'image/png'}, stream=True)
    
    if response.status_code == requests.codes.ok:
        with open('qrcode.png', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        
        await ctx.send(file=discord.File('qrcode.png'))
        os.remove('qrcode.png')
    else:
        await ctx.send(f"Error: {response.status_code} {response.text}")

#! Slash command for whatsthismean
@bot.tree.command(name='whatsthismean', description='Get the definition of a word')
@app_commands.describe(word = "Word to look up")
async def whatsthismean(interaction: discord.Interaction, word: str):
        api_url = 'https://api.api-ninjas.com/v1/dictionary?word={}'
        response = requests.get(api_url.format(word), headers={'X-Api-Key': api_ninjas_key})
        if response.status_code == requests.codes.ok:
            data = response.json()
            if data['valid']:
                definition = data['definition']
                await interaction.response.send_message(f"**{word.capitalize()}**: {definition}")
            else:
                await interaction.response.send_message(f"No definition found for the word: {word}")
        else:
            await interaction.response.send_message(f"Error: {response.status_code} - {response.text}")

@bot.command(name='whatsthismean')
async def whatsthismean(ctx, word: str):
    api_url = 'https://api.api-ninjas.com/v1/dictionary?word={}'
    response = requests.get(api_url.format(word), headers={'X-Api-Key': api_ninjas_key})
    if response.status_code == requests.codes.ok:
        data = response.json()
        if data['valid']:
            definition = data['definition']
            await ctx.send(f"**{word.capitalize()}**: {definition}")
        else:
            await ctx.send(f"No definition found for the word: {word}")
    else:
        await ctx.send(f"Error: {response.status_code} - {response.text}")  

#! Slash command for trivia
@bot.tree.command(name="trivia", description="Get a trivia question")
@app_commands.describe(category = "Category of the trivia question: Science, Math, Geography, Entertainment, History, or Games")
async def slash_trivia(interaction: discord.Interaction, category: str):
    category_key = category.lower()
    if category_key not in category_map:
        await interaction.response.send_message("Invalid category. Available categories: Science, Math, Geography, Entertainment, History, Games")
        return

    trivia_data = get_trivia_question(category_map[category_key])
    if trivia_data is None:
        await interaction.response.send_message("Error fetching trivia question, API not responsive")
        return

    current_trivia['question'] = trivia_data['question']
    current_trivia['answer'] = trivia_data['answer']
    current_trivia['answered'] = False
    print(current_trivia['answer'])

    await interaction.response.send_message(f"Trivia question in {category.capitalize()} category: {trivia_data['question']}\nUse `/answer your_answer` to answer!")
#! Slash command for answer
@bot.tree.command(name="answer", description="Answer the current trivia question")
@app_commands.describe(user_answer = "Your answer to the trivia question")
async def slash_answer(interaction: discord.Interaction, user_answer: str):
    if not current_trivia or current_trivia.get('answered', False):
        await interaction.response.send_message("There is no active trivia question or it has already been answered.")
        return
    correct_answer = current_trivia.get('answer', '').lower()#
    correct_words = set(correct_answer.split())
    user_words = set(user_answer.lower().split())

    if correct_words & user_words:
        current_trivia['answered'] = True
        await interaction.response.send_message(f"Congratulations {interaction.user.mention}! You answered correctly. The answer is indeed '{correct_answer.capitalize()}'.")
    else:
        await interaction.response.send_message(f"Sorry {interaction.user.mention}, that's not the correct answer. Try again!")

#! Slash command for kick (error: anyone can use it)
'''
@bot.tree.command(name='kick', description='Kick a user from the server')
@commands.has_permissions(administrator=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f'{member.mention} has been kicked from the server.')
    except discord.Forbidden:
        await interaction.response.send_message('I do not have permission to kick this user.')
    except discord.HTTPException:
        await interaction.response.send_message('Failed to kick the user.')

@slash_kick.error
async def slash_kick_error(interaction: discord.Interaction, error):
    if isinstance(error, commands.CheckFailure):
        await interaction.response.send_message('You do not have the necessary permissions to kick members.')
'''
#! Working Kick command
@bot.command(name='kick')
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} has been kicked from the server.')
    except discord.Forbidden:
        await ctx.send('I do not have permission to kick this user.')
    except discord.HTTPException:
        await ctx.send('Failed to kick the user.')

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have the necessary permissions to kick members.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the user you want to kick.')
#! Silence command
@bot.command(name='silence')
@commands.has_permissions(administrator=True)

async def silence(ctx, member: discord.Member, time: str):
    muted_lockdown_role = discord.utils.get(ctx.guild.roles, name="Muted_Lockdown")
    try:
        remind_time = parse_time(time)
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        member_role = discord.utils.get(ctx.guild.roles, name="Member")
        if not muted_role:
            await ctx.send("Muted role not found. Please create a role named 'Muted' with appropriate permissions.")
            return
        if not member_role:
            await ctx.send("Member role not found. Please create a role named 'Member' with general permissions and remove send message privelage from @everyone role.")
            return
        await member.remove_roles(member_role)
        await member.add_roles(muted_role)
        await ctx.send(f'{member.mention} has been muted for {time}.')
        async def unmute_user():
            if not muted_lockdown_role in member.roles:
                await member.remove_roles(muted_role)
                await member.add_roles(member_role)
                await ctx.send(f'{member.mention} has been unmuted and the Member role has been restored.')
            elif muted_lockdown_role in member.roles:
                await member.remove_roles(muted_role)
                await ctx.send(f'{member.mention} has been unmuted.')
        scheduler.add_job(unmute_user, trigger=DateTrigger(run_date=remind_time))
    except ValueError as e:
        await ctx.send(str(e))
    except discord.Forbidden:
        await ctx.send('I do not have permission to mute this user.')
    except discord.HTTPException:
        await ctx.send('Failed to mute the user.')

@silence.error
async def silence_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have the necessary permissions to mute members.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the user and the time duration to mute them. Usage: !silence @user time')
#! Unsilence command
@bot.command(name='unsilence')
@commands.has_permissions(administrator=True)
async def unsilence(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    member_role = discord.utils.get(ctx.guild.roles, name="Member")

    if not muted_role:
        await ctx.send("Muted role not found. Please create a role named 'Muted' with appropriate permissions.")
        return
    
    if not member_role:
        await ctx.send("Member role not found. Please create a role named 'Member'.")
        return
    
    if muted_role in member.roles:
        try:
            await member.remove_roles(muted_role)
            await member.add_roles(member_role)
            await ctx.send(f'{member.mention} has been unmuted and the Member role has been restored.')
        except discord.Forbidden:
            await ctx.send('I do not have permission to unmute this user.')
        except discord.HTTPException:
            await ctx.send('Failed to unmute the user.')

    else:
        await ctx.send(f'{member.mention} is not muted.')

@unsilence.error
async def unsilence_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have the necessary permissions to unmute members.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the user to unmute. Usage: !unsilence @user')
#! Ban command
@bot.command(name='ban')
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    try:
        await member.ban(reason=reason + " Member ID: " + str(member.id) )
        await ctx.send(f'{member.mention} has been banned. Reason: {reason}')
    except discord.Forbidden:
        await ctx.send('I do not have permission to ban this user.')
    except discord.HTTPException as e:
        await ctx.send(f'Failed to ban the user. Error: {e}')
    except Exception as e:
        await ctx.send('An error occurred')
        print(e)

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have the necessary permissions to ban members.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the user to ban. Usage: !ban @user [reason]')
#! Unban command
@bot.command(name='unban') 
@commands.has_permissions(administrator=True)
async def unban(ctx, user_id: int, *, reason=None):

    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        embed = discord.Embed(title="Unban", description=f"{user.name} ({user.id}) has been unbanned.", color=discord.Color.green())
        await ctx.send(embed=embed)

    except discord.NotFound:
        embed = discord.Embed(title="Error", description=f"User with ID {user_id} not found.", color=discord.Color.red())
        await ctx.send(embed=embed)

    except discord.Forbidden:
        embed = discord.Embed(title="Error", description="I do not have permission to unban users.", color=discord.Color.red())
        await ctx.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="Error", description=str(e), color=discord.Color.green())
        await ctx.send(embed=embed)
        print(e)

#! Lockdown command
@bot.command(name='lockdown')
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    member_role = discord.utils.get(ctx.guild.roles, name="Member")
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    muted_lockdown_role = discord.utils.get(ctx.guild.roles, name="Muted_Lockdown")
    if not member_role:
        await ctx.send("Member role not found. Please create a role named 'Member'.")
        return

    members = ctx.guild.members
    count = 0
    for member in members:
        if member_role in member.roles:
            try:
                await member.remove_roles(member_role)
                count += 1
            except discord.Forbidden:
                await ctx.send(f"I do not have permission to modify roles for {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"Failed to remove roles for {member.mention}.")
        elif muted_role in member.roles:
            try:
                await member.add_roles(muted_lockdown_role)
                count += 1
            except discord.Forbidden:
                await ctx.send(f"I do not have permission to modify roles for {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"Failed to add roles for {member.mention}.")
    await ctx.send(f"Added the 'Muted_Lockdown' role from {count} users.")
#! Unlock command
@bot.command(name='unlock')
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    member_role = discord.utils.get(ctx.guild.roles, name="Member")
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    muted_lockdown_role = discord.utils.get(ctx.guild.roles, name="Muted_Lockdown")
    
    if not member_role:
        await ctx.send("Member role not found. Please create a role named 'Member'.")
        return
    
    if not muted_role:
        await ctx.send("Muted role not found. Please create a role named 'Muted' with appropriate permissions.")
        return

    members = ctx.guild.members
    count = 0
    for member in members:
        if member_role not in member.roles and muted_role not in member.roles:
            try:
                await member.add_roles(member_role)
                count += 1
            except discord.Forbidden:
                await ctx.send(f"I do not have permission to modify roles for {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"Failed to add roles for {member.mention}.")
        elif muted_lockdown_role in member.roles:
            try:
                await member.remove_roles(muted_lockdown_role)
                count += 1
            except discord.Forbidden:
                await ctx.send(f"I do not have permission to modify roles for {member.mention}.")
            except discord.HTTPException:
                await ctx.send(f"Failed to remove roles for {member.mention}.")
    
    await ctx.send(f"Restored the 'Member' role to {count} users.")

@unlock.error
async def unlock_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have the necessary permissions to use this command.')

@lockdown.error
async def lockdown_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You do not have the necessary permissions to use this command.')

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    member_role = discord.utils.get(member.guild.roles, name="Member")

    if member_role:
        try:
            await member.add_roles(member_role)
            if channel is not None:
                embed = discord.Embed(
                    title="Welcome!",
                    description=f"Welcome to the server, {member.mention}!",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
        except discord.Forbidden:
            if channel is not None:
                await channel.send(f"Failed to assign 'Member' role to {member.mention}. I do not have permission.")
        except discord.HTTPException:
            if channel is not None:
                await channel.send(f"Failed to assign 'Member' role to {member.mention}. An error occurred.")
    else:
        if channel is not None:
            await channel.send("Member role not found. Please create a role named 'Member'.")

@bot.event
async def on_member_remove(member):
    channel = member.guild.system_channel
    if channel is not None:
        embed = discord.Embed(
            title="Goodbye!",
            description=f"{member.mention} has left the server.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)
        
@bot.command(name='motivate')
@commands.cooldown(1, 3, commands.BucketType.user)
async def motivate(ctx):
    try:
        quote = get_motivational_quote()
        await ctx.send(quote)
    except requests.exceptions.RequestException:
        await ctx.send("Error fetching motivational quote, API not responsive")
    except commands.CommandOnCooldown as e:
        await ctx.send(f"This command is on cooldown. Please try again in {e.retry_after:.2f} seconds.")

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(name='help')
async def help_command(ctx):
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
    """
    await ctx.send(help_text)   

@bot.command(name='dadjoke')
@commands.cooldown(1, 5, commands.BucketType.user)
async def dadjoke(ctx):
    try:
        joke = get_dad_joke()
        await ctx.send(joke)
    except requests.exceptions.RequestException:
        await ctx.send("Error fetching dad joke, API not responsive")
    except commands.CommandOnCooldown as e:
        await ctx.send(f"This command is on cooldown. Please try again in {e.retry_after:.2f} seconds.")

#! Slash command for motivate
@bot.tree.command(name="motivate", description="Get a motivational quote")
async def slash_motivate(interaction: discord.Interaction):
    try:
        quote = get_motivational_quote()
        await interaction.response.send_message(quote)
    except requests.exceptions.RequestException:
        await interaction.response.send_message("Error fetching motivational quote, API not responsive")

#! Slash command for dadjoke
@bot.tree.command(name="dadjoke", description="Get a dad joke")
async def slash_dadjoke(interaction: discord.Interaction):
    try:
        joke = get_dad_joke()
        await interaction.response.send_message(joke)
    except requests.exceptions.RequestException:
        await interaction.response.send_message("Error fetching dad joke, API not responsive")

def set_reminder(user_id, channel_id, message, remind_time):
    async def send_reminder():
        channel = bot.get_channel(channel_id)
        user = bot.get_user(user_id)
        await channel.send(f"{user.mention}, here is your reminder: {message}")

    scheduler.add_job(send_reminder, trigger=DateTrigger(run_date=remind_time))
#! Slash command for remindme
@bot.tree.command(name="remindme", description="Set a reminder")
@app_commands.describe(message = "Message for the reminder", time = "Time duration for the reminder, e.g. 10s (10 seconds), 5m (5 mintues), 1h (1 hour), 2d (2 days)")
async def remindme(interaction: discord.Interaction, message: str, time: str):
    try:
        remind_time = parse_time(time)
        set_reminder(interaction.user.id, interaction.channel_id, message, remind_time)
        await interaction.response.send_message(f"Reminder set for {time} with message: {message}")
    except ValueError as e:
        await interaction.response.send_message(str(e))

def parse_time(time_str):
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

bot.run(TOKEN)
