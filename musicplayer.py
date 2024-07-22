import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
#! pip install PyNaCl 
#! ffmpeg required, built versions available at https://www.gyan.dev/ffmpeg/builds/, once installed put the 3 exe files in /bin/ in the same folder as the bot

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='music')
    async def music(self, ctx, *, song_name: str):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch'
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
                if 'entries' in info:
                    video = info['entries'][0]
                    url = video['url']
                else:
                    await ctx.send("Could not find any results.")
                    return
        except Exception as e:
            await ctx.send(f"Error fetching YouTube information: {e}")
            return

        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            await ctx.send("You need to be in a voice channel to play music.")
            return

        if ctx.voice_client:
            if ctx.voice_client.channel != voice_channel:
                await ctx.voice_client.disconnect()
            else:
                await ctx.send("Already connected to this voice channel.")
                return

        try:
            voice_client = await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"Error connecting to voice channel: {e}")
            return

        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        try:
            voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts), after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send(f"Now playing: {video['title']}")
        except Exception as e:
            await ctx.send(f"Error playing audio: {e}")
            await voice_client.disconnect()

        while voice_client.is_playing():
            await asyncio.sleep(1)
        
        await voice_client.disconnect()

    @music.error
    async def music_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide a song name. Usage: !music <song_name>")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("There was an error processing your request.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to use this command.') 

    @app_commands.command(name='music', description='Play a song from YouTube')
    @app_commands.describe(song_name="Name of the song to play")
    async def slash_music(self, interaction: discord.Interaction, song_name: str):
        await interaction.response.defer()

        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch'
        }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
                if 'entries' in info:
                    video = info['entries'][0]
                    url = video['url']
                else:
                    await interaction.followup.send("Could not find any results.")
                    return
        except Exception as e:
            await interaction.followup.send(f"Error fetching YouTube information: {e}")
            return

        voice_channel = interaction.user.voice.channel
        if not voice_channel:
            await interaction.followup.send("You need to be in a voice channel to play music.")
            return

        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel != voice_channel:
                await interaction.guild.voice_client.disconnect()

        try:
            voice_client = await voice_channel.connect()
        except Exception as e:
            await interaction.followup.send(f"Error connecting to voice channel: {e}")
            return

        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        try:
            voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts), after=lambda e: print('Player error: %s' % e) if e else None)
            await interaction.followup.send(f"Now playing: {video['title']}")
        except Exception as e:
            await interaction.followup.send(f"Error playing audio: {e}")
            await voice_client.disconnect()

        while voice_client.is_playing():
            await asyncio.sleep(1)
        
        await voice_client.disconnect()

    @slash_music.error
    async def slash_music_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingRequiredArgument):
            await interaction.followup.send("Please provide a song name. Usage: /music <song_name>")
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            await interaction.followup.send("There was an error processing your request.")
        elif isinstance(error, app_commands.errors.CheckFailure):
            await interaction.followup.send('You do not have the necessary permissions to use this command.')

    @commands.command(name='stop')
    async def stop(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            await ctx.send("Stopped playing and disconnected from the voice channel.")
        else:
            await ctx.send("I am not connected to a voice channel.")

    @app_commands.command(name='stop', description='Stop playing music and disconnect from the voice channel')
    async def slash_stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            await interaction.response.send_message("Stopped playing and disconnected from the voice channel.")
        else:
            await interaction.response.send_message("I am not connected to a voice channel.")
