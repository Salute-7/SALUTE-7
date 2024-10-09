import disnake
from disnake.ext import commands
import os
import json
import sqlite3
from utils.base.colors import colors

def load_base():
    config_path = os.path.join('utils/global', f'main.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
base = load_base()

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

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

class info_news(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_image_sent_time = {} 
        self.last_image_seen_time = {} 
        self.seen_images = set() 
        self.image_cache = {}
        self.news_channels = {} 
        self.news_task = None 
        self.images_path = 'images/base'
 

    @commands.slash_command(name="info_news", description="Просмотреть собранные вами карточки!")
    async def info_news(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        config_data = load_config(interaction.guild.id)
        chosen_color = get_color_from_config(config_data)
        user_id = user.id if user else interaction.author.id
        global_channel_id = config_data.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        await interaction.response.defer()

        connection = sqlite3.connect(f'utils/cache/database/{interaction.guild_id}.db')
        cursor = connection.cursor()

        cursor.execute("SELECT image FROM seen_images WHERE user_id = ?", (user_id,))
        seen_images = cursor.fetchall()

        if seen_images:
            image_names = [row[0] for row in seen_images] 
            response = f"\n```{', '.join(image_names)}```"
        else:
            response = "Этот пользователь ещё не собрал ни одной карточки!"

        images_path2 = "images/main"

        images = [f for f in os.listdir(self.images_path) if os.path.isfile(os.path.join(self.images_path, f))]
        images2 = [f for f in os.listdir(images_path2) if os.path.isfile(os.path.join(images_path2, f))]

        cursor.execute("SELECT COUNT(*) FROM seen_images WHERE user_id = ?", (user_id,))
        total_seen_images = cursor.fetchone()[0] 

        embed = disnake.Embed(
            title=f"Коллекционные карточки: {total_seen_images} из {len(images)}",
            description=response,
            color=chosen_color
        )

        if "main.png" in images2:
            embed.set_image(url=f"attachment://main.png")

        await interaction.edit_original_response(embed=embed, file=disnake.File(os.path.join(images_path2, "main.png")))

        connection.close()