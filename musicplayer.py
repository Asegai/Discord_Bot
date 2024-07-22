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
        self.song_queue = {}  # Dictionary to store the song queue for each guild

    @commands.command(name='music')
    async def music(self, ctx, *, song_name: str = None):
        if song_name is None:
            await ctx.send("Please provide a song name. Usage: !music <song_name>")
            return
        
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

        if ctx.guild.id not in self.song_queue:
            self.song_queue[ctx.guild.id] = []

        self.song_queue[ctx.guild.id].append((url, video['title']))

        if not ctx.voice_client:
            try:
                voice_client = await voice_channel.connect()
                await self.play_next(ctx.guild)
            except Exception as e:
                await ctx.send(f"Error connecting to voice channel: {e}")
                return
        else:
            await ctx.send(f"Added to queue: {video['title']}")

    @music.error
    async def music_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide a song name. Usage: !music <song_name>")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send("There was an error processing your request, perhaps you're not connected to a VC.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('You do not have the necessary permissions to use this command.')

    @app_commands.command(name='music', description='Play a song from YouTube')
    @app_commands.describe(song_name="Name of the song to play")
    async def slash_music(self, interaction: discord.Interaction, song_name: str = None):
        if song_name is None:
            await interaction.response.send_message("Please provide a song name. Usage: /music <song_name>")
            return

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

        if interaction.guild.id not in self.song_queue:
            self.song_queue[interaction.guild.id] = []

        self.song_queue[interaction.guild.id].append((url, video['title']))

        if not interaction.guild.voice_client:
            try:
                voice_client = await voice_channel.connect()
                await self.play_next(interaction.guild)
            except Exception as e:
                await interaction.followup.send(f"Error connecting to voice channel: {e}")
                return
        else:
            await interaction.followup.send(f"Added to queue: {video['title']}")

    async def play_next(self, guild):
        if guild.id not in self.song_queue or not self.song_queue[guild.id]:
            return

        url, title = self.song_queue[guild.id].pop(0)
        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        def after_playing(error):
            if error:
                print('Player error: %s' % error)
            asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop)

        try:
            guild.voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_opts), after=after_playing)
            asyncio.run_coroutine_threadsafe(guild.voice_client.move_to(guild.voice_client.channel), self.bot.loop)
        except Exception as e:
            print(f"Error playing audio: {e}")
            await guild.voice_client.disconnect()

    @commands.command(name='stop')
    async def stop(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected():
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            self.song_queue[ctx.guild.id] = []
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
            self.song_queue[interaction.guild.id] = []
            await interaction.response.send_message("Stopped playing and disconnected from the voice channel.")
        else:
            await interaction.response.send_message("I am not connected to a voice channel.")

    @commands.command(name='pause')
    async def pause(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("Paused the music.")
        else:
            await ctx.send("No music is currently playing.")

    @app_commands.command(name='pause', description='Pause the currently playing music')
    async def slash_pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Paused the music.")
        else:
            await interaction.response.send_message("No music is currently playing.")

    @commands.command(name='resume')
    async def resume(self, ctx):
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("Resumed the music.")
        else:
            await ctx.send("No music is currently paused.")

    @app_commands.command(name='resume', description='Resume the paused music')
    async def slash_resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Resumed the music.")
        else:
            await interaction.response.send_message("No music is currently paused.")

    async def disconnect_after_playback(self, guild):
        await asyncio.sleep(1)
        voice_client = guild.voice_client
        if voice_client and not voice_client.is_playing():
            await voice_client.disconnect()
