import discord
from discord.ext import commands
import aiosqlite
import os
from utils.Tools import *

# Database setup
db_folder = 'db'
db_file = 'anti.db'
db_path = os.path.join(db_folder, db_file)

class Nightmode(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_db())
        self.ricky = ['1070619070468214824', '1087282349395411015', '858642338980954113']
        self.color = 0x000000  

    async def initialize_db(self):
        self.db = await aiosqlite.connect(db_path)
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS Nightmode (
                guildId TEXT,
                roleId TEXT,
                adminPermissions INTEGER
            )
        ''')
        await self.db.commit()

    async def is_extra_owner(self, user, guild):
        async with self.db.execute('''
            SELECT owner_id FROM extraowners WHERE guild_id = ? AND owner_id = ?
        ''', (guild.id, user.id)) as cursor:
            extra_owner = await cursor.fetchone()
        return extra_owner is not None

    @commands.hybrid_group(name="nightmode", aliases=[], help="Manages Nightmode feature", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def nightmode(self, ctx):
        nightmode_embed = discord.Embed(
            title='__**Nightmode**__',
            color=self.color,
            description=(
                'Nightmode swiftly disables dangerous permissions for roles, like stripping `ADMINISTRATION` rights, while preserving original settings for seamless restoration.\n\n**Make sure to keep my ROLE above all roles you want to protect.**'
            )
        )
        nightmode_embed.add_field(
            name="Usage",
            value="<:red_dot:1222796144996777995> `nightmode enable`\n<:red_dot:1222796144996777995> `nightmode disable`",
            inline=False
        )
        nightmode_embed.set_thumbnail(url=self.bot.user.avatar.url)
        await ctx.send(embed=nightmode_embed)

    @nightmode.command(name="enable", help="Enable nightmode")
    @commands.has_permissions(administrator=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def enable_nightmode(self, ctx):
        if ctx.guild.member_count < 50:  
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789> Access Denied",
                color=self.color,
                description='Your Server Doesn\'t Meet My 50 Member Criteria'
            ))

        own = ctx.author.id == ctx.guild.owner_id
        check = await self.is_extra_owner(ctx.author, ctx.guild)
        if not own and not check and ctx.author.id not in self.ricky:
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789> Access Denied",
                color=self.color,
                description='Only Server Owner Or Extraowner Can Run This Command.!'
            ))

        if not own and not (
            ctx.guild.me.top_role.position <= ctx.author.top_role.position
        ) and ctx.author.id not in self.ricky:
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789> Access Denied",
                color=self.color,
                description='Only Server Owner or Extraowner Having **Higher role than me can run this command**'
            ))

        bot_highest_role = ctx.guild.me.top_role
        manageable_roles = [
            role for role in ctx.guild.roles
            if role.position < bot_highest_role.position 
            and role.name != '@everyone' 
            and role.permissions.administrator
            and not role.managed  
        ]

        if not manageable_roles:
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789>  Error",
                color=self.color,
                description='No Roles Found With Admin Permissions'
            ))

        async with self.db.execute('SELECT guildId FROM Nightmode WHERE guildId = ?', (str(ctx.guild.id),)) as cursor:
            if await cursor.fetchone():
                return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789>  Error",
                    color=self.color,
                    description='Nightmode is already enabled.'
                ))

        async with self.db.cursor() as cursor:
            for role in manageable_roles:
                admin_permissions = discord.Permissions(administrator=True)
                if role.permissions.administrator:
                    permissions = role.permissions
                    permissions.administrator = False

                    await role.edit(permissions=permissions, reason='Nightmode ENABLED')

                    await cursor.execute('''
                    INSERT OR REPLACE INTO Nightmode (guildId, roleId, adminPermissions)
                    VALUES (?, ?, ?)
                    ''', (str(ctx.guild.id), str(role.id), int(admin_permissions.value)))
            await self.db.commit()

        await ctx.send(embed=discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
            color=self.color,
            description='Nightmode enabled! Dangerous Permissions Disabled For Manageable Roles.'
        ))

    @nightmode.command(name="disable", help="Disable nightmode")
    @commands.has_permissions(administrator=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def disable_nightmode(self, ctx):
        if ctx.guild.member_count < 50:  
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789> Access Denied",
                color=self.color,
                description='Your Server Doesn\'t Meet My 50 Member Criteria'
            ))

        own = ctx.author.id == ctx.guild.owner_id
        check = await self.is_extra_owner(ctx.author, ctx.guild)
        if not own and not check and ctx.author.id not in self.ricky:
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789> Access Denied",
                color=self.color,
                description='Only Server Owner Or Extraowner Can Run This Command.!'
            ))

        if not own and not (
            ctx.guild.me.top_role.position <= ctx.author.top_role.position
        ) and ctx.author.id not in self.ricky:
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789> Access Denied",
                color=self.color,
                description='Only Server Owner or Extraowner Having **Higher role than me can run this command**'
            ))

        async with self.db.execute('SELECT roleId, adminPermissions FROM Nightmode WHERE guildId = ?', (str(ctx.guild.id),)) as cursor:
            stored_roles = await cursor.fetchall()

        if not stored_roles:
            return await ctx.send(embed=discord.Embed(title="<:olympus_cross:1227866668152393789>  Error",
                color=self.color,
                description='Nightmode is not enabled.'
            ))

        async with self.db.cursor() as cursor:
            for role_id, admin_permissions in stored_roles:
                role = ctx.guild.get_role(int(role_id))
                if role:
                    permissions = discord.Permissions(administrator=bool(admin_permissions))
                    await role.edit(permissions=permissions, reason='Nightmode DISABLED')

                    await cursor.execute('DELETE FROM Nightmode WHERE guildId = ? AND roleId = ?', (str(ctx.guild.id), role_id))
            await self.db.commit()

        await ctx.send(embed=discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
            color=self.color,
            description='Nightmode disabled! Restored Permissions For Manageable Roles.'
        ))

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out Community or DM me.
"""