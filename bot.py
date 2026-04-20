import discord
import random
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
        
def save_config(config: dict):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

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
        if not giverole_loop.is_running():
            giverole_loop.start()

client = MyClient()

# message counter (unchanged logic)

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.content.startswith("/"):
        return
    
    if client.user.mentioned_in(message) and not message.mention_everyone:
        responses = [
            "I am the law!",
            "I am the law! And you'd better believe it!",
            "I knew you'd say that",
            "You want fear? I'm the fear. You want chaos? I'm the chaos. You want a new beginning? I am the new beginning!",
            "It's a lie! The evidence has been falsified! It's impossible! I never broke the law, I AM THE LAW!",
            "Court's adjourned!",
            "YOU BETRAYED THE LAW! LAWWWWWW!",
            "You wanna be afraid of somebody, be afraid of ME!",
            "I'm alive! I'm alive! Oh... so are you.",
            "Emotions? There ought to be a law against them.",
            "Mission? Mission? We're going to war. WARRRRR.",
            "I've never apologized.",
            "I'll be the judge of that.",
            "Double whammy",
        ]
        await message.channel.send(random.choice(responses))
        return

    data = load_data()
    user = str(message.author.id)
    channelid = message.channel.id

    if channelid in client.config["channels"]:
        if "sorry" in message.content.lower():
            await message.reply("I've never apologized.")
        
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


@client.tree.command(name="law-here", description="Add or remove this channelID from the config")
async def law_here(interaction: discord.Interaction):
    user_role_names = [role.name for role in interaction.user.roles]
    allowed = client.config["allowed_roles"]
    has_permission = any(role in user_role_names for role in allowed)
    
    if not has_permission:
        await interaction.response.send_message("No clearance. No appeal. Move.", ephemeral=True)
        return

    channels = client.config["channels"]
    if interaction.channel_id in channels:
        channels.remove(interaction.channel_id)
        save_config(client.config)
        await interaction.response.send_message("Removed. The law has spoken.", ephemeral=False)
    else:
        channels.append(interaction.channel_id)
        save_config(client.config)
        await interaction.response.send_message("The law has eyes here now.", ephemeral=False)
        

# leaderboard command

@client.tree.command(name="law-now", description="call the loop manually")
async def law_now(interaction: discord.Interaction):
    user_role_names = [role.name for role in interaction.user.roles]
    allowed = client.config["allowed_roles"]
    has_permission = any(role in user_role_names for role in allowed)
    
    if not has_permission:
        await interaction.response.send_message("No clearance. No appeal. Move.", ephemeral=True)
        return
    else:
        await interaction.response.send_message("The law has spoken", ephemeral=True)
    
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
    
    
    


# giverole

@tasks.loop(time=time(hour=client.config["reset_hour"], minute=client.config["reset_min"], tzinfo=timezone.utc))
async def giverole_loop():
    
    # Remove this block to make it daily:
    from datetime import datetime
    if datetime.now(timezone.utc).weekday() != client.config["reset_day"]:
        return
    # End block
    
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

