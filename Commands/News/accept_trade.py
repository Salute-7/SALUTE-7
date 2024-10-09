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

class accept_trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_image_sent_time = {} 
        self.last_image_seen_time = {} 
        self.seen_images = set() 
        self.image_cache = {}
        self.news_channels = {} 
        self.news_task = None 
        self.images_path = 'images/base'

    @commands.slash_command(name="accept_trade", description="Принимает предложение о продаже карточки!")
    async def accept_trade(self, interaction: disnake.ApplicationCommandInteraction, trade_id: int):
        config_data = load_config(interaction.guild.id)
        chosen_color = get_color_from_config(config_data)
        user_id = interaction.author.id

        if trade_id not in self.trade_requests:
            embed = disnake.Embed(
                title="",
                description=f"{base['ICON_PERMISSION']} Предложение с таким ID не найдено!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        trade_request = self.trade_requests[trade_id]

        if trade_request["buyer"] is not None:
            embed = disnake.Embed(
                title="",
                description=f"{base['ICON_PERMISSION']} Это предложение уже принято другим пользователем!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        connection = sqlite3.connect(f'utils/cache/database/{interaction.guild_id}.db')
        cursor = connection.cursor()

        cursor.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
        buyer_cash = cursor.fetchone()[0]
        if buyer_cash < trade_request["price"]:
            embed = disnake.Embed(
                title="",
                description=f"{base['ICON_PERMISSION']} У вас недостаточно монет, чтобы купить эту карточку!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            connection.close()
            return

        trade_request["buyer"] = interaction.author

        cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?", (trade_request["price"], user_id))
        cursor.execute("INSERT INTO seen_images (user_id, image) VALUES (?, ?)", (user_id, trade_request["card_name"]))
        cursor.execute("DELETE FROM seen_images WHERE user_id = ? AND image = ?", (trade_request["seller"].id, trade_request["card_name"]))
        connection.commit()

        embed = disnake.Embed(
            title="",
            description=f"{base['APPROVED']} Вы успешно купили карточку '{trade_request['card_name']}' у {trade_request['seller'].mention} за {trade_request['price']} монет!",
            color=chosen_color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        del self.trade_requests[trade_id]

        connection.close()
    