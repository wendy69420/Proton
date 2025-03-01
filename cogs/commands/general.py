import asyncio
import discord
from discord.ext import commands, tasks
from discord.utils import get
import datetime
import random
import requests
import aiohttp
import re
from discord.ext.commands.errors import BadArgument
from discord.ext.commands import Cog
from discord.colour import Color
import hashlib
from utils.Tools import *
from traceback import format_exception
import discord
from discord.ext import commands
import datetime
from discord import ButtonStyle
from discord.ui import Button, View
import psutil
import time
from datetime import datetime, timezone, timedelta
import sqlite3
from typing import *
import string
#from cogs.commands.moderation import do_removal

lawda = [
  '8', '3821', '23', '21', '313', '43', '29', '76', '11', '9',
  '44', '470', '318' , '26', '69'
]



class AvatarView(View):
  def __init__(self, user, member, author_id, banner_url):
    super().__init__()
    self.user = user
    self.member = member
    self.author_id = author_id
    self.banner_url = banner_url

    if self.user.avatar.is_animated():
      self.add_item(Button(label='GIF', url=self.user.avatar.with_format('gif').url, style=discord.ButtonStyle.link))
    self.add_item(Button(label='PNG', url=self.user.avatar.with_format('png').url, style=discord.ButtonStyle.link))
    self.add_item(Button(label='JPEG', url=self.user.avatar.with_format('jpg').url, style=discord.ButtonStyle.link))
    self.add_item(Button(label='WEBP', url=self.user.avatar.with_format('webp').url, style=discord.ButtonStyle.link))

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if interaction.user.id != self.author_id:
      await interaction.response.send_message(
        "Uh oh! That message doesn't belong to you. You must run this command to interact with it.",
        ephemeral=True
      )
      return False
    return True

  @discord.ui.button(label='Server Avatar', style=discord.ButtonStyle.success, custom_id='server_avatar_button')
  async def server_avatar(self, interaction: discord.Interaction, button: Button):
    if not self.member.guild_avatar:
      await interaction.response.send_message(
        "This user doesn't have a different guild avatar.",
        ephemeral=True
      )
    else:
      embed = interaction.message.embeds[0]
      embed.set_image(url=self.member.guild_avatar.url)
      await interaction.response.edit_message(embed=embed)

  @discord.ui.button(label='User Banner', style=discord.ButtonStyle.success, custom_id='banner_button')
  async def banner(self, interaction: discord.Interaction, button: Button):
    if not self.banner_url:
      await interaction.response.send_message(
        "This user doesn't have a banner.",
        ephemeral=True
      )
    else:
      embed = interaction.message.embeds[0]
      embed.set_image(url=self.banner_url)
      await interaction.response.edit_message(embed=embed)





class General(commands.Cog):

  def __init__(self, bot, *args, **kwargs):
    self.bot = bot

    self.aiohttp = aiohttp.ClientSession()
    self._URL_REGEX = r'(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])'
    self.color = 0x000000


  @commands.hybrid_command(
    usage="Avatar <member>",
    name='avatar',
    aliases=['av'],
    help="Get User avater/Guild avatar & Banner of a user."
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def _user(self, ctx, member: Optional[Union[discord.Member, discord.User]] = None):
    try:
      if member is None:
        member = ctx.author
      user = await self.bot.fetch_user(member.id)

      banner_url = user.banner.url if user.banner else None

      description = f"[`PNG`]({user.avatar.with_format('png').url}) | [`JPG`]({user.avatar.with_format('jpg').url}) | [`WEBP`]({user.avatar.with_format('webp').url})"
      if user.avatar.is_animated():
        description += f" | [`GIF`]({user.avatar.with_format('gif').url})"
      if banner_url:
        description += f" | [`Banner`]({banner_url})"

      embed = discord.Embed(
        color=self.color,
        description=description
      )
      embed.set_author(name=f"{member}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
      embed.set_image(url=user.avatar.url)
      embed.set_footer(text=f"Requested By {ctx.author}",
                       icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

      view = AvatarView(user, member, ctx.author.id, banner_url)
      await ctx.send(embed=embed, view=view)
    except Exception as e:
      print(f"Error: {e}")
      
  @commands.hybrid_command(
    name="servericon",
    help="Get the server icon",
    usage="Servericon"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def servericon(self, ctx: commands.Context):
    server = ctx.guild
    if server.icon is None:
      await ctx.reply("This server does not have an icon.")
      return

    webp = server.icon.replace(format='webp')
    jpg = server.icon.replace(format='jpg')
    png = server.icon.replace(format='png')

    description = f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"
    if server.icon.is_animated():
      gif = server.icon.replace(format='gif')
      description += f" | [`GIF`]({gif})"

    avemb = discord.Embed(
      color=self.color,
      title=f"{server}'s Icon",
      description=description
    )
    avemb.set_image(url=server.icon.url)
    avemb.set_footer(
      text=f"Requested By {ctx.author}",
      icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )

    view = discord.ui.View()
    view.add_item(Button(label="Download Icon", url=server.icon.url, style=ButtonStyle.link))

    await ctx.send(embed=avemb, view=view)



  @commands.hybrid_command(name="membercount",
                           help="Get total member count of the server",
                           usage="membercount",
                           aliases=["mc"])
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 2, commands.BucketType.user)
  async def membercount(self, ctx: commands.Context):
        total_members = len(ctx.guild.members)
        total_humans = len([member for member in ctx.guild.members if not member.bot])
        total_bots = len([member for member in ctx.guild.members if member.bot])

        online = len([member for member in ctx.guild.members if member.status == discord.Status.online])
        offline = len([member for member in ctx.guild.members if member.status == discord.Status.offline])
        idle = len([member for member in ctx.guild.members if member.status == discord.Status.idle])
        dnd = len([member for member in ctx.guild.members if member.status == discord.Status.do_not_disturb])



        embed = discord.Embed(title="Member Statistics",
                              color=0x000000)
        embed.add_field(name="__Count Stats:__",
                        value=f"<:olympus_users:1226064812157571163> Total Members: {total_members}\n<:olympus_friend:1228229690376982549> Total Humans: {total_humans}\n<:olympus_bot:1227873668466741320> Total Bots: {total_bots}",
                        inline=False)

        embed.add_field(name="__Presence Stats:__", value=f"<:olympus_online:1228271960233082901> Online: {online}\n<:olympus_dnd:1228272112368750613> Dnd: {dnd}\n<:olympus_idle:1228272291473784852> Idle: {idle}\n<:olympus_offline:1228272024829431873> Offline: {offline}", inline=False)

        await ctx.send(embed=embed)

  @commands.hybrid_command(name="poll", usage="Poll <message>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def poll(self, ctx: commands.Context, *, message):
    author = ctx.author
    emp = discord.Embed(title=f"**Poll raised by {author}!**",
                        description=f"{message}",
                        color=self.color)
    msg = await ctx.send(embed=emp)
    await msg.add_reaction("<:YES:1212448034437210142>")
    await msg.add_reaction("<:No:1212448060135841852>")

  
  @commands.command(name="hack",
    help="hack someone's discord account",
    usage="Hack <member>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def hack(self, ctx: commands.Context, member: discord.Member):
    stringi = member.name
    min_length = 2
    max_length = 12
    length = random.randint(min_length, max_length)
    stringg = member.name
    remaining_length = length - len(stringg)
    all_chars = string.ascii_letters + string.digits + string.punctuation
    random_chars = random.choices(all_chars, k=remaining_length)

    password = stringg + ''.join(random_chars)
    
    lund = await ctx.send(f"Processing to Hack {member.mention}...")
    await asyncio.sleep(2)
    random_pass = random.choice(lawda)
    
    random_pass2 = ''.join(random.choices(string.ascii_letters + string.digits, k=3))
    embed = discord.Embed(
  title=f"**Hacked {member.display_name}!**",
  description=(
  f"User - {member.mention}\n"
  f"E-Mail - {''.join(letter for letter in stringi if letter.isalnum())}{random_pass}@gmail.com\n"
  f"Account Password - {member.name}@{random_pass2}"
  ),
  color=0x000000
  )
    embed.set_footer(
  text=f"Hacked By {ctx.author}",
  icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
  )
    await ctx.send(embed=embed)
    await lund.delete()


  @commands.command(name="token", usage="Token <member>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 2, commands.BucketType.user)
  async def token(self, ctx: commands.Context, user: discord.Member = None):
    list = [
      "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
      "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "_"
      'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
      'ñ', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0',
      '1', '2', '3', '4', '5', '6', '7', '8', '9'
    ]
    token = random.choices(list, k=59)
    if user is None:
      user = ctx.author
      await ctx.send(user.mention + "'s token: " + ''.join(token))
    else:
      await ctx.send(user.mention + "'s token: " + "".join(token))

  @commands.command(name="users", help="checks total users of Olympus.")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def users(self, ctx: commands.Context):
    users = sum(g.member_count for g in self.bot.guilds
                if g.member_count != None)
    guilds = len(self.bot.guilds)
    embed = discord.Embed(
      title=f"**<:olympus_users:1226064812157571163> Olympus Users**",
      description=f"❯ Total of __**{users}**__ Users in **{guilds}** Guilds",
      color=self.color)
    await ctx.send(embed=embed)


  @commands.command(name="wizz", usage="Wizz")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def wizz(self, ctx: commands.Context):
    message6 = await ctx.send(
      f"`Wizzing {ctx.guild.name}, will take 22 seconds to complete`")
    message7 = await ctx.send(f"Changing all guild settings...")
    message5 = await ctx.send(f"Deleting **{len(ctx.guild.roles)}** Roles...")
    await asyncio.sleep(1)
    message4 = await ctx.send(
      f"Deleting **{len(ctx.guild.channels)}** Channels...")
    await asyncio.sleep(1)
    message3 = await ctx.send(f"Deleting Webhooks...")
    message2 = await ctx.send(f"Deleting emojis")
    await asyncio.sleep(1)
    message1 = await ctx.send(f"Installing Ban Wave..")
    await asyncio.sleep(1)
    await message6.delete()
    await message7.delete()
    await message5.delete()
    await message4.delete()
    await message3.delete()
    await message2.delete()
    await message1.delete()
    embed = discord.Embed(
      title=f"{self.bot.user.name}",
      description=f"**<a:olympus_WarnFlash:1272569018183843874> Successfully Wizzed {ctx.guild.name}**",
      color=self.color,
      timestamp=ctx.message.created_at)
    embed.set_footer(
      text=f"Wizzed By {ctx.author}",
      icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
      )
    await ctx.send(embed=embed)


  @commands.hybrid_command(
    name="urban",
    description="Searches for specified phrase on urbandictionary",
    help="Get meaning of specified phrase",
    usage="Urban <phrase>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def urban(self, ctx: commands.Context, *, phrase):
    async with self.aiohttp.get(
        "http://api.urbandictionary.com/v0/define?term={}".format(
          phrase)) as urb:
      urban = await urb.json()
      try:
        embed = discord.Embed(title=f"Meaning of \"{phrase}\"", color=self.color)
        embed.add_field(name="__Definition:__",
                        value=urban['list'][0]['definition'].replace(
                          '[', '').replace(']', ''))
        embed.add_field(name="__Example:__",
                        value=urban['list'][0]['example'].replace('[',
                                                                  '').replace(
                                                                    ']', ''))

        embed.add_field(name="__Author:__",
                        value=urban['list'][0]['author'].replace('[',
                                                                  '').replace(
                                                                    ']', ''))

        embed.add_field(name="__Written On:__",
                        value=urban['list'][0]['written_on'].replace('[',
                                                                  '').replace(
                                                                    ']', ''))
        embed.set_footer(
      text=f"Requested By {ctx.author}",
      icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
      )
        temp = await ctx.reply(embed=embed, mention_author=True)
        await asyncio.sleep(45)
        await temp.delete()
        await ctx.message.delete()
      except:
        pass

  @commands.command(name="rickroll",
                           help="Detects if provided url is a rick-roll",
                           usage="Rickroll <url>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def rickroll(self, ctx: commands.Context, *, url: str):
    if not re.match(self._URL_REGEX, url):
      raise BadArgument("Invalid URL")

    phrases = [
      "rickroll", "rick roll", "rick astley", "never gonna give you up"
    ]
    source = str(await (await self.aiohttp.get(
      url, allow_redirects=True)).content.read()).lower()
    rickRoll = bool((re.findall('|'.join(phrases), source,
                                re.MULTILINE | re.IGNORECASE)))
    await ctx.reply(embed=discord.Embed(
      title="Rick Roll {} in webpage".format(
        "was found" if rickRoll is True else "was not found"),
      color=Color.red() if rickRoll is True else Color.green(),
    ),
                    mention_author=True)

  @commands.command(name="hash",
                           help="Hashes provided text with provided algorithm")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def hash(self, ctx: commands.Context, algorithm: str, *, message):
    algos: dict[str, str] = {
      "md5": hashlib.md5(bytes(message.encode("utf-8"))).hexdigest(),
      "sha1": hashlib.sha1(bytes(message.encode("utf-8"))).hexdigest(),
      "sha224": hashlib.sha224(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_224": hashlib.sha3_224(bytes(message.encode("utf-8"))).hexdigest(),
      "sha256": hashlib.sha256(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_256": hashlib.sha3_256(bytes(message.encode("utf-8"))).hexdigest(),
      "sha384": hashlib.sha384(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_384": hashlib.sha3_384(bytes(message.encode("utf-8"))).hexdigest(),
      "sha512": hashlib.sha512(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_512": hashlib.sha3_512(bytes(message.encode("utf-8"))).hexdigest(),
      "blake2b": hashlib.blake2b(bytes(message.encode("utf-8"))).hexdigest(),
      "blake2s": hashlib.blake2s(bytes(message.encode("utf-8"))).hexdigest()
    }
    embed = discord.Embed(color=0x000000,
                          title="Hashed \"{}\"".format(message))
    if algorithm.lower() not in list(algos.keys()):
      for algo in list(algos.keys()):
        hashValue = algos[algo]
        embed.add_field(name=algo, value="```{}```".format(hashValue))
    else:
      embed.add_field(name=algorithm,
                      value="```{}```".format(algos[algorithm.lower()]),
                      inline=False)
    await ctx.reply(embed=embed, mention_author=True)

  
  @commands.command(name="invite",
                           aliases=['invite-bot'],
                           description="Get Support & Bot invite link!")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def invite(self, ctx: commands.Context):
    embed = discord.Embed(title="Olympus Invite & Support!",
      description=
      f"> <:created:1272499720153202688> **[Olympus - Invite Bot](https://discord.com/oauth2/authorize?client_id=1144179659735572640&permissions=2113268958&scope=bot)**\n> <:created:1272499720153202688> **[Olympus - Support](https://discord.gg/odx)**",
      color=0x000000)

    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1267667804048588992.png")
    embed.set_footer(text=f"Requested by {ctx.author.name}",
                     icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    invite = Button(
      label='Invite',
      style=discord.ButtonStyle.link,
      url=
      'https://discord.com/oauth2/authorize?client_id=1144179659735572640&permissions=2113268958&scope=bot'
    )
    support = Button(label='Support',
                    style=discord.ButtonStyle.link,
                    url=f'https://discord.gg/odx')
    vote = Button(label='Vote',
                      style=discord.ButtonStyle.link,
                      url='https://top.gg/bot/1144179659735572640/vote')
    view = View()
    view.add_item(invite)
    view.add_item(support)
    view.add_item(vote)
    await ctx.send(embed=embed, view=view)

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out Community or DM me.
"""