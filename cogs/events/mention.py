from utils import getConfig  
import discord
from discord.ext import commands
from utils.Tools import get_ignore_data
import aiosqlite

class Mention(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.color = 0xdc143c
        self.bot_name = "Olympus"

    async def is_blacklisted(self, message):
        async with aiosqlite.connect("db/block.db") as db:
            cursor = await db.execute("SELECT 1 FROM guild_blacklist WHERE guild_id = ?", (message.guild.id,))
            if await cursor.fetchone():
                return True
                
            cursor = await db.execute("SELECT 1 FROM user_blacklist WHERE user_id = ?", (message.author.id,))
            if await cursor.fetchone():
                return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if await self.is_blacklisted(message):
            return

        ignore_data = await get_ignore_data(message.guild.id)
        if str(message.author.id) in ignore_data["user"] or str(message.channel.id) in ignore_data["channel"]:
            return

        if message.reference and message.reference.resolved:
            if isinstance(message.reference.resolved, discord.Message):
                if message.reference.resolved.author.id == self.bot.user.id:
                    return

        guild_id = message.guild.id
        data = await getConfig(guild_id) 
        prefix = data["prefix"]

        if self.bot.user in message.mentions:
            if len(message.content.strip().split()) == 1:
                embed = discord.Embed(
                    title=f"{message.guild.name}",
                    color=self.color,
                    description=f"Hey {message.author.mention},\nPrefix For This Server is `{prefix}`\nServer ID: {message.guild.id}\n\nType `{prefix}help` for more information."
                )
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embed.set_footer(text="Powered by Olympus Development™", icon_url=self.bot.user.avatar.url)

                buttons = [
                    discord.ui.Button(label="Invite", style=discord.ButtonStyle.link, url="https://discord.com/oauth2/authorize?client_id=1144179659735572640&permissions=2113268958&scope=bot"),
                    discord.ui.Button(label="Web", style=discord.ButtonStyle.link, url="https://olyumpus.vercel.app/"),
                    discord.ui.Button(label="Support", style=discord.ButtonStyle.link, url="https://discord.com/invite/odx"),
                ]

                view = discord.ui.View()
                for button in buttons:
                    view.add_item(button)

                await message.channel.send(embed=embed, view=view)
