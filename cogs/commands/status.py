import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import os
from utils.Tools import *

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="status", help="Shows the status of the user in detail.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def status(self, ctx, user: discord.User = None):
        user = user or ctx.author
        processing = await ctx.send("<a:loading:1246691973633671268> Loading Status...")
        embed = discord.Embed(title=f"{user.display_name}'s Status", color=0x000000)

        status_emoji = {
            "online": "<:olympus_online:1228271960233082901> Online",
            "idle": "<:olympus_idle:1228272291473784852> Idle",
            "dnd": "<:olympus_dnd:1228272112368750613> Do Not Disturb",
            "offline": "<:olympus_offline:1228272024829431873> Offline"
        }

        member = None
        for guild in self.bot.guilds:
            member = guild.get_member(user.id)
            if member:
                break

        if member:
            status = status_emoji.get(str(member.status), "<:olympus_offline:1228272024829431873> Offline")
            embed.add_field(name="Status:", value=status, inline=False)

            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)

            platform = self.get_platform(member)
            embed.add_field(name="Platform:", value=platform, inline=False)

            custom_status = self.get_custom_status(member)
            if custom_status:
                embed.add_field(name="Custom Status:", value=custom_status, inline=False)

            activity_text = self.get_activity_text(member.activities)
            if activity_text:
                embed.add_field(name="__Activity__:", value=activity_text, inline=False)

            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    song_name = activity.title
                    album_cover_url = str(activity.album_cover_url)

                    album_image_path = 'data/pictures/album_image.png'

                    async with aiohttp.ClientSession() as session:
                        async with session.get(album_cover_url) as resp:
                            if resp.status == 200:
                                album_data = await resp.read()
                                with open(album_image_path, 'wb') as f:
                                    f.write(album_data)

                    card_image_path = self.create_spotify_card(song_name, album_image_path)

                    if os.path.exists(card_image_path):
                        file = discord.File(card_image_path, filename="spotify_card.png")
                        embed.set_image(url="attachment://spotify_card.png")
                    else:
                        await ctx.send("Failed to generate the Spotify card image.")
        else:
            try:
                user = await self.bot.fetch_user(user.id)
                embed.add_field(name="Status:", value="<:olympus_offline:1228272024829431873> Offline", inline=False)
                avatar_url = user.default_avatar.url
                embed.set_thumbnail(url=avatar_url)
            except discord.NotFound:
                await ctx.send("User not found.")
                return

        requester_avatar_url = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=requester_avatar_url)

        await ctx.send(embed=embed, file=file if 'file' in locals() else None)
        await processing.delete()

    def create_spotify_card(self, song_name, album_image_path):
        card_path = 'data/pictures/spotify.png'
        output_path = 'data/pictures/spotify_card_output.png'

        base_img = Image.open(card_path).convert("RGBA")
        draw = ImageDraw.Draw(base_img)

        album_img = Image.open(album_image_path).convert("RGBA")
        album_img = album_img.resize((160, 160))

        mask = Image.new("L", album_img.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 160, 160), fill=255)

        base_img.paste(album_img, (30, 30), mask) 

        font_path = 'utils/arial.ttf'
        font = ImageFont.truetype(font_path, 40)

        truncated_song_name = song_name if len(song_name) <= 60 else song_name[:57] + "..."
        song_name_position = (220, 70) 
        draw.text(song_name_position, truncated_song_name, font=font, fill="white")

        base_img.save(output_path)
        return output_path

    def get_platform(self, member):
        if member.desktop_status != discord.Status.offline:
            return "<:desktop:1295398716446081045> Desktop"
        elif member.mobile_status != discord.Status.offline:
            return "<:mobile:1295398543548219475> Mobile"
        elif member.web_status != discord.Status.offline:
            return "<:icon_browser:1295399187709562941> Browser"
        return "Unknown"

    def get_custom_status(self, member):
        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity):
                status_text = activity.name or ""
                if activity.name == "Custom Status":
                    status_text = "‎ "
                status_emoji = str(activity.emoji) if activity.emoji else ""

                if status_emoji and not status_text:
                    return status_emoji
                elif status_emoji and status_text:
                    return f"{status_emoji} {status_text}"
                elif status_text:
                    return status_text
        return None

    def get_activity_text(self, activities):
        activity_list = []
        for activity in activities:
            if isinstance(activity, discord.Game):
                activity_list.append(f"Playing {activity.name}")
            elif isinstance(activity, discord.Streaming):
                activity_list.append(f"Streaming {activity.name} on **[Twitch]({activity.url})**")
            elif isinstance(activity, discord.Spotify):
                activity_list.append(f"**[Listening to Spotify](https://open.spotify.com/track/{activity.track_id})**")
            elif isinstance(activity, discord.Activity):
                activity_list.append(f"{activity.type.name.capitalize()} {activity.name}")
        return "\n".join(activity_list) if activity_list else None

"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (Olympus Development)
    + for any queries reach out Community or DM me.
"""