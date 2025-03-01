import discord
from discord.ext import commands
from datetime import datetime
from utils.Tools import *

class SnipeView(discord.ui.View):
    def __init__(self, bot, snipes, user_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.snipes = snipes
        self.index = 0
        self.user_id = user_id
        self.update_buttons()

    def update_buttons(self):
        self.first_button.disabled = self.index == 0 or len(self.snipes) == 1
        self.prev_button.disabled = self.index == 0 or len(self.snipes) == 1
        self.next_button.disabled = self.index == len(self.snipes) - 1 or len(self.snipes) == 1
        self.last_button.disabled = self.index == len(self.snipes) - 1 or len(self.snipes) == 1

    async def send_snipe_embed(self, interaction: discord.Interaction):
        snipe = self.snipes[self.index]
        embed = discord.Embed(color=0x000000)
        embed.set_author(name=f"Deleted Message {self.index + 1}/{len(self.snipes)}", icon_url=snipe['author_avatar'])
        uid = snipe['author_id']
        display_name = snipe['author_name']
        embed.description = (
            f"<:olympusUser:1294654665895579721> **Author:** **[{display_name}](https://discord.com/users/{uid})**\n"
            f"<:olympusID:1294654633821863967> **Author ID:** `{snipe['author_id']}`\n"
            f"<:olympusMention:1294654604998475856> **Author Mention:** <@{snipe['author_id']}>\n"
            f"<:olympusTime:1294654567539277824> **Deleted:** <t:{snipe['deleted_at']}:R>\n"
        )

        if snipe['content']:
            embed.add_field(name="<:olympus_bin:1254336650075701308> **Content:**", value=snipe['content'])
        if snipe['attachments']:
            attachment_links = "\n".join([f"[{attachment['name']}]({attachment['url']})" for attachment in snipe['attachments']])
            embed.add_field(name="<:olympusMedia:1294574309565534229> **Attachments:**", value=attachment_links)

        embed.set_footer(text=f"Total Deleted Messages: {len(self.snipes)} | Requested by {interaction.user}", icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(emoji="<:olympus_first:1254347208254558279>", style=discord.ButtonStyle.secondary, custom_id="first")
    async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = 0
        self.update_buttons()
        await self.send_snipe_embed(interaction)

    @discord.ui.button(emoji="<:olympus_backward:1254314965351923795>", style=discord.ButtonStyle.secondary, custom_id="previous")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        self.update_buttons()
        await self.send_snipe_embed(interaction)

    @discord.ui.button(emoji="<:olympus_bin:1254336650075701308>", style=discord.ButtonStyle.danger, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    @discord.ui.button(emoji="<:olympus_forward:1254314940668317717>", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.snipes) - 1:
            self.index += 1
        self.update_buttons()
        await self.send_snipe_embed(interaction)

    @discord.ui.button(emoji="<:olympus_last:1254347295122526208>", style=discord.ButtonStyle.secondary, custom_id="last")
    async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = len(self.snipes) - 1
        self.update_buttons()
        await self.send_snipe_embed(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipes = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        if message.channel.id not in self.snipes:
            self.snipes[message.channel.id] = []
        if len(self.snipes[message.channel.id]) >= 10:
            self.snipes[message.channel.id].pop(0)

        attachments = []
        if message.attachments:
            attachments = [{'name': attachment.filename, 'url': attachment.url} for attachment in message.attachments]

        self.snipes[message.channel.id].insert(0, {
            'author_name': message.author.name,
            'author_avatar': message.author.avatar.url,
            'author_id': message.author.id,
            'content': message.content or None,
            'deleted_at': int(datetime.utcnow().timestamp()),
            'attachments': attachments
        })

    @commands.hybrid_command(name='snipe', help="Shows the recently deleted messages in the channel.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx):
        channel_snipes = self.snipes.get(ctx.channel.id, [])
        if not channel_snipes:
            await ctx.send("No recently deleted messages found in this channel.")
            return

        first_snipe = channel_snipes[0]
        embed = discord.Embed(color=0x000000)
        embed.set_author(name="Last Deleted Message", icon_url=first_snipe['author_avatar'])
        uid = first_snipe['author_id']
        display_name = first_snipe['author_name']
        embed.description = (
            f"<:olympusUser:1294654665895579721> **Author:** **[{display_name}](https://discord.com/users/{uid})**\n"
            f"<:olympusID:1294654633821863967> **Author ID:** `{first_snipe['author_id']}`\n"
            f"<:olympusMention:1294654604998475856> **Author Mention:** <@{first_snipe['author_id']}>\n"
            f"<:olympusTime:1294654567539277824> **Deleted:** <t:{first_snipe['deleted_at']}:R>\n"
        )

        if first_snipe['content']:
            embed.add_field(name="<:olympus_bin:1254336650075701308> **Content:**", value=first_snipe['content'])
        if first_snipe['attachments']:
            attachment_links = "\n".join([f"[{attachment['name']}]({attachment['url']})" for attachment in first_snipe['attachments']])
            embed.add_field(name="<:olympusMedia:1294574309565534229> **Attachments:**", value=attachment_links)

        embed.set_footer(text=f"Total Deleted Messages: {len(channel_snipes)} | Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        view = SnipeView(self.bot, channel_snipes, ctx.author.id)

        if len(channel_snipes) > 1:
            message = await ctx.send(embed=embed, view=view)
            view.message = message
        else:
            view.first_button.disabled = True
            view.prev_button.disabled = True
            view.next_button.disabled = True
            view.last_button.disabled = True
            message = await ctx.send(embed=embed, view=view)
            view.message = message

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out Community or DM me.
"""