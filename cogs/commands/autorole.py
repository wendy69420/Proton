from __future__ import annotations
import discord
import aiosqlite
import logging
from discord.ext import commands
from typing import List, Dict
from utils.Tools import *

logging.basicConfig(
    level=logging.INFO,
    format="\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)

DATABASE_PATH = 'db/autorole.db'

class BasicView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id and interaction.user.id not in [246469891761111051]:
            await interaction.response.send_message("Uh oh! That message doesn't belong to you.\nYou must run this command to interact with it.", ephemeral=True)
            return False
        return True


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.create_table())
        self.color = 0x000000

    async def create_table(self):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS autorole (
                guild_id INTEGER PRIMARY KEY,
                bots TEXT NOT NULL,
                humans TEXT NOT NULL
            )
            """)
            await db.commit()

    async def get_autorole(self, guild_id: int) -> Dict[str, List[int]]:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT bots, humans FROM autorole WHERE guild_id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    bots, humans = row
                    
                    bots = [int(role_id) for role_id in bots.replace('[', '').replace(']', '').replace(' ', '').split(',') if role_id]
                    humans = [int(role_id) for role_id in humans.replace('[', '').replace(']', '').replace(' ', '').split(',') if role_id]
                      
                    return {"bots": bots, "humans": humans}
                else:
                    return {"bots": [], "humans": []}

    

    async def update_autorole(self, guild_id: int, data: Dict[str, List[int]]):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            bots = ','.join(map(str, data['bots']))
            humans = ','.join(map(str, data['humans']))
            
            await db.execute("INSERT OR REPLACE INTO autorole (guild_id, bots, humans) VALUES (?, ?, ?)",
                             (guild_id, bots, humans))
            await db.commit()


        
                
    @commands.group(name="autorole", invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)
            

    @_autorole.command(name="config", help="Shows the current autorole configuration")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _ar_config(self, ctx):
        
        data = await self.get_autorole(ctx.guild.id)
        if data:
            fetched_humans = [ctx.guild.get_role(role_id) for role_id in data["humans"] if ctx.guild.get_role(role_id)]
            fetched_bots = [ctx.guild.get_role(role_id) for role_id in data["bots"] if ctx.guild.get_role(role_id)]

            hums = "\n".join(role.mention for role in fetched_humans) or "None"
            bos = "\n".join(role.mention for role in fetched_bots) or "None"

            emb = discord.Embed(color=self.color, title=f"Autorole Configuration for {ctx.guild.name}")
            emb.add_field(name="<:olympus_friend:1228229690376982549> __Humans__", value=hums, inline=False)
            emb.add_field(name="<:olympus_bot:1227873668466741320> __Bots__", value=bos, inline=False)

            await ctx.send(embed=emb)
        else:
            emb = discord.Embed(color=self.color, description="No autorole configuration found in this Guild.")
            await ctx.reply(embed=emb)



    @_autorole.group(name="reset", help="Clear autorole config in the Guild")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _autorole_reset(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole_reset.command(name="humans", help="Clear autorole configuration for humans")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans_reset(self, ctx):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT humans FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()

        if data and data[0]:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("UPDATE autorole SET humans = ? WHERE guild_id = ?", ('[]', ctx.guild.id))
                await db.commit()
            embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                  description="Cleared all human autoroles in this Guild.",
                                  color=self.color)
        else:
            embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                                  description="No Autoroles set for humans in this Guild.",
                                  color=self.color)

        await ctx.reply(embed=embed)

    @_autorole_reset.command(name="bots", help="Clear autorole configuration for bots")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots_reset(self, ctx):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT bots FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()

        if data and data[0]:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("UPDATE autorole SET bots = ? WHERE guild_id = ?", ('[]', ctx.guild.id))
                await db.commit()
            embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                  description="Cleared all bot autoroles in this Guild.",
                                  color=self.color)
        else:
            embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                                  description="No Autoroles set for Bots in this Guild.",
                                  color=self.color)

        await ctx.reply(embed=embed)

    @_autorole_reset.command(name="all", help="Clear all autorole configuration in the Guild")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_reset_all(self, ctx):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT humans, bots FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()

        if data and (data[0] or data[1]):
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("UPDATE autorole SET humans = ?, bots = ? WHERE guild_id = ?", ('[]', '[]', ctx.guild.id))
                await db.commit()
            embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                  description="Cleared all autoroles in this Gudild.",
                                  color=self.color)
        else:
            embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                  description="No Autoroles set in this Guild.",
                  color=self.color)

        await ctx.reply(embed=embed)

    @_autorole.group(name="humans", help="Setup autoroles for human")
    @blacklist_check()
    @ignore_check()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole_humans.command(name="add", help="Add role to list of human Autoroles.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans_add(self, ctx, *, role: discord.Role):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT humans FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()
        
        if data:
            humans = eval(data[0])
            if role.id in humans:
                embed = discord.Embed(title="<:olympus_notify:1227866804630720565> Access Denied",
                                    description=f"{role.mention} is already in human autoroles.",
                                    color=self.color)
            elif len(humans) >= 10:
                embed = discord.Embed(title="<:olympus_notify:1227866804630720565> Access Denied",
                                    description="You can only add upto 10 human autoroles.",
                                    color=self.color)
            else:
                humans.append(role.id)
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE autorole SET humans = ? WHERE guild_id = ?", (str(humans), ctx.guild.id))
                    await db.commit()
                embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                    description=f"{role.mention} has been added to human autoroles.",
                                    color=self.color)
        else:
            humans = [role.id]
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("INSERT INTO autorole (guild_id, humans, bots) VALUES (?, ?, ?)", (ctx.guild.id, str(humans), '[]'))
                await db.commit()
            embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                  description=f"{role.mention} has been added to human autoroles.",
                                  color=self.color)

        await ctx.reply(embed=embed)

    @_autorole_humans.command(name="remove", help="Remove a role from human Autoroles.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_humans_remove(self, ctx, *, role: discord.Role):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT humans FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()

        if data:
            humans = eval(data[0])
            if role.id not in humans:
                embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                                    description=f"{role.mention} is not in human autoroles.",
                                    color=self.color)
            else:
                humans.remove(role.id)
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE autorole SET humans = ? WHERE guild_id = ?", (str(humans), ctx.guild.id))
                    await db.commit()
                embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                    description=f"{role.mention} has been removed from human autoroles.",
                                    color=self.color)
        else:
            embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                                  description=f"No Autoroles set in this guild for humans.",
                                  color=self.color)

        await ctx.reply(embed=embed)

    @_autorole.group(name="bots", help="Setup autoroles for bots")
    @blacklist_check()
    @ignore_check()
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_autorole_bots.command(name="add", help="Add role to bot Autoroles.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots_add(self, ctx, *, role: discord.Role):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT bots FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()
        
        if data:
            bots = eval(data[0])
            if role.id in bots:
                embed = discord.Embed(title="<:olympus_notify:1227866804630720565> Access Denied",
                                      description=f"{role.mention} is already in bot autoroles.",
                                      color=self.color)
            elif len(bots) >= 10:
                embed = discord.Embed(title="<:olympus_notify:1227866804630720565> Access Denied",
                                    description="You can only add upto 10 bot autoroles",
                                    color=self.color)
            else:
                bots.append(role.id)
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE autorole SET bots = ? WHERE guild_id = ?", (str(bots), ctx.guild.id))
                    await db.commit()
                embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                    description=f"{role.mention} has been added to bot autoroles.",
                                    color=self.color)
        else:
            bots = [role.id]
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("INSERT INTO autorole (guild_id, humans, bots) VALUES (?, ?, ?)", (ctx.guild.id, '[]', str(bots)))
                await db.commit()
            embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                  description=f"{role.mention} has been added to bot autoroles.",
                                color=self.color)

        await ctx.reply(embed=embed)

    @_autorole_bots.command(name="remove", help="Remove a role from bot Autoroles.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _autorole_bots_remove(self, ctx, *, role: discord.Role):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT bots FROM autorole WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
                data = await cursor.fetchone()

        if data:
            bots = eval(data[0])
            if role.id not in bots:
                embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                                      description=f"{role.mention} is not in bot autoroles.",
                                      color=self.color)
            else:
                bots.remove(role.id)
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE autorole SET bots = ? WHERE guild_id = ?", (str(bots), ctx.guild.id))
                    await db.commit()
                embed = discord.Embed(title="<:olympus_tick:1227866641027698792> Success",
                                      description=f"{role.mention} has been removed from bot autoroles.",
                                      color=self.color)
        else:
            embed = discord.Embed(title="<:olympus_cross:1227866668152393789> Error",
                                  description=f"No Autoroles set in this guild for bots.",
                                  color=self.color)

        await ctx.reply(embed=embed)
        

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out support or DM me.
"""