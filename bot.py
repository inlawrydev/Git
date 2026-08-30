"""
IRY HUB OBF — Roblox Obfuscator Bot
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
from datetime import datetime

from obfuscator import AdvancedRobloxObfuscator, BytecodeObfuscator
from pastefy_uploader import PastefyUploader

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
# intents.message_content = True  # Убрали, т.к. используем только slash-команды

class ObfuscatorBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        self.obf = AdvancedRobloxObfuscator()
        self.bytecode_obf = BytecodeObfuscator()
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

def create_embed(paste_result: dict, level: str, original_size: int, obf_size: int) -> discord.Embed:
    if paste_result['success']:
        embed = discord.Embed(
            title="✅ Обфускация завершена!",
            description=f"Уровень: `{level}`",
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
    embed.add_field(name="🔐 Методы", value="XOR, Minify, Junk, Rename", inline=False)
    return embed

@bot.tree.command(name="obfuscate", description="🔒 Обфусцировать Roblox-скрипт")
@app_commands.describe(
    code="Lua-код для обфускации",
    level="Уровень защиты",
    title="Название пасты"
)
@app_commands.choices(level=[
    app_commands.Choice(name="🔧 Light (переименование + minify)", value="light"),
    app_commands.Choice(name="🔒 Medium (+ XOR-шифрование строк)", value="medium"),
    app_commands.Choice(name="🛡️ Heavy (всё + junk code + числа)", value="heavy"),
    app_commands.Choice(name="⚡ Bytecode (компиляция в байткод)", value="bytecode")
])
async def obfuscate(
    interaction: discord.Interaction,
    code: str,
    level: str = "heavy",
    title: str = "Obfuscated Script"
):
    await interaction.response.defer(thinking=True)
    
    original_size = len(code.encode('utf-8'))
    
    try:
        if level == "bytecode":
            result = bot.bytecode_obf.obfuscate_bytecode(code)
            if result['success']:
                obfuscated = result['loader']
            else:
                # Fallback на heavy
                obfuscated = bot.obf.obfuscate(code, "heavy")
                level = "heavy (fallback из-за ошибки bytecode)"
        else:
            obfuscated = bot.obf.obfuscate(code, level)
        
        obf_size = len(obfuscated.encode('utf-8'))
        
        # Загружаем на Pastefy
        paste_result = await upload_to_pastefy(title, obfuscated)
        
        embed = create_embed(paste_result, level, original_size, obf_size)
        
        if not paste_result['success']:
            # Отправляем файлом если Pastefy упал
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(obfuscated)
                fp = f.name
            await interaction.followup.send(embed=embed, file=discord.File(fp, "obfuscated.lua"))
            os.unlink(fp)
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="obfuscate_file", description="📁 Загрузить .lua файл")
@app_commands.describe(
    file="Файл .lua",
    level="Уровень защиты"
)
@app_commands.choices(level=[
    app_commands.Choice(name="🔧 Light", value="light"),
    app_commands.Choice(name="🔒 Medium", value="medium"),
    app_commands.Choice(name="🛡️ Heavy", value="heavy"),
    app_commands.Choice(name="⚡ Bytecode", value="bytecode")
])
async def obfuscate_file(
    interaction: discord.Interaction,
    file: discord.Attachment,
    level: str = "heavy"
):
    if not file.filename.endswith('.lua'):
        await interaction.response.send_message("❌ Только `.lua`!", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        content = await file.read()
        code = content.decode('utf-8')
        original_size = len(content)
        
        if level == "bytecode":
            result = bot.bytecode_obf.obfuscate_bytecode(code)
            if result['success']:
                obfuscated = result['loader']
            else:
                obfuscated = bot.obf.obfuscate(code, "heavy")
                level = "heavy (fallback)"
        else:
            obfuscated = bot.obf.obfuscate(code, level)
        
        obf_size = len(obfuscated.encode('utf-8'))
        
        paste_result = await upload_to_pastefy(f"Obfuscated {file.filename}", obfuscated)
        
        embed = create_embed(paste_result, level, original_size, obf_size)
        embed.set_footer(text=f"Файл: {file.filename}")
        
        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
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
        description="Продвинутый обфускатор Roblox-скриптов",
        color=0x5865F2
    )
    embed.add_field(
        name="/obfuscate",
        value="Обфусцировать код\n"
              "`code` — Lua-код\n"
              "`level` — light/medium/heavy/bytecode\n"
              "`title` — название пасты",
        inline=False
    )
    embed.add_field(
        name="🔧 Light",
        value="Переименование переменных + minification",
        inline=False
    )
    embed.add_field(
        name="🔒 Medium",
        value="+ XOR-шифрование строк",
        inline=False
    )
    embed.add_field(
        name="🛡️ Heavy",
        value="+ Обфускация чисел + junk code + flattening\n"
              "Весь код в **одну строку**!",
        inline=False
    )
    embed.add_field(
        name="⚡ Bytecode",
        value="Компиляция в байткод LuaJIT + XOR-шифрование",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Укажите DISCORD_TOKEN!")
        exit(1)
    bot.run(TOKEN)
