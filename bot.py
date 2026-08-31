
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
            name="Roblox scripts рџ”’"
        )
    )

async def upload_to_pastefy(title: str, content: str) -> dict:
    return await bot.pastefy.upload_paste(title, content, "UNLISTED")

def validate_code_size(code: str) -> int:
    size = len(code.encode('utf-8'))
    if size > MAX_INPUT_BYTES:
        raise ValueError(f"Р Р°Р·РјРµСЂ РёСЃС…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РїСЂРµРІС‹С€Р°РµС‚ {MAX_INPUT_BYTES // 1024} KiB")
    return size

def create_embed(paste_result: dict, original_size: int, obf_size: int) -> discord.Embed:
    if paste_result['success']:
        embed = discord.Embed(
            title="вњ… РћР±С„СѓСЃРєР°С†РёСЏ Р·Р°РІРµСЂС€РµРЅР°!",
            description="рџ›ЎпёЏ Р—Р°С‰РёС‚Р°: **MAXIMUM**",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        embed.add_field(name="рџ”— РЎСЃС‹Р»РєР°", value=f"[Pastefy]({paste_result['url']})", inline=False)
        embed.add_field(name="рџ“‹ Raw", value=f"[РљРѕРїРёСЂРѕРІР°С‚СЊ]({paste_result['raw_url']})", inline=False)
    else:
        embed = discord.Embed(
            title="вљ пёЏ Pastefy РЅРµРґРѕСЃС‚СѓРїРµРЅ",
            description=f"РћС€РёР±РєР°: `{paste_result['error']}`",
            color=0xffaa00,
            timestamp=datetime.now()
        )

    embed.add_field(name="рџ“¦ РСЃС…РѕРґРЅС‹Р№", value=f"`{original_size}` Р±Р°Р№С‚", inline=True)
    embed.add_field(name="рџ“¦ РћР±С„СѓСЃС†РёСЂРѕРІР°РЅРЅС‹Р№", value=f"`{obf_size}` Р±Р°Р№С‚", inline=True)
    embed.add_field(
        name="рџ”ђ РњРµС‚РѕРґС‹",
        value="Multi-key XOR, Splitting, Rename, Minify, Junk, Numbers, Wrapper",
        inline=False
    )
    embed.add_field(
        name="вљ™пёЏ РЎРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ",
        value="`loadstring` В· `game:HttpGet` В· `syn.request` В· `getgenv` В· "
              "`hookfunction` В· `queue_on_teleport` В· `Drawing` В· 250+ executor API",
        inline=False
    )
    return embed

@bot.tree.command(name="obfuscate", description="рџ”’ РћР±С„СѓСЃС†РёСЂРѕРІР°С‚СЊ Roblox-СЃРєСЂРёРїС‚ (MAX Р·Р°С‰РёС‚Р°)")
@app_commands.describe(
    code="Lua-РєРѕРґ РґР»СЏ РѕР±С„СѓСЃРєР°С†РёРё",
    title="РќР°Р·РІР°РЅРёРµ РїР°СЃС‚С‹"
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
            raise ValueError("Р РµР·СѓР»СЊС‚Р°С‚ СЃР»РёС€РєРѕРј Р±РѕР»СЊС€РѕР№ РґР»СЏ РѕС‚РїСЂР°РІРєРё РІ Discord")

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
        await interaction.followup.send(f"вќЊ РћС€РёР±РєР°: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="obfuscate_file", description="рџ“Ѓ Р—Р°РіСЂСѓР·РёС‚СЊ .lua С„Р°Р№Р» (MAX Р·Р°С‰РёС‚Р°)")
@app_commands.describe(file="Р¤Р°Р№Р» .lua")
async def obfuscate_file(
    interaction: discord.Interaction,
    file: discord.Attachment
):
    if not file.filename.endswith('.lua'):
        await interaction.response.send_message("вќЊ РўРѕР»СЊРєРѕ `.lua`!", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        content = await file.read()
        code = content.decode('utf-8')
        original_size = validate_code_size(code)

        obfuscated = bot.obf.obfuscate(code)
        obf_size = len(obfuscated.encode('utf-8'))
        if obf_size > MAX_OUTPUT_BYTES:
            raise ValueError("Р РµР·СѓР»СЊС‚Р°С‚ СЃР»РёС€РєРѕРј Р±РѕР»СЊС€РѕР№ РґР»СЏ РѕС‚РїСЂР°РІРєРё РІ Discord")

        paste_result = await upload_to_pastefy(f"Obfuscated {file.filename}", obfuscated)
        embed = create_embed(paste_result, original_size, obf_size)
        embed.set_footer(text=f"Р¤Р°Р№Р»: {file.filename}")

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
        await interaction.followup.send(f"вќЊ РћС€РёР±РєР°: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="ping", description="рџЏ“ РџСЂРѕРІРµСЂРєР°")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="рџЏ“ Pong!", description=f"`{latency}ms`", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="рџ“– РЎРїСЂР°РІРєР°")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="рџ”’ IRY HUB OBF",
        description="РџСЂРѕРґРІРёРЅСѓС‚С‹Р№ РѕР±С„СѓСЃРєР°С‚РѕСЂ Roblox-СЃРєСЂРёРїС‚РѕРІ\nрџ›ЎпёЏ Р РµР¶РёРј СЃ РїСЂРёРѕСЂРёС‚РµС‚РѕРј СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё",
        color=0x5865F2
    )
    embed.add_field(
        name="/obfuscate",
        value="РћР±С„СѓСЃС†РёСЂРѕРІР°С‚СЊ РєРѕРґ\n`code` вЂ” Lua-РєРѕРґ\n`title` вЂ” РЅР°Р·РІР°РЅРёРµ РїР°СЃС‚С‹",
        inline=False
    )
    embed.add_field(
        name="/obfuscate_file",
        value="РћР±С„СѓСЃС†РёСЂРѕРІР°С‚СЊ `.lua` С„Р°Р№Р»",
        inline=False
    )
    embed.add_field(
        name="рџ›ЎпёЏ РњРµС‚РѕРґС‹ Р·Р°С‰РёС‚С‹",
        value="Multi-key XOR-С€РёС„СЂРѕРІР°РЅРёРµ СЃС‚СЂРѕРє В· Р Р°Р·Р±РёРµРЅРёРµ СЃС‚СЂРѕРє РЅР° С‡Р°СЃС‚Рё В· "
              "РџРµСЂРµРёРјРµРЅРѕРІР°РЅРёРµ РїРµСЂРµРјРµРЅРЅС‹С… В· РћР±С„СѓСЃРєР°С†РёСЏ С‡РёСЃРµР» В· Junk-РєРѕРґ В· "
              "Minification (РІРµСЃСЊ РєРѕРґ РІ РѕРґРЅСѓ СЃС‚СЂРѕРєСѓ)",
        inline=False
    )
    embed.add_field(
        name="вљ™пёЏ РџРѕР»РЅР°СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ",
        value="`loadstring(game:HttpGet())` В· `syn.request` В· `request` В· `http_request` В· "
              "`getgenv` В· `gethui` В· `identifyexecutor` В· `queue_on_teleport` В· "
              "`setclipboard` В· `writefile` В· `hookfunction` В· `hookmetamethod` В· "
              "`Drawing` В· `WebSocket` В· `getrawmetatable` В· `newcclosure` Рё РґСЂ.",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if not TOKEN:
        print("вќЊ РЈРєР°Р¶РёС‚Рµ DISCORD_TOKEN!")
        exit(1)
    bot.run(TOKEN)
