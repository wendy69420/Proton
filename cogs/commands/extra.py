import os 
import discord
from discord.ext import commands
import datetime
import sys
from discord.ui import Button, View
import psutil
import time
from utils.Tools import *
from discord.ext import commands, menus
from discord.ext.commands import BucketType, cooldown
import requests
from typing import *
from utils import *
from utils.config import BotName, serverLink
from utils import Paginator, DescriptionEmbedPaginator, FieldPagePaginator, TextPaginator
from core import Cog, Olympus, Context
from typing import Optional
import aiosqlite 
import asyncio
import aiohttp


start_time = time.time()


def datetime_to_seconds(thing: datetime.datetime):
  current_time = datetime.datetime.fromtimestamp(time.time())
  return round(
    round(time.time()) +
    (current_time - thing.replace(tzinfo=None)).total_seconds())

tick = "<:olympus_tick:1227866641027698792>"
cross = "<:olympus_cross:1227866668152393789>"


class RoleInfoView(View):
  def __init__(self, role: discord.Role, author_id):
    super().__init__(timeout=180)
    self.role = role
    self.author_id = author_id

  @discord.ui.button(label='Show Permissions',  emoji="<:admin:1205192382975582321>", style=discord.ButtonStyle.secondary)
  async def show_permissions(self, interaction: discord.Interaction, button: Button):
    if interaction.user.id != self.author_id:
          await interaction.response.send_message("Uh oh! That message doesn't belong to you. You must run this command to interact with it.", ephemeral=True)
          return

    permissions = [perm.replace("_", " ").title() for perm, value in self.role.permissions if value]
    permission_text = ", ".join(permissions) if permissions else "None"
    embed = discord.Embed(title=f"Permissions for {self.role.name}", description=permission_text or "No permissions.", color=self.role.color)
    await interaction.response.send_message(embed=embed, ephemeral=True)

    
class OverwritesView(View):
  def __init__(self, channel, author_id):
      super().__init__(timeout=180)
      self.channel = channel
      self.author_id = author_id

  @discord.ui.button(label='Show Overwrites', style=discord.ButtonStyle.primary)
  async def show_overwrites(self, interaction: discord.Interaction, button: Button):
      if interaction.user.id != self.author_id:
          await interaction.response.send_message("Uh oh! That message doesn't belong to you. You must run this command to interact with it.", ephemeral=True)
          return

      overwrites = []
      for target, perms in self.channel.overwrites.items():
          permissions = {
              "View Channel": perms.view_channel,
              "Send Messages": perms.send_messages,
              "Read Message History": perms.read_message_history,
              "Manage Messages": perms.manage_messages,
              "Embed Links": perms.embed_links,
              "Attach Files": perms.attach_files,
              "Manage Channels": perms.manage_channels,
              "Manage Permissions": perms.manage_permissions,
              "Manage Webhooks": perms.manage_webhooks,
              "Create Instant Invite": perms.create_instant_invite,
              "Add Reactions": perms.add_reactions,
              "Mention Everyone": perms.mention_everyone,
              "Kick Members": perms.kick_members,
              "Ban Members": perms.ban_members,
              "Moderate Members": perms.moderate_members,
              "Send TTS Messages": perms.send_tts_messages,
              "Use External Emojis": perms.external_emojis,
              "Use External Stickers": perms.external_stickers,
              "View Audit Log": perms.view_audit_log,
              "Voice Mute Members": perms.mute_members,
              "Voice Deafen Members": perms.deafen_members,
              "Administrator": perms.administrator
          }

          overwrites.append(f"**For {target.name}**\n" +
                            "\n".join(f"  * **{perm}:** {'✅' if value else '❌' if value is False else '⛔'}" for perm, value in permissions.items()))

      embed = discord.Embed(title=f"Overwrites for {self.channel.name}", color=discord.Color.blurple())
      embed.description = "\n".join(overwrites) if overwrites else "No overwrites for this channel."
      embed.set_footer(text="✅ = Allowed, ❌ = Denied, ⛔ = None")
      await interaction.response.send_message(embed=embed, ephemeral=True)




class Extra(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.color = 0x000000
    self.start_time = datetime.datetime.now()

  @commands.hybrid_group(name="banner")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def banner(self, ctx):
    if ctx.invoked_subcommand is None:
      await ctx.send_help(ctx.command)

  @banner.command(name="server")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  async def server(self, ctx):
    if not ctx.guild.banner:
      await ctx.reply(f"{cross} This server doesn't have a banner.")
    else:
      webp = ctx.guild.banner.replace(format='webp')
      jpg = ctx.guild.banner.replace(format='jpg')
      png = ctx.guild.banner.replace(format='png')
      embed = discord.Embed(
        color=self.color,
        description=f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"
        if not ctx.guild.banner.is_animated() else
        f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp}) | [`GIF`]({ctx.guild.banner.replace(format='gif')})"
      )
      embed.set_image(url=ctx.guild.banner)
      embed.set_author(name=ctx.guild.name,
                       icon_url=ctx.guild.icon.url
                       if ctx.guild.icon else ctx.guild.default_icon.url)
      embed.set_footer(text=f"Requested By {ctx.author}",
                       icon_url=ctx.author.avatar.url
                       if ctx.author.avatar else ctx.author.default_avatar.url)
      await ctx.reply(embed=embed)

  
  @banner.command(name="user")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  async def _user(self,
                  ctx,
                  member: Optional[Union[discord.Member,
                                         discord.User]] = None):
    if member == None or member == "":
      member = ctx.author
    bannerUser = await self.bot.fetch_user(member.id)
    if not bannerUser.banner:
      await ctx.reply("{} | {} doesn't have a banner.".format(cross, member))
    else:
      webp = bannerUser.banner.replace(format='webp')
      jpg = bannerUser.banner.replace(format='jpg')
      png = bannerUser.banner.replace(format='png')
      embed = discord.Embed(
        color=self.color,
        description=f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"
        if not bannerUser.banner.is_animated() else
        f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp}) | [`GIF`]({bannerUser.banner.replace(format='gif')})"
      )
      embed.set_author(name=f"{member}",
                       icon_url=member.avatar.url
                       if member.avatar else member.default_avatar.url)
      embed.set_image(url=bannerUser.banner)
      embed.set_footer(text=f"Requested By {ctx.author}",
                       icon_url=ctx.author.avatar.url
                       if ctx.author.avatar else ctx.author.default_avatar.url)

      await ctx.send(embed=embed)


  
  

  @commands.command(name="uptime", description="Shows the Bot's Uptime.")
  @blacklist_check() 
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def uptime(self, ctx):
      pfp = ctx.author.display_avatar.url

      uptime_seconds = int(round(time.time() - start_time))
      uptime_timedelta = datetime.timedelta(seconds=uptime_seconds)

      uptime_string = f"Up since {datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')} UTC"
      uptime_duration_string = f"{uptime_timedelta.days} days, {uptime_timedelta.seconds // 3600} hours, {(uptime_timedelta.seconds // 60) % 60} minutes, {uptime_timedelta.seconds % 60} seconds"

      embed = discord.Embed(title=f"Olympus Uptime", color=self.color)
      embed.add_field(name="__UTC__", value=f"<:olympus_info:1227625594511163537> {uptime_string}\n\n", inline=False)
      embed.add_field(name="__Online Duration__", value=f"<:olympus_duration:1251052632949395538> {uptime_duration_string}", inline=False)
      embed.set_footer(text=f"Requested by {ctx.author}", icon_url=pfp)

      await ctx.send(embed=embed)

    

  @commands.hybrid_command(name="serverinfo",
                           aliases=["sinfo", "si"],
                           with_app_command=True)
  @blacklist_check() 
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def serverinfo(self, ctx):
        embed = discord.Embed(color=0x000000).set_author(
            name=f"{ctx.guild.name}'s Information",
            icon_url=ctx.guild.me.display_avatar.url if ctx.guild.icon is None else ctx.guild.icon.url
        ).set_footer(
            text=f"Requested By {ctx.author}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        )

        if ctx.guild.icon is not None:
            embed.set_thumbnail(url=ctx.guild.icon.url)
            embed.timestamp = discord.utils.utcnow()

        c_at = ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S")

        embed.add_field(
            name="**__About__**",
            value=f"**Name : ** {ctx.guild.name}\n**ID :** {ctx.guild.id}\n**Owner <:olympus_owner:1228227536207740989> :** {ctx.guild.owner} (<@{ctx.guild.owner_id}>)\n**Created At : ** {c_at}\n**Members :** {len(ctx.guild.members)}",
            inline=False
        )

        if ctx.guild.description:
            embed.add_field(
                name="**__Description__**",
                value=ctx.guild.description,
                inline=False
            )

        embed.add_field(
            name="**__General Stats__**",
            value=f"**Verification Level :** {ctx.guild.verification_level}\n**Channels :** {len(ctx.guild.channels)}\n**Roles :** {len(ctx.guild.roles)}\n**Emojis :** {len(ctx.guild.emojis)}\n**Boost Status :** Level {ctx.guild.premium_tier} (Boosts: {ctx.guild.premium_subscription_count})",
            inline=False
        )

        if ctx.guild.features:
            features = "\n".join([f"<:red_tick:1243492355969908746>: {feature[:1].upper() + feature[1:].lower().replace('_', ' ')}" for feature in ctx.guild.features])
            embed.add_field(
                name="**__Features__**",
                value=f"{features if len(features) <= 1024 else features[0:1000] + '...and more'}",
                inline=False
            )

        embed.add_field(
            name="**__Channels__**",
            value=f"**Total:** {len(ctx.guild.channels)}\nChannels: {len(ctx.guild.text_channels)} text, {len(ctx.guild.voice_channels)} voice",
            inline=False
        )

        regular_emojis = [emoji for emoji in ctx.guild.emojis if not emoji.animated]
        animated_emojis = [emoji for emoji in ctx.guild.emojis if emoji.animated]
        disabled_emojis = len(ctx.guild.emojis) - len(regular_emojis) - len(animated_emojis)

        embed.add_field(
            name="**__Emoji Info__**",
            value=f"Regular: {len(regular_emojis)}/100\nAnimated: {len(animated_emojis)}/100\nDisabled: {disabled_emojis} regular, {len(animated_emojis)} animated\nTotal Emoji: {len(ctx.guild.emojis)}/200",
            inline=False
        )

        embed.add_field(
            name="**__Boost Status__**",
            value=f"Level: {ctx.guild.premium_tier} [<:olympus_booster:1243448375328903199> {ctx.guild.premium_subscription_count} boosts]",
            inline=False
        )

        roles = ctx.guild.roles
        roles_list = [role.mention for role in roles]
        roles_count = len(roles_list)
        roles_display = "\n".join(roles_list[:10])

        if roles_count > 10:
            roles_display += f"\n...and {roles_count - 10} more"

        embed.add_field(
            name=f"**__Server Roles__ [ {roles_count} ]**",
            value=roles_display,
            inline=False
        )

        if ctx.guild.banner:
            embed.set_image(url=ctx.guild.banner)


        await ctx.send(embed=embed)
        

  
  @commands.hybrid_command(name="userinfo",
                           aliases=["whois", "ui"],
                           usage="Userinfo [user]",
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
  @commands.guild_only()
  async def _userinfo(self,
                      ctx,
                      member: Optional[Union[discord.Member,
                                             discord.User]] = None):
    if member == None or member == "":
      member = ctx.author
    elif member not in ctx.guild.members:
      member = await self.bot.fetch_user(member.id)

    badges = ""
    if member.public_flags.hypesquad:
      badges += "HypeSquad Events, "
    if member.public_flags.hypesquad_balance:
      badges += "HypeSquad Balance, "
    if member.public_flags.hypesquad_bravery:
      badges += "HypeSquad Bravery, "
    if member.public_flags.hypesquad_brilliance:
      badges += "HypeSquad Brilliance, "
    if member.public_flags.early_supporter:
      badges += "Early Supporter, "
    if member.public_flags.active_developer:
      badges += "Active Developer, "
    if member.public_flags.verified_bot_developer:
      badges += "Early Verified Bot Developer, "
    if member.public_flags.discord_certified_moderator:
      badges += "Moderators Program Alumni, "
    if member.public_flags.staff:
      badges += "Discord Staff, "
    if member.public_flags.partner:
      badges += "Partnered Server Owner "
    if badges == None or badges == "":
      badges += f"{cross}"

    if member in ctx.guild.members:
      nickk = f"{member.nick if member.nick else 'None'}"
      joinedat = f"<t:{round(member.joined_at.timestamp())}:R>"
    else:
      nickk = "None"
      joinedat = "None"

    kp = ""
    if member in ctx.guild.members:
      if member.guild_permissions.kick_members:
        kp += "Kick Members"
      if member.guild_permissions.ban_members:
        kp += " , Ban Members"
      if member.guild_permissions.administrator:
        kp += " , Administrator"
      if member.guild_permissions.manage_channels:
        kp += " , Manage Channels"
        
      if  member.guild_permissions.manage_guild:
        kp += " , Manage Server"
        
      if member.guild_permissions.manage_messages:
        kp += " , Manage Messages"
      if member.guild_permissions.mention_everyone:
        kp += " , Mention Everyone"
      if member.guild_permissions.manage_nicknames:
        kp += " , Manage Nicknames"
      if member.guild_permissions.manage_roles:
        kp += " , Manage Roles"
      if member.guild_permissions.manage_webhooks:
        kp += " , Manage Webhooks"
      if member.guild_permissions.manage_emojis:
        kp += " , Manage Emojis"

      if kp is None or kp == "":
        kp = "None"

    if member in ctx.guild.members:
      if member == ctx.guild.owner:
        aklm = "Server Owner"
      elif member.guild_permissions.administrator:
        aklm = "Server Admin"
      elif member.guild_permissions.ban_members or member.guild_permissions.kick_members:
        aklm = "Server Moderator"
      else:
        aklm = "Server Member"

    bannerUser = await self.bot.fetch_user(member.id)
    embed = discord.Embed(color=self.color)
    embed.timestamp = discord.utils.utcnow()
    if not bannerUser.banner:
      pass
    else:
      embed.set_image(url=bannerUser.banner)
    embed.set_author(name=f"{member.name}'s Information",
                     icon_url=member.avatar.url
                     if member.avatar else member.default_avatar.url)
    embed.set_thumbnail(
      url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="__General Information__",
                    value=f"""
**Name:** {member}
**ID:** {member.id}
**Nickname:** {nickk}
**Bot?:** {'<:olympus_tick:1227866641027698792> Yes' if member.bot else '<:olympus_cross:1227866668152393789> No'}
**Badges:** {badges}
**Account Created:** <t:{round(member.created_at.timestamp())}:R>
**Server Joined:** {joinedat}
            """,
                    inline=False)
    if member in ctx.guild.members:
      r = (', '.join(role.mention for role in member.roles[1:][::-1])
           if len(member.roles) > 1 else 'None.')
      embed.add_field(name="__Role Info__",
                      value=f"""
**Highest Role:** {member.top_role.mention if len(member.roles) > 1 else 'None'}
**Roles [{f'{len(member.roles) - 1}' if member.roles else '0'}]:** {r if len(r) <= 1024 else r[0:1006] + ' and more...'}
**Color:** {member.color if member.color else '99aab5'}
                """,
                      inline=False)
    if member in ctx.guild.members:
      embed.add_field(
        name="__Extra__",
        value=
        f"**Boosting:** {f'<t:{round(member.premium_since.timestamp())}:R>' if member in ctx.guild.premium_subscribers else 'None'}\n**Voice <:olympus_mic:1222790370216120382>:** {'None' if not member.voice else member.voice.channel.mention}",
        inline=False)
    if member in ctx.guild.members:
      embed.add_field(name="__Key Permissions__",
                      value=", ".join([kp]),
                      inline=False)
    if member in ctx.guild.members:
      embed.add_field(name="__Acknowledgement__",
                      value=f"{aklm}",
                      inline=False)
    if member in ctx.guild.members:
      embed.set_footer(text=f"Requested by {ctx.author}",
                       icon_url=ctx.author.avatar.url
                       if ctx.author.avatar else ctx.author.default_avatar.url)
    else:
      if member not in ctx.guild.members:
        embed.set_footer(text=f"{member.name} not in this server.",
                         icon_url=ctx.author.avatar.url if ctx.author.avatar
                         else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)



  @commands.hybrid_command(name='roleinfo', aliases=["ri"], help="Displays information about a specified role.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def roleinfo(self, ctx, role: discord.Role):
    members = role.members
    created_at = role.created_at.strftime("%Y-%m-%d %H:%M:%S")

    embed = discord.Embed(
      title=f"Role Information - {role.name}",
      color=role.color,
      timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1205191291323940874.png")
    embed.add_field(name="__General Information__", value=f"**ID:** {role.id}\n**Name:** {role.name}\n**Mention:** <@&{role.id}>\n**Color:** {str(role.color)}\n**Total Member:** {len(role.members)}\n", inline=True)
    total_roles = len(ctx.guild.roles) - 0
    role_position = total_roles - role.position
    embed.add_field(name="Position", value=str(role_position), inline=True)
    embed.add_field(name="Mentionable", value=str(role.mentionable), inline=True)
    embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
    embed.add_field(name="Managed", value=str(role.managed), inline=True)
    embed.add_field(name="Created At", value=created_at, inline=True)
    embed.set_footer(text=f"Requested By {ctx.author}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

    view = RoleInfoView(role, ctx.author.id)
    await ctx.send(embed=embed, view=view)





  @commands.command(name="boostcount",
                    help="Shows boosts count",
                    usage="boosts",
                    aliases=["bc"],
                    with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def boosts(self, ctx):
    await ctx.send(
      embed=discord.Embed(title=f"<:olympus_booster:1243448375328903199> Boosts Count Of {ctx.guild.name}",
                          description="**Total `%s` boosts**" %
                          (ctx.guild.premium_subscription_count),
                          color=self.color))

  @commands.hybrid_group(name="list",
                         invoke_without_command=True,
                         with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def __list_(self, ctx: commands.Context):
    if ctx.subcommand_passed is None:
      await ctx.send_help(ctx.command)
      ctx.command.reset_cooldown(ctx)

  @__list_.command(name="boosters",
                   aliases=["boost", "booster"],
                   usage="List boosters",
                   help="List of boosters in the Guild",
                   with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_boost(self, ctx):
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) [{mem.mention}] - <t:{round(mem.premium_since.timestamp())}:R>"
      for no, mem in enumerate(guild.premium_subscribers, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=
      f"List of Boosters in {guild.name} - {len(guild.premium_subscribers)}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="bans", help= "List of all banned members in Guild", aliases=["ban"], with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(view_audit_log=True)
  @commands.bot_has_permissions(view_audit_log=True)
  async def list_ban(self, ctx):
    bans = [member async for member in ctx.guild.bans()]
    if len(bans) == 0:
      return await ctx.reply("There aren't any banned users in this guild.", mention_author=False)
    else:
      mems = ([
      member async for member in ctx.guild.bans()
    ])
      guild = ctx.guild
      entries = [
      f"`#{no}.` {mem}"
      for no, mem in enumerate(mems, start=1)
    ]
      paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Banned Users in {guild.name} - {len(bans)}",
      description="",
      per_page=10),
                          ctx=ctx)
      await paginator.paginate()

  @__list_.command(
    name="inrole",
    aliases=["inside-role"],
    help="List of members that are in the specified role",
    with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_inrole(self, ctx, role: discord.Role):
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) [{mem.mention}] - <t:{int(mem.created_at.timestamp())}:D>"
      for no, mem in enumerate(role.members, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"List of Members in {role} - {len(role.members)}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="emojis",
                   aliases=["emoji"],
                   help="List of emojis in the Guild with ids",
                   with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_emojis(self, ctx):
    guild = ctx.guild
    entries = [
      f"`#{no}.` {e} - `{e}`"
      for no, e in enumerate(ctx.guild.emojis, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"List of Emojis in {guild.name} - {len(ctx.guild.emojis)}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="roles",
                   aliases=["role"],
                   help="List of all roles in the server with ids",
                   with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  @commands.has_permissions(manage_roles=True)
  async def list_roles(self, ctx):
    guild = ctx.guild
    entries = [
      f"`#{no}.` {e.mention} - `[{e.id}]`"
      for no, e in enumerate(ctx.guild.roles, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"List of Roles in {guild.name} - {len(ctx.guild.roles)}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="bots",
                   aliases=["bot"],
                   help="List of All Bots in a server",
                   with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_bots(self, ctx):
    guild = ctx.guild
    people = filter(lambda member: member.bot, ctx.guild.members)
    people = sorted(people, key=lambda member: member.joined_at)
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) [{mem.mention}]"
      for no, mem in enumerate(people, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Bots in {guild.name} - {len(people)}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="admins",
                   aliases=["admin"],
                   help="List of all Admins of the Guild",
                   with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_admin(self, ctx):
    mems = ([
      mem for mem in ctx.guild.members
      if mem.guild_permissions.administrator
    ])
    mems = sorted(mems, key=lambda mem: not mem.bot)
    admins = len([
      mem for mem in ctx.guild.members
      if mem.guild_permissions.administrator
    ])
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) [{mem.mention}] - <t:{int(mem.created_at.timestamp())}:D>"
      for no, mem in enumerate(mems, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Admins in {guild.name} - {admins}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="invoice", help="List of all users in a voice channel", aliases=["invc"], with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def listusers(self, ctx):
    if not ctx.author.voice:
      return await ctx.send("You are not connected to a voice channel")
    members = ctx.author.voice.channel.members
    entries = [
      f"`[{n}]` | {member} [{member.mention}]"
      for n, member in enumerate(members, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      description="",
      title=f"Voice List of {ctx.author.voice.channel.name} - {len(members)}",
      color=self.color),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="moderators", help= "List of All Admins of a server", aliases=["mods"], with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_mod(self, ctx):
    membs = ([
      mem for mem in ctx.guild.members
      if mem.guild_permissions.ban_members
      or mem.guild_permissions.kick_members
    ])
    mems = filter(lambda member: member.bot, ctx.guild.members)
    mems = sorted(membs, key=lambda mem: mem.joined_at)
    admins = len([
      mem for mem in ctx.guild.members
      if mem.guild_permissions.ban_members
      or mem.guild_permissions.kick_members
    ])
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) [{mem.mention}] - <t:{int(mem.created_at.timestamp())}:D>"
      for no, mem in enumerate(mems, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Mods in {guild.name} - {admins}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="early", aliases=["sup"], help= "List of members that have Early Supporter badge.", with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_early(self, ctx):
    mems = ([
      memb for memb in ctx.guild.members
      if memb.public_flags.early_supporter
    ])
    mems = sorted(mems, key=lambda memb: memb.created_at)
    admins = len([
      memb for memb in ctx.guild.members
      if memb.public_flags.early_supporter
    ])
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id})  [{mem.mention}] - <t:{int(mem.created_at.timestamp())}:D>"
      for no, mem in enumerate(mems, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Early Supporters Id's in {guild.name} - {admins}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="activedeveloper", help= "List of members that have Active Developer badge.",
                   aliases=["activedev"],
                   with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_activedeveloper(self, ctx):
    mems = ([
      memb for memb in ctx.guild.members
      if memb.public_flags.active_developer
    ])
    mems = sorted(mems, key=lambda memb: memb.created_at)
    admins = len([
      memb for memb in ctx.guild.members
      if memb.public_flags.active_developer
    ])
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) [{mem.mention}] - <t:{int(mem.created_at.timestamp())}:D>"
      for no, mem in enumerate(mems, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Active Developer Id's in {guild.name} - {admins}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="createdat", help= "List of Account Creation Date of all Users", with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_cpos(self, ctx):
    mems = ([memb for memb in ctx.guild.members])
    mems = sorted(mems, key=lambda memb: memb.created_at)
    admins = len([memb for memb in ctx.guild.members])
    guild = ctx.guild
    entries = [
      f"`[{no}]` | [{mem}](https://discord.com/users/{mem.id}) - <t:{int(mem.created_at.timestamp())}:D>"
      for no, mem in enumerate(mems, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Creation every id in {guild.name} - {admins}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()

  @__list_.command(name="joinedat", help= "List of Guild Joined date of all Users", with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def list_joinpos(self, ctx):
    mems = ([memb for memb in ctx.guild.members])
    mems = sorted(mems, key=lambda memb: memb.joined_at)
    admins = len([memb for memb in ctx.guild.members])
    guild = ctx.guild
    entries = [
      f"`#{no}.` [{mem}](https://discord.com/users/{mem.id}) Joined At - <t:{int(mem.joined_at.timestamp())}:D>"
      for no, mem in enumerate(mems, start=1)
    ]
    paginator = Paginator(source=DescriptionEmbedPaginator(
      entries=entries,
      title=f"Join Position of every user in {guild.name} - {admins}",
      description="",
      per_page=10),
                          ctx=ctx)
    await paginator.paginate()




  @commands.command(name="joined-at",
                    help="Shows when a user joined",
                    usage="joined-at [user]",
                    with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def joined_at(self, ctx):
    joined = ctx.author.joined_at.strftime("%a, %d %b %Y %I:%M %p")
    await ctx.send(embed=discord.Embed(
      title="joined-at", description="**`%s`**" % (joined), color=self.color))

  @commands.command(name="github", usage="github [search]")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def github(self, ctx, *, search_query):
    json = requests.get(
      f"https://api.github.com/search/repositories?q={search_query}").json()

    if json["total_count"] == 0:
      await ctx.send(f"No matching repositories found with the name: {search_query}")
    else:
      await ctx.send(
        f"Found result for '{search_query}':\n{json['items'][0]['html_url']}")

  @commands.hybrid_command(name="vcinfo",
                           description="View information about a voice channel.",
                           help="View information about a voice channel.", 
                           usage="<VoiceChannel>",
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def vcinfo(self, ctx, channel: discord.VoiceChannel = None):
    if channel is None:
      await ctx.reply(f"{cross} Please provide a valid voice channel.")
      return
    embed = discord.Embed(title=f"Voice Channel Info for: {channel.name}", color=self.color)
    embed.add_field(name="ID", value=channel.id, inline=True)
    embed.add_field(name="Members", value=len(channel.members), inline=True)
    embed.add_field(name="Bitrate", value=f"{channel.bitrate/1000} kbps", inline=True)
    embed.add_field(name="Created At", value=channel.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
    embed.add_field(name="Region", value=channel.rtc_region, inline=True)

    if channel.user_limit:
      embed.add_field(name="User Limit", value=channel.user_limit, inline=True)

    if channel.overwrites:
      overwrites = []
      for role, permissions in channel.overwrites.items():
        overwrites.append(f"**{role}**: {permissions}")
      embed.add_field(name="Overwrites", value="\n".join(overwrites), inline=False)

    view = View()
    view.add_item(Button(label="Join", style=discord.ButtonStyle.green, url=f"https://discord.com/channels/{ctx.guild.id}/{channel.id}"))
    view.add_item(Button(label="Invite", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/invite"))

    await ctx.send(embed=embed, view=view)


  @commands.hybrid_command(name="channelinfo",
     aliases=['cinfo', 'ci'],
     description='Get information about a channel.',
     help='Get information about a channel.',
     usage="<Channel>",
     with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def channelinfo(self, ctx, channel: discord.TextChannel = None):
    if channel is None:
      channel = ctx.channel
      
    embed = discord.Embed(title=f"Channel Info - {channel.name}",
    color=0x000000)
    embed.add_field(name="ID", value=channel.id, inline=False)
    embed.add_field(name="Created At", value=channel.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=False)
    embed.add_field(name="Topic", value=channel.topic if channel.topic else "None", inline=False)
    embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay} seconds" if channel.slowmode_delay else "None", inline=False)
    embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1205345282158501899.png")
    embed.set_footer(text=f"Requested By {ctx.author}",
                       icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
      
      
    view = OverwritesView(channel, ctx.author.id)
    view.add_item(Button(label="Redirect Channel", style=discord.ButtonStyle.green, url=f"https://discord.com/channels/{ctx.guild.id}/{channel.id}"))
      
    await ctx.send(embed=embed, view=view)


  @commands.command(name="ping", aliases=['latency'],
                      help="Checks the bot latency.",
                      with_app_command=True)
  @ignore_check()
  @blacklist_check()
  @commands.cooldown(1, 2, commands.BucketType.user)
  async def ping(self, ctx):
    msg = await ctx.reply(f"🏓 Pong **{round(self.bot.latency * 1000, 2)}ms**")
    
    db_latency = None
    try:
      async with aiosqlite.connect("db/afk.db") as db:
        start_time = time.perf_counter()
        await db.execute("SELECT 1")
        end_time = time.perf_counter()
        db_latency = (end_time - start_time) * 1000
        db_latency = round(db_latency, 2)
    except Exception as e:
      print(f"Error measuring database latency: {e}")
      db_latency = "N/A"

    await msg.edit(content=f"🏓 Pong **{round(self.bot.latency * 1000, 2)}ms** | Database: **{db_latency}ms**")



  
  @commands.command(name="permissions", aliases= ["perms"],
                           help="Check and list the key permissions of a specific user",
                           usage="perms <user>",
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def keyperms(self, ctx, member: discord.Member):
    key_permissions = []

    if member.guild_permissions.create_instant_invite:
      key_permissions.append("Create Instant Invite")
    if member.guild_permissions.kick_members:
      key_permissions.append("Kick Members")
    if member.guild_permissions.ban_members:
      key_permissions.append("Ban Members")
    if member.guild_permissions.administrator:
      key_permissions.append("Administrator")
    if member.guild_permissions.manage_channels:
      key_permissions.append("Manage Channels")
    if member.guild_permissions.manage_messages:
      key_permissions.append("Manage Messages")
    if member.guild_permissions.mention_everyone:
      key_permissions.append("Mention Everyone")
    if member.guild_permissions.manage_nicknames:
      key_permissions.append("Manage Nicknames")
    if member.guild_permissions.manage_roles:
      key_permissions.append("Manage Roles")
    if member.guild_permissions.manage_webhooks:
      key_permissions.append("Manage Webhooks")
    if member.guild_permissions.manage_emojis:
      key_permissions.append("Manage Emojis")
    if member.guild_permissions.manage_guild:
      key_permissions.append("Manage Server")
    if member.guild_permissions.manage_permissions:
      key_permissions.append("Manage Permissions")
    if member.guild_permissions.manage_threads:
      key_permissions.append("Manage Threads")
    if member.guild_permissions.moderate_members:
      key_permissions.append("Moderate Members")
    if member.guild_permissions.move_members:
      key_permissions.append("Move Members")
    if member.guild_permissions.mute_members:
      key_permissions.append("Mute Members (VC)")
    if member.guild_permissions.deafen_members:
      key_permissions.append("Deafen Members")
    if member.guild_permissions.priority_speaker:
      key_permissions.append("Priority Speaker")
    if member.guild_permissions.stream:
      key_permissions.append("Stream")
    
    
    

    permissions_list = ", ".join(key_permissions) if key_permissions else "None"

    embed = discord.Embed(title=f"Key Permissions of {member}",
                          color=0x000000)
    embed.add_field(name="__**Key Permissions**__", value=permissions_list, inline=False)

    await ctx.reply(embed=embed)

  




  @commands.hybrid_command(name="report",
                           aliases=["bug"],
                           usage='Report <bug>',
                           description='Report a bug to the Development team.',
                           help='Report a bug to the Development team.',
                           with_app_command=True)
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 30, commands.BucketType.channel)
  async def report(self, ctx, *, bug):
    channel = self.bot.get_channel(1271825687438954557)
    embed = discord.Embed(title='Bug Reported',
                          description=bug,
                          color=0x000000)
    embed.add_field(name='Reported By',
                    value=f'{ctx.author.name}',
                    inline=True)
    embed.add_field(name="Server", value=ctx.guild.name, inline=False)
    embed.add_field(name="Channel", value=ctx.channel.name, inline=False)
    await channel.send(embed=embed)
    confirm_embed = discord.Embed(title="<a:success:1204107381575917668> Bug Reported",
      description="Thank you for reporting the bug. We will look into it.",
      color=0x000000)
    await ctx.reply(embed=confirm_embed)

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out support or DM me.
"""