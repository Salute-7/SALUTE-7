import disnake
from disnake.ext import commands
import os
import random
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

class trade_card(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_image_sent_time = {} 
        self.last_image_seen_time = {}
        self.seen_images = set() 
        self.image_cache = {} 
        self.news_channels = {} 
        self.news_task = None
        self.trade_requests = {}
        self.images_path = 'images/base'

    @commands.slash_command(name="trade_card", description="Продает или передает коллекционную карточку!")
    async def trade_card(self, interaction: disnake.ApplicationCommandInteraction, card_name: str, user: disnake.Member, price: int = None):
        config_data = load_config(interaction.guild.id)
        chosen_color = get_color_from_config(config_data)
        user_id = interaction.author.id

        global_channel_id = config_data.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
                "Ошибка при отправке сообщения в глобальный чат:",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        if card_name not in os.listdir(self.images_path):
            embed = disnake.Embed(
                title="",
                description=f"{base['ICON_ERROR']} Карточки с таким именем не существует!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        connection = sqlite3.connect(f'utils/cache/database/{interaction.guild_id}.db')
        cursor = connection.cursor()

        cursor.execute("SELECT 1 FROM seen_images WHERE user_id = ? AND image = ?", (user_id, card_name))
        result = cursor.fetchone()
        if not result:
            embed = disnake.Embed(
                title="",
                description=f"{base['ICON_PERMISSION']} У вас нет этой карточки!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            connection.close()
            return

        if price is not None:
            trade_id = random.randint(1, 9999) 
            self.trade_requests[trade_id] = {
                "card_name": card_name,
                "seller": interaction.author,
                "price": price,
                "buyer": None 
            }

            embed = disnake.Embed(
                title=f"Предложение о продаже коллекционной карточки!",
                description=f"{interaction.author.mention} предлагает купить его карточку `{card_name}` за {price}₽\n"
                          f"Чтобы принять предложение, используйте команду </accept_trade:1289624166021992463> `{trade_id}.`",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed)
        else:
            cursor.execute("INSERT INTO seen_images (user_id, image) VALUES (?, ?)", (user.id, card_name))
            connection.commit()

            cursor.execute("DELETE FROM seen_images WHERE user_id = ? AND image = ?", (user_id, card_name))
            connection.commit()

            embed = disnake.Embed(
                title="",
                description=f"{base['APPROVED']} Вы успешно передали карточку '{card_name}' пользователю {user.mention}!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        connection.close()       