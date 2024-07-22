import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import re

scheduler = AsyncIOScheduler()

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kick')
    @commands.has_permissions(administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        try:
            await member.kick(reason=reason)
            await ctx.send(f'{member.mention} has been kicked from the server.')
        except discord.Forbidden:
            await ctx.send('I do not have permission to kick this user.')
        except discord.HTTPException:
            await ctx.send('Failed to kick the user.')

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to kick members.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please mention the user you want to kick.')

    @commands.command(name='silence')
    @commands.has_permissions(administrator=True)
    async def silence(self, ctx, member: discord.Member, time: str):
        muted_lockdown_role = discord.utils.get(ctx.guild.roles, name="Muted_Lockdown")
        try:
            remind_time = self.parse_time(time)
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            member_role = discord.utils.get(ctx.guild.roles, name="Member")
            if not muted_role:
                await ctx.send("Muted role not found. Please create a role named 'Muted' with appropriate permissions.")
                return
            if not member_role:
                await ctx.send("Member role not found. Please create a role named 'Member' with general permissions and remove send message privilege from @everyone role.")
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
    async def silence_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to mute members.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please mention the user and the time duration to mute them. Usage: !silence @user time')

    @commands.command(name='unsilence')
    @commands.has_permissions(administrator=True)
    async def unsilence(self, ctx, member: discord.Member):
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
    async def unsilence_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to unmute members.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please mention the user to unmute. Usage: !unsilence @user')

    @commands.command(name='ban')
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        try:
            await member.ban(reason=reason + " Member ID: " + str(member.id))
            await ctx.send(f'{member.mention} has been banned. Reason: {reason}')
        except discord.Forbidden:
            await ctx.send('I do not have permission to ban this user.')
        except discord.HTTPException as e:
            await ctx.send(f'Failed to ban the user. Error: {e}')
        except Exception as e:
            await ctx.send('An error occurred')
            print(e)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to ban members.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please mention the user to ban. Usage: !ban @user [reason]')

    @commands.command(name='unban')
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, user_id: int, *, reason=None):
        try:
            user = await self.bot.fetch_user(user_id)
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

    @commands.command(name='lockdown')
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
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
        await ctx.send(f"Added the 'Muted_Lockdown' role to {count} users.")

    @commands.command(name='unlock')
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx):
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
    async def unlock_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to use this command.')

    @lockdown.error
    async def lockdown_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to use this command.')

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
