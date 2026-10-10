import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import json
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

PLAYERS_FILE = "players.json"
REDEEMED_CODES_FILE = "redeemed_codes.json"

def load_data(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
        return default
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

players_list = load_data(PLAYERS_FILE, [])
redeemed_codes = load_data(REDEEMED_CODES_FILE, [])

def process_redemption(code, player_id):
    url = "https://ks-giftcode.centurygame.com/api/redeem"
    payload = {"fid": str(player_id), "cdk": str(code)}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        return res.json()
    except Exception as e:
        return {"code": -1, "msg": str(e)}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    if not auto_redeemer_task.is_running():
        auto_redeemer_task.start()

# Slash Command: Add Player
@bot.tree.command(name="add_player", description="Add a player to the alliance auto-redeem list")
@app_commands.describe(player_id="The KingShot Player ID (FID)", nickname="Player's in-game name")
async def add_player(interaction: discord.Interaction, player_id: str, nickname: str):
    global players_list
    for p in players_list:
        if p["id"] == player_id:
            await interaction.response.send_message(f"Player ID `{player_id}` is already in the list!", ephemeral=True)
            return
    
    players_list.append({"id": player_id, "name": nickname})
    save_data(PLAYERS_FILE, players_list)
    await interaction.response.send_message(f"✅ Added **{nickname}** (`{player_id}`) to alliance roster!")

# Slash Command: Remove Player
@bot.tree.command(name="remove_player", description="Remove a player from the auto-redeem list")
async def remove_player(interaction: discord.Interaction, player_id: str):
    global players_list
    initial_len = len(players_list)
    players_list = [p for p in players_list if p["id"] != player_id]
    
    if len(players_list) < initial_len:
        save_data(PLAYERS_FILE, players_list)
        await interaction.response.send_message(f"🗑️ Removed Player ID `{player_id}` from roster.")
    else:
        await interaction.response.send_message(f"Player ID `{player_id}` not found in roster.", ephemeral=True)

# Slash Command: List Players
@bot.tree.command(name="list_players", description="View all registered alliance players")
async def list_players(interaction: discord.Interaction):
    if not players_list:
        await interaction.response.send_message("No players registered yet.", ephemeral=True)
        return
    
    msg = "**👑 Alliance Roster for Auto-Redeem:**\n"
    for idx, p in enumerate(players_list, 1):
        msg += f"{idx}. **{p['name']}** — `{p['id']}`\n"
    
    await interaction.response.send_message(msg)

# Slash Command: Manual Alliance Redeem
@bot.tree.command(name="redeem", description="Manually trigger code redemption for the entire alliance")
async def redeem(interaction: discord.Interaction, code: str):
    await interaction.response.defer()
    
    if not players_list:
        await interaction.followup.send("No players in roster. Use `/add_player` first.")
        return

    success_count = 0
    already_claimed = 0
    failed_count = 0

    for player in players_list:
        res = process_redemption(code, player["id"])
        err_code = res.get("err_code", -1)
        
        if err_code == 0 or res.get("code") == 0:
            success_count += 1
        elif err_code == 40008 or "claimed" in str(res).lower():
            already_claimed += 1
        else:
            failed_count += 1
            
        await asyncio.sleep(1) # Rate limit safety delay

    embed = discord.Embed(title=f"🎁 Code Redemption Results: `{code}`", color=0x00FF00)
    embed.add_field(name="✅ Success", value=str(success_count), inline=True)
    embed.add_field(name="🟡 Already Claimed", value=str(already_claimed), inline=True)
    embed.add_field(name="❌ Failed", value=str(failed_count), inline=True)
    
    await interaction.followup.send(embed=embed)

# 24/7 Background Auto-Redeemer Task (Runs every 15 mins)
@tasks.loop(minutes=15)
async def auto_redeemer_task():
    global redeemed_codes
    if not players_list:
        return
        
    try:
        res = requests.get("https://kingshot.net/api/gift-codes", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code != 200:
            return
        
        active_codes = res.json().get("codes", [])
        for code_obj in active_codes:
            code = code_obj if isinstance(code_obj, str) else code_obj.get("code")
            if not code or code in redeemed_codes:
                continue
                
            print(f"Auto-redeeming new code found: {code}")
            for player in players_list:
                process_redemption(code, player["id"])
                await asyncio.sleep(1)
                
            redeemed_codes.append(code)
            save_data(REDEEMED_CODES_FILE, redeemed_codes)
            
    except Exception as e:
        print(f"Auto-redeemer background error: {e}")

bot.run(TOKEN)
