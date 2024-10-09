import os
import json
import sqlite3
import disnake
from utils.base.colors import colors
from disnake.ext import commands

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

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'orange')
    return colors.get(color_choice.lower(), disnake.Color.orange())

class top_balance(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot
        print('Файл Commands/Statistica/top_balance.py Загружен!')

    @bot.slash_command(name="top_balance", description="Показывает топ 10 по балансу (🌎)")
    async def top_balance(self, ctx):
        await ctx.response.defer()  # Отложенный ответ

        guild_id = ctx.guild.id
        settings = load_config(guild_id)  # Предполагается, что у вас есть функция load_config
        chosen_color = get_color_from_config(settings)  # Предполагается, что у вас есть функция get_color_from_config

        # Подключение к базе данных
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()

        # Получение топ-10 пользователей по балансу
        cursor.execute("SELECT id, cash FROM users WHERE cash >= 1 ORDER BY cash DESC LIMIT 10")
        top_players = cursor.fetchall()

        # Проверка на наличие доступных пользователей
        if not top_players:
            await ctx.edit_original_response(content="Нет доступных пользователей для отображения.")
            return

        embed = disnake.Embed(title="ТОП-10 самых богатых пользователей", color=chosen_color)
        for i, player in enumerate(top_players):
            user_id = player[0]
            try:
                # Получение пользователя по ID
                user = await ctx.guild.fetch_member(user_id)
                # Форматирование упоминания пользователя
                mention = f"{user.display_name}" if user else ""
            except (disnake.NotFound, disnake.HTTPException):
                # Пропуск пользователя, если он не найден или недоступен
                continue
            
            formatted_cash = f"{int(player[1]):,}".replace(',', '.')

            # Получаем информацию о машине пользователя из таблицы purchases
            cursor.execute("SELECT car_name, car_image_url FROM purchases WHERE user_id = ? ORDER BY purchase_price DESC", (user.id,))
            car_info = cursor.fetchone()

            cursor.execute("SELECT home_name, home_image_url FROM home WHERE user_id = ? ORDER BY home_price DESC", (user.id,))
            home_info = cursor.fetchone()

            # Получаем информацию о доме пользователя
            cursor.execute("SELECT home_name, home_info FROM home WHERE user_id = ?", (user.id,))
            home_info = cursor.fetchone()

            car_details = ""
            if car_info:
                car_name = car_info[0]
                cursor.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ? AND car_name IS NOT NULL", (user.id,))
                additional_cars = cursor.fetchone()[0]
                additional_cars_text = f" (+{additional_cars - 1})" if additional_cars > 1 else ""
                car_details = f"| {car_name}{additional_cars_text}"

            home_details = ""
            if home_info:
                home_name = home_info[0]
                home_infos = home_info[1]
                cursor.execute("SELECT COUNT(*) FROM home WHERE user_id = ? AND home_name IS NOT NULL", (user.id,))
                additional_home = cursor.fetchone()[0]
                additional_home_text = f" (+{additional_home - 1})" if additional_home > 1 else ""
                home_details = f"| {home_name}, {home_infos} {additional_home_text}"

            if i == 0:  
                embed.set_thumbnail(url=user.avatar.url)

            # Добавляем информацию о пользователе в эмбед
            embed.add_field(
                name=f"{i + 1}. {user.display_name} ({user.name})",
                value=f"{formatted_cash}₽ {car_details} {home_details}",
                inline=False
            )

        # Отправка встраивания
        await ctx.edit_original_response(embed=embed)

        # Закрытие соединения с базой данных
        connection.close()