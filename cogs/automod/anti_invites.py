import discord
from discord.ext import commands
import aiosqlite
import asyncio
from datetime import timedelta
import re

class AntiInvite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite_pattern = re.compile(r'(https?://)?(www\.)?(discord\.gg|discordapp\.com/invite|discord\.com/invite)/\S+')

    async def is_automod_enabled(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT enabled FROM automod WHERE guild_id = ?", (guild_id,))
            result = await cursor.fetchone()
            return result is not None and result[0] == 1

    async def is_anti_invites_enabled(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT punishment FROM automod_punishments WHERE guild_id = ? AND event = 'Anti invites'", (guild_id,))
            result = await cursor.fetchone()
            return result is not None

    async def get_ignored_channels(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT id FROM automod_ignored WHERE guild_id = ? AND type = 'channel'", (guild_id,))
            return [row[0] for row in await cursor.fetchall()]

    async def get_ignored_roles(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT id FROM automod_ignored WHERE guild_id = ? AND type = 'role'", (guild_id,))
            return [row[0] for row in await cursor.fetchall()]

    async def get_punishment(self, guild_id):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT punishment FROM automod_punishments WHERE guild_id = ? AND event = 'Anti invites'", (guild_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    async def log_action(self, guild, user, channel, action, reason):
        async with aiosqlite.connect("db/automod.db") as db:
            cursor = await db.execute("SELECT log_channel FROM automod_logging WHERE guild_id = ?", (guild.id,))
            log_channel_id = await cursor.fetchone()

        if log_channel_id and log_channel_id[0]:
            log_channel = guild.get_channel(log_channel_id[0])
            if log_channel:
                embed = discord.Embed(title="Automod Log: Anti-Invite", color=0xff0000)
                embed.add_field(name="User", value=user.mention, inline=False)
                embed.add_field(name="Action", value=action, inline=False)
                embed.add_field(name="Channel", value=channel.mention, inline=False)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.set_footer(text=f"User ID: {user.id}")
                avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
                embed.set_thumbnail(url=avatar_url)
                embed.timestamp=discord.utils.utcnow()
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        guild = message.guild
        user = message.author
        channel = message.channel
        guild_id = guild.id

        if not await self.is_automod_enabled(guild_id) or not await self.is_anti_invites_enabled(guild_id):
            return

        if user == guild.owner or user == self.bot.user:
            return

        ignored_channels = await self.get_ignored_channels(guild_id)
        if channel.id in ignored_channels:
            return

        ignored_roles = await self.get_ignored_roles(guild_id)
        if any(role.id in ignored_roles for role in user.roles):
            return

        if self.invite_pattern.search(message.content):
            invite_link = self.invite_pattern.search(message.content).group(0)
            invite_code = invite_link.split('/')[-1]

            try:
                invite = await guild.invites()
                if any(invite.code == invite_code for invite in invite):
                    return  

                punishment = await self.get_punishment(guild_id)
                action_taken = None
                reason = "Posted an invite link"

                try:
                    if punishment == "Mute":
                        timeout_duration = discord.utils.utcnow() + timedelta(minutes=12)
                        await user.edit(timed_out_until=timeout_duration, reason="Posted an invite link")
                        action_taken = "Muted for 12 minutes"
                    elif punishment == "Kick":
                        await user.kick(reason="Posted an invite link")
                        action_taken = "Kicked"
                    elif punishment == "Ban":
                        await user.ban(reason="Posted an invite link")
                        action_taken = "Banned"
                        
                    await message.delete()

                    simple_embed = discord.Embed(title="Automod Anti-Invite", color=0xff0000)
                    simple_embed.description = f"<:olympus_tick:1227866641027698792> | {user.mention} has been successfully **{action_taken}** for **posting an invite link.**"
                    simple_embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1294125691587006525.png")
                    simple_embed.set_footer(text="Use the “automod logging” command to get automod logs if it is not enabled.", icon_url=self.bot.user.avatar.url)
                    await channel.send(embed=simple_embed, delete_after=30)

                    await self.log_action(guild, user, channel, action_taken, reason)

                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
                except Exception:
                    pass

            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_rate_limit(self, message):
        await asyncio.sleep(10)

