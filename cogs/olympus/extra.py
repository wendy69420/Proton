import discord
from discord.ext import commands


class _extra(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Utility commands"""
  
    def help_custom(self):
		      emoji = '⚙️'
		      label = "Utility Commands"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Utility__(self, ctx: commands.Context):
        """`botinfo` , `stats` , `invite` , `serverinfo` , `userinfo` , `roleinfo` , `boostcount` , `unbanall` ,  `joined-at` , `ping` , `github` , `vcinfo` , `channelinfo` , `badges` , `banner user` , `banner server` , `reminder start` , `reminder clear` , `permissions` , `timer`\n\n__**Media Commands**__\n`media` , `media setup ` , `media remove` , `media config` , `media bypass` , `media bypass add` , `media bypass remove` , `media bypass show`"""