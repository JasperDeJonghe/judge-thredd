import discord
from datetime import time, timezone
from discord import app_commands
from discord.ext import tasks
import json
import os

# Variable

Medals = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

# helpers

def load_config() -> dict:
    if not os.path.exists("config.json"):
        print("Config not loaded - make sure you have config.json in the root of the folder")
        return {}
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def load_data() -> dict:
    if not os.path.exists("leaderboard.json"):
        return {}
    try:
        with open("leaderboard.json", "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data: dict):
    with open("leaderboard.json", "w") as f:
        json.dump(data, f, indent=4)

# client setup

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)   # holds all slash commands
        self.config = load_config()

    async def setup_hook(self):
        await self.tree.sync()   # registers commands with Discord on startup

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        giverole_loop.start()

client = MyClient()

# message counter (unchanged logic)

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.content.startswith("/"):
        return

    data = load_data()
    user = str(message.author.id)
    channelid = message.channel.id

    # Check if user already exists in the leaderboard
    if channelid in client.config["channels"]:
        if user in data:
            data[user] += 1
        else:
            data[user] = 1
            print(f"New user added to leaderboard: {message.author.name} (ID: {user})")

        save_data(data)

# post_leaderboard (shared logic)

async def post_leaderboard(guild: discord.Guild):
    data = load_data()

    if not data:
        return

    flipped = []
    for user_id, count in data.items():
        flipped.append((count, user_id))

    flipped.sort(reverse=True)
    top_5 = flipped[:5]

    embed = discord.Embed(title="Top 5 Helpers", color=discord.Color.gold())
    lines = []

    for index, (count, user_id) in enumerate(top_5):
        member = guild.get_member(int(user_id))

        if member is not None:
            name = member.name
        else:
            name = f"Unknown (ID: {user_id})"

        lines.append(f"{Medals[index]} {name} — {count} messages")

    embed.add_field(name="", value="\n".join(lines), inline=False)

    top_member = guild.get_member(int(top_5[0][1]))
    if top_member is not None:
        embed.set_thumbnail(url=top_member.display_avatar.url)

    output_channel = client.get_channel(int(client.config["output_channel"]))
    await output_channel.send(embed=embed)

# leaderboard command

# Uncomment this part if you want to manually call the leaderboard command

# @client.tree.command(name="leaderboard", description="Show the message leaderboard")
# async def leaderboard(interaction: discord.Interaction):
#     data = load_data()

#     if not data:
#         await interaction.response.send_message("Leaderboard is empty.")
#         return

#     await post_leaderboard(interaction.guild)
#     await interaction.response.send_message("Leaderboard posted!")



# giverole

@tasks.loop(time=time(hour=client.config["reset_hour"], minute=client.config["reset_min"], tzinfo=timezone.utc))
async def giverole_loop():
    data = load_data()
    if not data:
        print("No data available.")
        return

    guild = client.guilds[0]
    
    await post_leaderboard(guild)
    
    trophee_role = discord.utils.get(guild.roles, name=client.config["role"])
    if not trophee_role:
        print("role not found.")
        return

    top_user_id = max(data, key=data.get)
    try:
        top_member = await guild.fetch_member(int(top_user_id))
    except discord.NotFound:
        print("Top user not found in server.")
        return

    # Remove role from everyone who currently has it
    for member in trophee_role.members:
        try:
            await member.remove_roles(trophee_role)
        except discord.Forbidden:
            print(f"Cannot remove Trophee from {member.mention}.")

    # Award role to the winner
    try:
        await top_member.add_roles(trophee_role)
        embed_announcement = discord.Embed(title=f"{top_member} is the new best helper!", color=discord.Color.gold())
        output_channel = client.get_channel(int(client.config["output_channel"]))
        await output_channel.send(embed=embed_announcement)
        
        print(f"{top_member.mention} is now the top helper!")
    except discord.Forbidden:
        print("Missing permissions to assign role.")
        return

    save_data({})
    print("Leaderboard has been reset.")

# run

client.run(client.config["api_key"])