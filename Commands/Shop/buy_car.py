import os
import json
import sqlite3
import disnake
import datetime
from utils.base.selected_car import cars
from utils.base.colors import colors
from disnake.ext import commands

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

class buy_car(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('Файл Commands/Shop/buy_car.py Загружен!')

    @commands.slash_command(name='buy_car', description='Покупка автомобиля. (🌎)')
    async def buy_car(self, inter: disnake.AppCmdInter):
        await inter.response.defer()  # Отложенный ответ

        guild_id = inter.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        options = [
            disnake.SelectOption(label=car['name'], value=str(index))
            for index, car in enumerate(cars)
        ]

        select = disnake.ui.Select(placeholder='Выберите один из вариантов', options=options)

        async def select_callback(interaction: disnake.Interaction):
            nonlocal select  

            # Получение выбранного автомобиля
            selected_car = cars[int(select.values[0])]

            formatted_car = f"{selected_car['price']:,}₽".replace(',', '.')

            # Проверка баланса
            with sqlite3.connect(f'utils/cache/database/{inter.guild_id}.db') as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT cash FROM users WHERE id = ?", (interaction.user.id,))
                user_cash = cursor.fetchone()
                user_cash = user_cash[0] if user_cash else 0

            cursor.execute(
                "SELECT COUNT(*) FROM purchases WHERE user_id = ? AND car_name = ?",
                (interaction.user.id, selected_car['name'])
            )
            has_car = cursor.fetchone()[0]

            if has_car > 0:
                embed = disnake.Embed(
                    title=f"{selected_car['name']}",
                    description=f'У вас уже есть {selected_car["name"]}!',
                    color=chosen_color
                )
                embed.set_footer(text=f'Стоимость: {formatted_car}') 
                embed.set_image(url=selected_car['image'])
                await interaction.response.edit_message(embed=embed)
                return

            buy_button = disnake.ui.Button(label="Купить", style=disnake.ButtonStyle.green)

            if user_cash < selected_car['price']:
                embed = disnake.Embed(
                    title=f"{selected_car['name']}",
                    description=f'У вас недостаточно средств для покупки {selected_car["name"]}.',
                    color=chosen_color
                )
                embed.set_footer(text=f'Стоимость: {formatted_car}') 
                embed.set_image(url=selected_car['image'])
                view = disnake.ui.View()
                view.add_item(select)
                view.remove_item(buy_button)
                await interaction.response.edit_message(embed=embed, view=view)
                return

            # Подтверждение покупки
            embed = create_embed(
                '',
                f'{selected_car["description"]}',
                color=chosen_color
            )
            embed.set_footer(text=f'Стоимость: {formatted_car}') 
            embed.set_image(url=selected_car['image'])

            view = disnake.ui.View()
            view.add_item(buy_button)

            # Передаем view и buy_button в функцию обратного вызова
            buy_button.callback = lambda interaction: buy_button_callback(interaction, view, buy_button) 
    

            async def buy_button_callback(interaction: disnake.MessageInteraction):
                nonlocal select

                selected_car = cars[int(select.values[0])]

                if interaction.user != inter.user: 
                    embed = disnake.Embed(
                    title=f"",
                    description=f'Ты не можешь купить эту машину!.',
                    color=chosen_color
                    )
                    embed.set_footer(text=f'Стоимость: {formatted_car}') 
                    embed.set_image(url=selected_car['image'])
                    await interaction.response.send_message(embed=embed)
                    return


                with sqlite3.connect(f'utils/cache/database/{inter.guild_id}.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT cash FROM users WHERE id = ?", (interaction.user.id,))
                    user_cash = cursor.fetchone()
                    user_cash = user_cash[0] if user_cash else 0

                if user_cash < selected_car['price']:
                    embed = disnake.Embed(
                        title=f"{selected_car['name']}",
                        description=f'У вас недостаточно средств для покупки {selected_car["name"]}.',
                        color=chosen_color
                    )
                    embed.set_footer(text=f'Стоимость: {formatted_car}') 
                    embed.set_image(url=selected_car['image'])
                    view.remove_item(buy_button)
                    await interaction.response.edit_message(embed=embed, view=view)
                    return

                # Обработка покупки
                with sqlite3.connect(f'utils/cache/database/{inter.guild_id}.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?", (selected_car['price'], interaction.user.id))
                    cursor.execute(
                        "INSERT INTO purchases (user_id, car_name, purchase_price, car_image_url, purchase_date) VALUES (?, ?, ?, ?, ?)",
                        (interaction.user.id, selected_car['name'], selected_car['price'], selected_car['image'], datetime.datetime.now())
                    )
                    connection.commit()

                # Вывод подтверждения покупки
                embed = disnake.Embed(
                    title="Поздравляем!",
                    description=f"Вы успешно купили {selected_car['name']} за {formatted_car}!",
                    color=chosen_color
                )
                embed.set_footer(text=f'Стоимость: {formatted_car}') 
                embed.set_image(url=selected_car['image'])
                select.disabled = False  
                # Удаляем кнопку "Купить"
                view.remove_item(buy_button)

                # Обновляем сообщение
                await interaction.response.edit_message(embed=embed, view=view) 

            buy_button.callback = buy_button_callback
            view = disnake.ui.View()
            view.add_item(buy_button)
            view.add_item(select)

            # Отправляем сообщение с кнопкой и селектом
            await interaction.response.edit_message(embed=embed, view=view)

        select.callback = select_callback
        view = disnake.ui.View()
        view.add_item(select)
        embed=create_embed('BMW M5 2018',           
                            "**Характеристики:**\n" 
                            "Год выпуска: 2018\n"              
                            "Поколение: F90 (2017—2020)\n"              
                            "Пробег: 56 000 км\n"              
                            "ПТС: Оригинал\n"             
                            "Владельцев по ПТС: 1\n"             
                            "Состояние: Не битый\n"             
                            "Модификация: 4.4 AT (625 л.с.)\n"              
                            "Объём двигателя: 4.4 л\n"              
                            "Привод: Полный К/П: Авто", color=chosen_color)
        embed.set_image(url='https://avatars.mds.yandex.net/get-autoru-vos/5238237/e9a5f74c0dc83b0187566312601bf258/1200x900')
        await inter.edit_original_message(embed=embed, view=view)