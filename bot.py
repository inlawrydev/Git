
import discord
from discord import app_commands
from discord.ext import commands
import os
import tempfile
from datetime import datetime

from obfuscator import AdvancedRobloxObfuscator
from pastefy_uploader import PastefyUploader

TOKEN = os.getenv('DISCORD_TOKEN')
MAX_INPUT_BYTES = 512 * 1024
MAX_OUTPUT_BYTES = 8 * 1024 * 1024

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
            name="Roblox scripts"
        )
    )

async def upload_to_pastefy(title: str, content: str) -> dict:
    return await bot.pastefy.upload_paste(title, content, "UNLISTED")

def validate_code_size(code: str) -> int:
    size = len(code.encode('utf-8'))
    if size > MAX_INPUT_BYTES:
        raise ValueError(f"Source file exceeds {MAX_INPUT_BYTES // 1024} KiB")
    return size

def create_embed(paste_result: dict, original_size: int, obf_size: int) -> discord.Embed:
    if paste_result['success']:
        embed = discord.Embed(
            title="Obfuscation Complete!",
            description="Protection: **SAFE**",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        embed.add_field(name="Link", value=f"[Pastefy]({paste_result['url']})", inline=False)
        embed.add_field(name="Raw", value=f"[Copy]({paste_result['raw_url']})", inline=False)
    else:
        embed = discord.Embed(
            title="Pastefy Unavailable",
            description=f"Error: `{paste_result['error']}`",
            color=0xffaa00,
            timestamp=datetime.now()
        )

    embed.add_field(name="Source", value=f"`{original_size}` bytes", inline=True)
    embed.add_field(name="Obfuscated", value=f"`{obf_size}` bytes", inline=True)
    embed.add_field(
        name="Methods",
        value="Multi-key XOR, String Splitting, Minification",
        inline=False
    )
    embed.add_field(
        name="Compatibility",
        value="`loadstring`  `game:HttpGet`  `syn.request`  `getgenv`  "
              "`hookfunction`  `queue_on_teleport`  `Drawing`  250+ executor API",
        inline=False
    )
    return embed

@bot.tree.command(name="obfcode", description="Obfuscate a Roblox script (safe mode)")
@app_commands.describe(
    code="Lua code to obfuscate",
    title="Paste title"
)
async def obfuscate(
    interaction: discord.Interaction,
    code: str,
    title: str = "Obfuscated Script"
):
    await interaction.response.defer(thinking=True)

    try:
        original_size = validate_code_size(code)
        obfuscated = bot.obf.obfuscate(code)
        obf_size = len(obfuscated.encode('utf-8'))
        if obf_size > MAX_OUTPUT_BYTES:
            raise ValueError("Result is too large to send through Discord")

        paste_result = await upload_to_pastefy(title, obfuscated)
        embed = create_embed(paste_result, original_size, obf_size)

        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as f:
                f.write(obfuscated)
                fp = f.name
            try:
                await interaction.followup.send(embed=embed, file=discord.File(fp, "obfuscated.lua"))
            finally:
                os.unlink(fp)
        else:
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="obf", description="Upload a .lua file (safe mode)")
@app_commands.describe(file="Lua file")
async def obfuscate_file(
    interaction: discord.Interaction,
    file: discord.Attachment
):
    if not file.filename.endswith('.lua'):
        await interaction.response.send_message(" Only `.lua` files are accepted!", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        content = await file.read()
        code = content.decode('utf-8')
        original_size = validate_code_size(code)

        obfuscated = bot.obf.obfuscate(code)
        obf_size = len(obfuscated.encode('utf-8'))
        if obf_size > MAX_OUTPUT_BYTES:
            raise ValueError("Result is too large to send through Discord")

        paste_result = await upload_to_pastefy(f"Obfuscated {file.filename}", obfuscated)
        embed = create_embed(paste_result, original_size, obf_size)
        embed.set_footer(text=f"File: {file.filename}")

        if not paste_result['success']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as f:
                f.write(obfuscated)
                fp = f.name
            try:
                await interaction.followup.send(embed=embed, file=discord.File(fp, f"obf_{file.filename}"))
            finally:
                os.unlink(fp)
        else:
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="Pong!", description=f"`{latency}ms`", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show help")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="IRY HUB OBF",
        description="Roblox script obfuscator\nCompatibility-first safe mode",
        color=0x5865F2
    )
    embed.add_field(
        name="/obfcode",
        value="Obfuscate Lua code\n`code` - Lua source\n`title` - paste title",
        inline=False
    )
    embed.add_field(
        name="/obf",
        value="Obfuscate an attached `.lua` file",
        inline=False
    )
    embed.add_field(
        name="Protection Methods",
        value="Multi-key XOR string encryption  String splitting  "
              "Minification (single-line output)",
        inline=False
    )
    embed.add_field(
        name="Supported APIs",
        value="`loadstring(game:HttpGet())`  `syn.request`  `request`  `http_request`  "
              "`getgenv`  `gethui`  `identifyexecutor`  `queue_on_teleport`  "
              "`setclipboard`  `writefile`  `hookfunction`  `hookmetamethod`  "
              "`Drawing`  `WebSocket`  `getrawmetatable`  `newcclosure` and more.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("Set DISCORD_TOKEN before starting the bot.")
        exit(1)
    bot.run(TOKEN)
