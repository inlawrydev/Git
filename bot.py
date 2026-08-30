"""
Roblox Obfuscator Bot for Discord
Hosted on Hugging Face Spaces
С автоматической загрузкой на Pastefy
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
from datetime import datetime

from obfuscator import RobloxObfuscator, SimpleObfuscator
from pastefy_uploader import PastefyUploader

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.message_content = True

class ObfuscatorBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        self.bytecode_obf = RobloxObfuscator()
        self.simple_obf = SimpleObfuscator()
        self.pastefy = PastefyUploader()
        
    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        print(f"Logged in as {self.user}")
        print("Slash commands synced!")

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

async def upload_to_pastefy(title: str, content: str, visibility: str = "UNLISTED") -> dict:
    return await bot.pastefy.upload_paste(title, content, visibility)

def create_result_embed(
    paste_result: dict,
    method: str,
    original_size: int,
    obf_size: int,
    filename: str = None
) -> discord.Embed:
    
    if paste_result['success']:
        embed = discord.Embed(
            title="✅ Обфускация завершена!",
            description="Код загружен на Pastefy",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="🔗 Ссылка",
            value=f"[Открыть на Pastefy]({paste_result['url']})",
            inline=False
        )
        embed.add_field(
            name="📋 Raw (для копирования)",
            value=f"[Скопировать код]({paste_result['raw_url']})",
            inline=False
        )
    else:
        embed = discord.Embed(
            title="⚠️ Обфускация завершена, но Pastefy недоступен",
            description=f"Ошибка: `{paste_result['error']}`",
            color=0xffaa00,
            timestamp=datetime.now()
        )
    
    embed.add_field(
        name="🔐 Метод",
        value=f"`{method}`",
        inline=True
    )
    embed.add_field(
        name="📦 Исходный размер",
        value=f"`{original_size}` байт",
        inline=True
    )
    embed.add_field(
        name="📦 Обфусцированный",
        value=f"`{obf_size}` байт",
        inline=True
    )
    
    if filename:
        embed.set_footer(text=f"Файл: {filename}")
    
    return embed

@bot.tree.command(
    name="obfuscate_code",
    description="🔒 Обфусцировать Lua-код и загрузить на Pastefy"
)
@app_commands.describe(
    code="Lua-код для обфускации",
    method="Метод: bytecode (лучший) | simple (fallback)",
    title="Название пасты на Pastefy",
    visibility="Видимость: unlisted (по умолчанию) | public | private"
)
@app_commands.choices(method=[
    app_commands.Choice(name="🔒 Bytecode (рекомендуется)", value="bytecode"),
    app_commands.Choice(name="🔧 Simple (fallback)", value="simple")
])
@app_commands.choices(visibility=[
    app_commands.Choice(name="🔒 Unlisted (по ссылке)", value="UNLISTED"),
    app_commands.Choice(name="🌍 Public (все видят)", value="PUBLIC"),
    app_commands.Choice(name="🔐 Private (только вы)", value="PRIVATE")
])
async def obfuscate_code(
    interaction: discord.Interaction,
    code: str,
    method: str = "bytecode",
    title: str = "Obfuscated Roblox Script",
    visibility: str = "UNLISTED"
):
    await interaction.response.defer(thinking=True)
    
    original_size = len(code.encode('utf-8'))
    
    try:
        if method == "bytecode":
            result = bot.bytecode_obf.obfuscate_bytecode(code)
            if result['success']:
                obfuscated = result['loader']
            else:
                obfuscated = bot.simple_obf.obfuscate(code)
                method = "simple (fallback из-за ошибки bytecode)"
        else:
            obfuscated = bot.simple_obf.obfuscate(code)
        
        obf_size = len(obfuscated.encode('utf-8'))
        
        paste_result = await upload_to_pastefy(
            title=title,
            content=obfuscated,
            visibility=visibility
        )
        
        embed = create_result_embed(
            paste_result=paste_result,
            method=method,
            original_size=original_size,
            obf_size=obf_size
        )
        
        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(obfuscated)
                file_path = f.name
            
            await interaction.followup.send(
                embed=embed,
                file=discord.File(file_path, "obfuscated.lua")
            )
            os.unlink(file_path)
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await interaction.followup.send(
            content=f"❌ Ошибка: `{str(e)}`",
            ephemeral=True
        )

@bot.tree.command(
    name="obfuscate_file",
    description="📁 Загрузить .lua файл, обфусцировать и выложить на Pastefy"
)
@app_commands.describe(
    file="Файл .lua для обфускации",
    method="Метод обфускации",
    title="Название пасты",
    visibility="Видимость пасты"
)
@app_commands.choices(method=[
    app_commands.Choice(name="🔒 Bytecode (рекомендуется)", value="bytecode"),
    app_commands.Choice(name="🔧 Simple (fallback)", value="simple")
])
@app_commands.choices(visibility=[
    app_commands.Choice(name="🔒 Unlisted", value="UNLISTED"),
    app_commands.Choice(name="🌍 Public", value="PUBLIC"),
    app_commands.Choice(name="🔐 Private", value="PRIVATE")
])
async def obfuscate_file(
    interaction: discord.Interaction,
    file: discord.Attachment,
    method: str = "bytecode",
    title: str = None,
    visibility: str = "UNLISTED"
):
    if not file.filename.endswith('.lua'):
        await interaction.response.send_message(
            "❌ Только `.lua` файлы!", ephemeral=True
        )
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        content = await file.read()
        code = content.decode('utf-8')
        original_size = len(content)
        
        paste_title = title or f"Obfuscated {file.filename}"
        
        if method == "bytecode":
            result = bot.bytecode_obf.obfuscate_bytecode(code)
            if result['success']:
                obfuscated = result['loader']
            else:
                obfuscated = bot.simple_obf.obfuscate(code)
                method = "simple (fallback)"
        else:
            obfuscated = bot.simple_obf.obfuscate(code)
        
        obf_size = len(obfuscated.encode('utf-8'))
        
        paste_result = await upload_to_pastefy(
            title=paste_title,
            content=obfuscated,
            visibility=visibility
        )
        
        embed = create_result_embed(
            paste_result=paste_result,
            method=method,
            original_size=original_size,
            obf_size=obf_size,
            filename=file.filename
        )
        
        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(obfuscated)
                fp = f.name
            await interaction.followup.send(embed=embed, file=discord.File(fp, f"obf_{file.filename}"))
            os.unlink(fp)
        else:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await interaction.followup.send(
            content=f"❌ Ошибка: `{str(e)}`",
            ephemeral=True
        )

@bot.tree.command(name="ping", description="🏓 Проверить работу бота")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Задержка: `{latency}ms`",
        color=0x00ff00 if latency < 100 else 0xffaa00
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="📖 Справка по боту")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔒 Roblox Obfuscator Bot",
        description="Обфускация скриптов с автозагрузкой на Pastefy",
        color=0x5865F2
    )
    embed.add_field(
        name="/obfuscate_code",
        value="Обфусцировать код из чата\n"
              "• `code` — Lua-код\n"
              "• `method` — bytecode или simple\n"
              "• `title` — название пасты\n"
              "• `visibility` — unlisted/public/private",
        inline=False
    )
    embed.add_field(
        name="/obfuscate_file",
        value="Загрузить `.lua` файл\n"
              "Поддерживает файлы до 8MB",
        inline=False
    )
    embed.add_field(
        name="🔗 Pastefy интеграция",
        value="Все обфусцированные скрипты автоматически загружаются на [pastefy.app](https://pastefy.app)\n"
              "• **Unlisted** — доступ по ссылке\n"
              "• **Public** — виден всем\n"
              "• **Private** — только вам (требует API ключ)",
        inline=False
    )
    embed.add_field(
        name="🔐 Bytecode метод",
        value="Компиляция в байткод LuaJIT + XOR-шифрование.\n"
              "Генерирует защищённый загрузчик для Roblox.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Укажите DISCORD_TOKEN в переменных окружения!")
        exit(1)
    bot.run(TOKEN)
