import os
import json
import sqlite3
import disnake
from utils.base.colors import colors
from disnake.ext import commands
from datetime import datetime

bot = commands.InteractionBot(intents=disnake.Intents.all())

def load_base():
    config_path = os.path.join('utils/cache/configs', f'main.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

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
    color_choice = settings.get('COLOR', 'orange')
    return colors.get(color_choice.lower(), disnake.Color.orange())

base = load_base()

class sellhome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('Файл Commands/Shop/sellhome.py Загружен!')

    @commands.slash_command(name='sellhome', description='Продать жилище. (🌎)')
    async def sell_car(self, interaction: disnake.ApplicationCommandInteraction):
        guild_id = interaction.guild.id
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        try:
            # Получение информации о машинах пользователя
            cursor.execute("SELECT home_name, home_price, home_buy_date, home_image_url FROM home WHERE user_id = ?", (interaction.author.id,))
            car_info = cursor.fetchall()

            if not car_info:
                embed = disnake.Embed(
                    title=f"",
                    description=f"У вас нет мест проживания, которые вы могли бы продать.",
                    color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Создание списка машин и их цен продажи
            cars_for_sale = []
            for home_name, home_price, home_buy_date, home_image_url in car_info:
                sale_price = home_price * 0.75
                cars_for_sale.append((home_name, sale_price, home_price, home_buy_date, home_image_url))

            # Создание эмбеда со списком машин
            embed = disnake.Embed(
                title="Места в которых вы проживаете:",
                description="",
                color=chosen_color
            )

            # Добавление списка машин в эмбед
            for i, (home_name, sale_price, home_price, home_buy_date, home_image_url) in enumerate(cars_for_sale):
                formatted_balance = f"{home_price:,.0f}₽".replace(',', '.')
                formatted_sale_price = f"{sale_price:,.0f}₽".replace(',', '.')
                purchase_date_dt = datetime.strptime(home_buy_date, '%Y-%m-%d %H:%M:%S.%f')
                formatted_date = purchase_date_dt.strftime('%d.%m.%Y')
                embed.add_field(
                    name=home_name,
                    value=f"Дата покупки: {formatted_date}\nЦена покупки: {formatted_balance}\nЦена продажи: {formatted_sale_price}",
                    inline=False
                )
                # Добавление картинки машины, если она есть
                if home_image_url:
                    embed.set_image(url=home_image_url)
                    break # Выводим картинку только для первой машины

            # Создание кнопок для выбора машины
            view = disnake.ui.View()
            select = disnake.ui.Select(placeholder='Выберите место проживания для продажи', options=[
                disnake.SelectOption(label=f"{home_name}", value=f"{i}_{home_name}")
                                for i, (home_name, sale_price, home_price, home_buy_date, home_image_url) in enumerate(cars_for_sale)
            ])
            view.add_item(select)

            # Функция обратного вызова для select
            async def select_callback(interaction: disnake.MessageInteraction):
                selected_car_value = select.values[0]
                author_id = interaction.author.id
                if interaction.author.id != author_id:
                    embed = disnake.Embed(
                    title=f"",
                    description=f'Вы не можете выбрать дом для продажи, так как не являетесь владельцем.',
                    color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed)
                    return

                if selected_car_value is not None and '_' in selected_car_value:
                    try:
                        # Извлечение индекса машины из selected_car_value
                        selected_car_index = int(selected_car_value.split('_')[0])
                        selected_car_name = cars_for_sale[selected_car_index][0]
                        selected_sale_price = cars_for_sale[selected_car_index][1]
                        selected_purchase_price = cars_for_sale[selected_car_index][2]
                        selected_purchase_date = cars_for_sale[selected_car_index][3]

                        formatted_2 = f"{selected_sale_price:,.0f}₽".replace(',', '.')
                        formatted_3 = f"{selected_purchase_price:,.0f}₽".replace(',', '.')
                    
                        purchase_date_dt = datetime.strptime(selected_purchase_date, '%Y-%m-%d %H:%M:%S.%f')
                        formatted_purchase_date = purchase_date_dt.strftime('%d.%m.%Y')

                    except (IndexError, ValueError) as e:
                        await interaction.response.send_message(f"Произошла ошибка: {str(e)}")
                        return

                    # Создание подтверждения продажи
                    confirmation_embed = disnake.Embed(
                        title=f"",
                        description=f"Вы уверены, что хотите продать **{selected_car_name}** за **{formatted_2}**?",
                        color=chosen_color
                    )
                    confirmation_embed.add_field(
                        name="Цена продажи:",
                        value=f"```{formatted_2}```",
                        inline=True
                    )
                    confirmation_embed.add_field(
                        name="Дата покупки:",
                        value=f"```{formatted_purchase_date}```",
                        inline=True
                    )
                    confirmation_embed.add_field(
                        name="Цена покупки:",
                        value=f"```{formatted_3}```",
                        inline=True
                    )

                    confirmation_embed.set_image(f"https://avatars.dzeninfra.ru/get-ynews/271828/9fe3c893f234d89fd337b7fada50eb35/800x400")

                    # Создание кнопок для подтверждения или отмены
                    confirm_view = disnake.ui.View()
                    confirm_button = disnake.ui.Button(label="Подтвердить", style=disnake.ButtonStyle.green)
                    cancel_button = disnake.ui.Button(label="Отменить", style=disnake.ButtonStyle.red)

                    async def confirm_callback(button_interaction: disnake.MessageInteraction):
                        cursor.execute("SELECT COUNT(*) FROM home WHERE user_id = ? AND home_name = ?", (interaction.user.id, selected_car_name))
                        home_exists = cursor.fetchone()[0] > 0

                        if not home_exists:
                            embed = disnake.Embed(
                                title=f"",
                                description=f"Это имущество больше не принадлежит вам.",
                                color=chosen_color)
                            await button_interaction.response.send_message(embed=embed, ephemeral=True)
                            return
                        
                        cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (selected_sale_price, interaction.author.id))
                        cursor.execute("DELETE FROM home WHERE user_id = ? AND home_name = ?", (interaction.user.id, selected_car_name))
                        connection.commit()

                        # Форматирование цен
                        formatted_balance = f"{selected_purchase_price:,.2f}₽".replace(',', '.')
                        formatted_balance2 = f"{selected_sale_price:,.2f}₽".replace(',', '.')
                        purchase_date_dt = datetime.strptime(selected_purchase_date, '%Y-%m-%d %H:%M:%S.%f')
                        formatted_date = purchase_date_dt.strftime('%d.%m.%Y')

                        # Редактирование эмбеда с подтверждением
                        confirmation_embed.title = f"{selected_car_name} был продан за {formatted_balance2}"
                        confirmation_embed.description = ""

                        await button_interaction.response.edit_message(embed=confirmation_embed, view=None)

                    async def cancel_callback(button_interaction: disnake.MessageInteraction):
                        await button_interaction.response.edit_message(embed=confirmation_embed, view=None)

                    confirm_view.add_item(confirm_button)
                    confirm_view.add_item(cancel_button)
                    confirm_button.callback = confirm_callback
                    cancel_button.callback = cancel_callback
                    await interaction.response.send_message(embed=confirmation_embed, ephemeral=True, view=confirm_view)

            select.callback = select_callback
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"Произошла ошибка: {str(e)}", ephemeral=True)
