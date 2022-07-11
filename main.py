import asyncio

import discord
import youtube_dl

from discord.ext import commands

youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        embed = discord.Embed(title="Успешно", description=f"Да начнёться пати!\nВы успешно настроили музыку.\nСейчас играет: {player.title}\nГромкость можно настроить через команду fm!volume", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            embed = discord.Embed(title="Ошибка", description=f"Вы не подключены к голосовому каналу!", color=discord.Color.red())
            return await ctx.send(embed=embed)
        ctx.voice_client.source.volume = volume / 100
        embed = discord.Embed(title="Успешно", description=f"Вы настроили громкость на {volume}%!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()
        embed = discord.Embed(title="Готово", description="Музыка успешно остановлена!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                embed = discord.Embed(title="Ошибка", description="Вы не подключены к голосовому каналу!", color=discord.Color.red())
                await ctx.send(embed=embed)
                raise commands.CommandError(f"{ctx.author.name}: Пользователь не подключен к голосовому каналу.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Командый справочник", description="``fm!help`` - выводит эту справку\n``fm!play`` - играть музыку\n``fm!stop`` - остановить музыку\n``fm!volume`` - установить громкость музыки", color=discord.Color.purple())
        await ctx.send(embed=embed)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="Ваш-Префикс-Команд",
    intents=intents,
)

bot.remove_command('help')

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Ваш статус"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})\n')
    print('------------------------------------')

async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start('Ваш-токен-бота')

asyncio.run(main())