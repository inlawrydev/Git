"""
IRY HUB OBF — Roblox Obfuscator Bot
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
from datetime import datetime

from obfuscator import AdvancedRobloxObfuscator
from pastefy_uploader import PastefyUploader

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()

class ObfuscatorBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        self.obf = AdvancedRobloxObfuscator()
        self.pastefy = PastefyUploader()

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Logged in as {self.user}")

    async def close(self):
        await self.pastefy.close()
        await super().close()

bot = ObfuscatorBot()

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Roblox scripts 🔒"
        )
    )

async def upload_to_pastefy(title: str, content: str) -> dict:
    return await bot.pastefy.upload_paste(title, content, "UNLISTED")

def create_embed(paste_result: dict, original_size: int, obf_size: int) -> discord.Embed:
    if paste_result['success']:
        embed = discord.Embed(
            title="✅ Обфускация завершена!",
            description="🛡️ Защита: **MAXIMUM**",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        embed.add_field(name="🔗 Ссылка", value=f"[Pastefy]({paste_result['url']})", inline=False)
        embed.add_field(name="📋 Raw", value=f"[Копировать]({paste_result['raw_url']})", inline=False)
    else:
        embed = discord.Embed(
            title="⚠️ Pastefy недоступен",
            description=f"Ошибка: `{paste_result['error']}`",
            color=0xffaa00,
            timestamp=datetime.now()
        )

    embed.add_field(name="📦 Исходный", value=f"`{original_size}` байт", inline=True)
    embed.add_field(name="📦 Обфусцированный", value=f"`{obf_size}` байт", inline=True)
    embed.add_field(
        name="🔐 Методы",
        value="Multi-key XOR, Splitting, Rename, Minify, Junk, Numbers, Wrapper",
        inline=False
    )
    embed.add_field(
        name="⚙️ Совместимость",
        value="`loadstring` · `game:HttpGet` · `syn.request` · `getgenv` · "
              "`hookfunction` · `queue_on_teleport` · `Drawing` · 250+ executor API",
        inline=False
    )
    return embed

@bot.tree.command(name="obfuscate", description="🔒 Обфусцировать Roblox-скрипт (MAX защита)")
@app_commands.describe(
    code="Lua-код для обфускации",
    title="Название пасты"
)
async def obfuscate(
    interaction: discord.Interaction,
    code: str,
    title: str = "Obfuscated Script"
):
    await interaction.response.defer(thinking=True)

    original_size = len(code.encode('utf-8'))

    try:
        obfuscated = bot.obf.obfuscate(code)
        obf_size = len(obfuscated.encode('utf-8'))

        paste_result = await upload_to_pastefy(title, obfuscated)
        embed = create_embed(paste_result, original_size, obf_size)

        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as f:
                f.write(obfuscated)
                fp = f.name
            await interaction.followup.send(embed=embed, file=discord.File(fp, "obfuscated.lua"))
            os.unlink(fp)
        else:
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="obfuscate_file", description="📁 Загрузить .lua файл (MAX защита)")
@app_commands.describe(file="Файл .lua")
async def obfuscate_file(
    interaction: discord.Interaction,
    file: discord.Attachment
):
    if not file.filename.endswith('.lua'):
        await interaction.response.send_message("❌ Только `.lua`!", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        content = await file.read()
        code = content.decode('utf-8')
        original_size = len(content)

        obfuscated = bot.obf.obfuscate(code)
        obf_size = len(obfuscated.encode('utf-8'))

        paste_result = await upload_to_pastefy(f"Obfuscated {file.filename}", obfuscated)
        embed = create_embed(paste_result, original_size, obf_size)
        embed.set_footer(text=f"Файл: {file.filename}")

        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as f:
                f.write(obfuscated)
                fp = f.name
            await interaction.followup.send(embed=embed, file=discord.File(fp, f"obf_{file.filename}"))
            os.unlink(fp)
        else:
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="ping", description="🏓 Проверка")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong!", description=f"`{latency}ms`", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="📖 Справка")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 IRY HUB OBF",
        description="Продвинутый обфускатор Roblox-скриптов\n🛡️ Всегда **максимальный** уровень защиты",
        color=0x5865F2
    )
    embed.add_field(
        name="/obfuscate",
        value="Обфусцировать код\n`code` — Lua-код\n`title` — название пасты",
        inline=False
    )
    embed.add_field(
        name="/obfuscate_file",
        value="Обфусцировать `.lua` файл",
        inline=False
    )
    embed.add_field(
        name="🛡️ Методы защиты",
        value="Multi-key XOR-шифрование строк · Разбиение строк на части · "
              "Переименование переменных · Обфускация чисел · Junk-код · "
              "Minification (весь код в одну строку)",
        inline=False
    )
    embed.add_field(
        name="⚙️ Полная совместимость",
        value="`loadstring(game:HttpGet())` · `syn.request` · `request` · `http_request` · "
              "`getgenv` · `gethui` · `identifyexecutor` · `queue_on_teleport` · "
              "`setclipboard` · `writefile` · `hookfunction` · `hookmetamethod` · "
              "`Drawing` · `WebSocket` · `getrawmetatable` · `newcclosure` и др.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Укажите DISCORD_TOKEN!")
        exit(1)
    bot.run(TOKEN)
