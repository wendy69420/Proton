import discord
from discord.ext import commands


class _voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """Voice commands"""
  
    def help_custom(self):
		      emoji = '🎤'
		      label = "Voice Commands"
		      description = ""
		      return emoji, label, description

    @commands.group()
    async def __Voice__(self, ctx: commands.Context):
        """
        `voice` , `voice kick` , `voice kickall` , `voice mute` , `voice muteall` , `voice unmute` , `voice unmuteall` , `voice deafen` , `voice deafenall` , `voice undeafen` , `voice undeafenall` , `voice move` , `voice moveall` , `voice pull` , `voice pullall` , `voice lock` , `voice unlock` , `voice private` , `voice unprivate`\n\n**__VC Autorole__**\n`vcrole add` , `vcrole remove` , `vcrole config`"""






