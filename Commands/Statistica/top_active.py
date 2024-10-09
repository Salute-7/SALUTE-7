import os
import json
import disnake
from utils.base.colors import colors
from disnake.ext import commands
from datetime import datetime, timedelta

bot = commands.InteractionBot(intents=disnake.Intents.all())

def load_config(guild_id):
    config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    return None

def load_base():
    config_path = os.path.join('utils/global', f'main.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed
base = load_base()

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

class top_active(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @commands.slash_command(name="top_active", description="Показывает топ-10 самых активных пользователей по разным критериям и за выбранный период.")
    async def top(self,
                  inter,
                  interval: str = commands.Param(
                      choices=["день", "неделю", "месяц"],
                      default="день")):

        guild_id = inter.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == inter.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return 
        await inter.response.defer()  

        user_stats = {}

        today = datetime.now()  

        if interval == "день":
            messages = await inter.channel.history(
                limit=None, after=today - timedelta(days=1)).flatten()
        elif interval == "неделю":
            messages = await inter.channel.history(
                limit=None, after=today - timedelta(weeks=1)).flatten()
        elif interval == "месяц":
            messages = await inter.channel.history(
                limit=None, after=today - timedelta(days=30)).flatten()
        else:  
            pass

        for message in messages: 
            if message.author.bot:
                continue

            if message.author in user_stats:
                user_stats[message.author]['messages'] += 1
            else:
                user_stats[message.author] = {
                    'messages': 1,
                    'voice_time': 0
                }  

        sorted_user_stats = sorted(user_stats.items(),
                                   key=lambda item: item[1]['messages'],
                                   reverse=True)
        title = f"Топ-10 самых активных пользователей по сообщениям в этом канале за {interval}"

        embed = disnake.Embed(title=title, color=chosen_color)
        for i, (user, stats) in enumerate(sorted_user_stats[:10]):
            if i == 0:
                embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name=f"{i + 1}. {user.display_name} ({user.name})",
                            value=f"{stats['messages']} сообщений.",
                            inline=False)

        await inter.followup.send(embed=embed)

