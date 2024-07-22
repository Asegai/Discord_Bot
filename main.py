import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from musicplayer import MusicCommands
from moderation import ModerationCommands
from miscellaneous import MiscellaneousCommands

with open('auth_token.txt', 'r') as file: #! Create a file named auth_token.txt in the same folder as the python files and put your discord bot token in it
    TOKEN = file.read().strip()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    await bot.add_cog(MusicCommands(bot))
    await bot.add_cog(ModerationCommands(bot))
    await bot.add_cog(MiscellaneousCommands(bot))
    await bot.tree.sync()
    scheduler.start()
    print(f'{bot.user.name} has connected to Discord!')


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
        
bot.run(TOKEN)
