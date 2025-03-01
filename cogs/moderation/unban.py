import discord
from discord.ext import commands
from discord import ui
from utils.Tools import *

class BanView(ui.View):
    def __init__(self, user, author):
        super().__init__(timeout=120)
        self.user = user
        self.author = author
        self.message = None  
        self.color = discord.Color.from_rgb(0, 0, 0)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @ui.button(label="Ban", style=discord.ButtonStyle.danger)
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReasonModal(user=self.user, author=self.author, view=self)
        await interaction.response.send_modal(modal)

    @ui.button(style=discord.ButtonStyle.gray, emoji="<:olympus_bin:1254336650075701308>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

class AlreadyUnbannedView(ui.View):
    def __init__(self, user, author):
        super().__init__(timeout=60)
        self.user = user
        self.author = author
        self.message = None  

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    @ui.button(label="Ban", style=discord.ButtonStyle.danger)
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReasonModal(user=self.user, author=self.author, view=self)
        await interaction.response.send_modal(modal)

    @ui.button(style=discord.ButtonStyle.gray, emoji="<:olympus_bin:1254336650075701308>")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

class ReasonModal(ui.Modal):
    def __init__(self, user, author, view):
        super().__init__(title="Ban Reason")
        self.user = user
        self.author = author
        self.view = view
        self.reason_input = ui.TextInput(label="Reason for Banning", placeholder="Provide a reason for banning or leave it blank for no reason.", required = False, max_length=2000, style=discord.TextStyle.paragraph)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value or "No reason provided"
        try:
            await self.user.send(f"<a:olympus_WarnFlash:1272569018183843874> You have been Banned from **{self.author.guild.name}** by **{self.author}**. Reason: {reason or 'No reason provided'}")
            dm_status = "Yes"
        except discord.Forbidden:
            dm_status = "No"
        except discord.HTTPException:
            dm_status = "No"

        embed = discord.Embed(description=f"**<:olympusUser:1294654665895579721> Target User:** [{self.user}](https://discord.com/users/{self.user.id})\n<:olympusMention:1294654604998475856> **User Mention:** {self.user.mention}\n**<:olympusDM:1295595078122999915> DM Sent:** {dm_status}\n**<:olympusReason:1295595129809141812> Reason:** {reason}", color=0x000000)
        embed.set_author(name=f"Successfully Banned {self.user.name}", icon_url=self.user.avatar.url if self.user.avatar else self.user.default_avatar.url)
        embed.add_field(name="<:olympusMod:1295601558985379852> Moderator:", value=interaction.user.mention, inline=False)
        embed.set_footer(text=f"Requested by {self.author}", icon_url=self.author.avatar.url if self.author.avatar else self.author.default_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        try:
            await interaction.guild.ban(self.user, reason=f"Ban requested by {self.author}")
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        try:
            await interaction.response.edit_message(embed=embed, view=self.view)
            for item in self.view.children:
                item.disabled = True
            await interaction.message.edit(view=self.view)
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass
            

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = discord.Color.from_rgb(0, 0, 0)

    def get_user_avatar(self, user):
        return user.avatar.url if user.avatar else user.default_avatar.url

    @commands.hybrid_command(
        name="unban",
        help="Unbans a user from the Server",
        usage="unban <member>",
        aliases=["forgive", "pardon"])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason=None):
        bans = [entry async for entry in ctx.guild.bans()]
        if not any(ban_entry.user.id == user.id for ban_entry in bans):
            embed = discord.Embed(description="**Requested User is not banned in this server.**", color=self.color)
            embed.add_field(name="__Ban__:", value="Click on the `Ban` button to ban the mentioned user.")
            embed.set_author(name=f"{user.name} is Not Banned!", icon_url=self.get_user_avatar(user))
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=self.get_user_avatar(ctx.author))
            view = AlreadyUnbannedView(user=user, author=ctx.author)
            message = await ctx.send(embed=embed, view=view)
            view.message = message 
            return

        try:
            await user.send(f"<:Ztick:1222750301233090600> You have been unbanned from **{ctx.guild.name}** by **{ctx.author}**. Reason: {reason or 'No reason provided'}")
            dm_status = "Yes"
        except discord.Forbidden:
            dm_status = "No"
        except discord.HTTPException:
            dm_status = "No"

        await ctx.guild.unban(user, reason=f"Unban requested by {ctx.author} for reason: {reason or 'No reason provided'}")

        reasonn = reason or "No reason provided"
        embed = discord.Embed(description=f"**<:olympusUser:1294654665895579721> Target User:** [{user}](https://discord.com/users/{user.id})\n**<:olympusMention:1294654604998475856> User Mention:** {user.mention}\n**<:olympusDM:1295595078122999915> DM Sent:** {dm_status}\n**<:olympusReason:1295595129809141812> Reason:** {reasonn}", color=self.color)
        embed.set_author(name=f"Successfully Unbanned {user.name}", icon_url=self.get_user_avatar(user))
        embed.add_field(name="<:olympusMod:1295601558985379852> Moderator:", value=ctx.author.mention, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=self.get_user_avatar(ctx.author))
        embed.timestamp = discord.utils.utcnow()

        view = BanView(user=user, author=ctx.author)
        message = await ctx.send(embed=embed, view=view)
        view.message = message


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out Community or DM me.
"""