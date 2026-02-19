import discord
import json
import os

class MyClient(discord.Client):

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Ensure leaderboard file exists
        if not os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "w") as f:
                json.dump({}, f)

        # Load leaderboard data
        try:
            with open("leaderboard.json", "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

        user = str(message.author.id)

        # Count messages (ignore commands)
        if not message.content.startswith("!"):
            if user in data:
                data[user] += 1
            else:
                data[user] = 1

            with open("leaderboard.json", "w") as f:
                json.dump(data, f, indent=4)

        # -----------------------
        # SHOW LEADERBOARD
        # -----------------------
        if message.content.startswith('!leaderboard'):
            if not data:
                await message.channel.send("Leaderboard is empty.")
            else:
                msg_lines = []
                for user_id, count in data.items():
                    member = message.guild.get_member(int(user_id))
                    name = member.name if member else f"Unknown({user_id})"
                    msg_lines.append(f"{name}: {count}")
                await message.channel.send("\n".join(msg_lines))
            return

        # GIVE ROLE TO TOP USER
        if message.content.startswith('!giverole'):
            if not data:
                await message.channel.send("No data available.")
                return

            guild = message.guild
            trophee_role = discord.utils.get(guild.roles, name="Trophee")

            if not trophee_role:
                await message.channel.send("Trophee role not found.")
                return

            # Find top user
            top_user_id = max(data, key=data.get)

            try:
                top_member = await guild.fetch_member(int(top_user_id))
            except discord.NotFound:
                await message.channel.send("Top user not found in server.")
                return

            # Remove role from everyone
            for member in trophee_role.members:
                try:
                    await member.remove_roles(trophee_role)
                except discord.Forbidden:
                    await message.channel.send(f"Cannot remove Trophee from {member.mention}.")

            # Give role to top member
            try:
                await top_member.add_roles(trophee_role)
                await message.channel.send(f"{top_member.mention} is now the top player!")
            except discord.Forbidden:
                await message.channel.send("Missing permissions to assign role.")
                return

            # Reset leaderboard
            with open("leaderboard.json", "w") as f:
                json.dump({}, f, indent=4)

            await message.channel.send("Leaderboard has been reset.")
            return


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

# Replace with your own bot api token
client.run("")
