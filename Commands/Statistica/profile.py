import os
import json
import math
import disnake
import sqlite3
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

class profile(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot
        print('Файл Commands/Statistica/profile.py Загружен!')

    @commands.slash_command(name='profile', description='Узнать текущий баланс (🌎)')
    async def balance(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        try:
            if user is None:
                user = interaction.author

            guild_id = interaction.guild.id
            settings = load_config(guild_id)
            connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
            cursor = connection.cursor()
            chosen_color = get_color_from_config(settings)

            # Получение баланса пользователя
            cursor.execute("SELECT cash FROM users WHERE id = ?", (user.id,))
            balance_info = cursor.fetchone()

            if balance_info is not None:
                balance = balance_info[0]
                balance = 0 if balance <= 0.9 else math.floor(balance)
                formatted_balance = f"{balance:,}".replace(',', '.')
            else:
                formatted_balance = "Информация отсутствует"

            # Получение информации о машине
            cursor.execute("SELECT car_name, car_image_url FROM purchases WHERE user_id = ? ORDER BY purchase_price DESC", (user.id,))
            car_info = cursor.fetchone()

            if car_info:
                car_name = car_info[0]
                car_image_url = car_info[1]
            else:
                car_name = "-------------"
                car_image_url = None

            cursor.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ? AND car_name IS NOT NULL", (user.id,))
            additional_cars = cursor.fetchone()[0]
            additional_cars_text = f" (+{additional_cars - 1})" if additional_cars > 1 else ""

            cursor.execute("SELECT COUNT(*) FROM home WHERE user_id = ? AND home_name IS NOT NULL", (user.id,))
            additional_home = cursor.fetchone()[0]
            additional_home_text = f" (+{additional_home - 1})" if additional_home > 1 else ""
            home_details = f"{additional_home_text}"

            # Получение информации о доме
            cursor.execute("SELECT home_name, home_image_url FROM home WHERE user_id = ? ORDER BY home_price DESC", (user.id,))
            home_info = cursor.fetchone()

            if home_info:
                home_name = home_info[0]
            else:
                home_name = "-------------"

        except Exception as e:
            embed = disnake.Embed(
                title="",
                description=f"🔴 Произошла ошибка: {str(e)}",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Создание эмбеда для отображения информации о балансе и имуществе
        embed = disnake.Embed(title="", description="", color=chosen_color)
        embed.set_author(name=f"Ссылка на профиль",
                         url=f"https://discord.com/users/{user.id}",
                         icon_url=user.avatar.url)

        embed.add_field(
            name="Баланс:",
            value=f"```{formatted_balance}₽```",
            inline=True
        )

        embed.add_field(
            name="Имущество:",
            value=f"```{car_name}{additional_cars_text}```" if car_name != "```-------------```" else "```-------------```",
            inline=True
        )

        embed.add_field(
            name="Проживание:",
            value=f"```{home_name}{home_details}```" if home_name != "```-------------```" else "```-------------```",
            inline=True
        )
        embed.add_field(
            name="",
            value=
            f"***Создан:***\n```{user.created_at.strftime('%d.%m.%Y %H:%M:%S')}```",
            inline=True)

        user = user

        ROLE_IDS_MODERATOR = []
        for role_id in settings['ROLE_MODER'].split(','):
            try:
                ROLE_IDS_MODERATOR.append(int(role_id.strip()))
            except ValueError:
                print(f"Ошибка: Не удалось преобразовать '{role_id}' в целое число.")
        ROLE_IDS_ADMIN = []
        for role_id in settings['ROLE_ADMIN'].split(','):
            try:
                ROLE_IDS_ADMIN.append(int(role_id.strip()))
            except ValueError:
                print(f"Ошибка: Не удалось преобразовать '{role_id}' в целое число.")

        is_tech_specialist = any(role.id in ROLE_IDS_ADMIN
                                for role in user.roles)
        is_moderator = any(role.id in ROLE_IDS_MODERATOR
                            for role in user.roles)

        if user == interaction.guild.owner:
            embed.add_field(
                name="",
                value=f"***Доступ:***\n```Основатель сервера```",
                inline=True)
        elif is_tech_specialist:
            embed.add_field(name="",
                            value=f"***Доступ:***\n```Администратор сервера```",
                            inline=True)
        elif is_moderator:
            embed.add_field(name="",
                            value=f"***Доступ:***\n```Модератор сервера```",
                            inline=True)
        else:
            embed.add_field(
                name="",
                value=f"***Доступ:***\n```Участник сервера```",
                inline=True)

        embed.add_field(name="",
                        value=f"***UserID:***\n```{user.id}```",
                        inline=True)
        
        if car_image_url is not None:
            embed.set_thumbnail(url=car_image_url)
        else:
            embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.send(embed=embed)
