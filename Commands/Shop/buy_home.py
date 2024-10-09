import os
import json
import sqlite3
import disnake
import datetime
import asyncio
from utils.base.selected_home import homes
from utils.base.colors import colors
from disnake.ext import commands

bot = commands.InteractionBot(intents=disnake.Intents.all())

def load_base():
    config_path = os.path.join('utils/global', f'main.json')
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
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

base = load_base()

class buy_home(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='buy_home', description='Покупка жилища.')
    async def buy_car(self, inter: disnake.AppCmdInter): 

        guild_id = inter.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        await inter.response.defer()

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == inter.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return 

        options = [
            disnake.SelectOption(label=car['name'], value=str(index))
            for index, car in enumerate(homes)
        ]

        select = disnake.ui.Select(placeholder='Выберите один из вариантов', options=options)

        async def select_callback(interaction: disnake.Interaction):
            nonlocal select  
            author_id = interaction.author.id
            if interaction.author.id != author_id:
                embed = disnake.Embed(
                title=f"Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Вы не можете выбрать раздел, так как не являетесь владельцем.",
                color=chosen_color
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            selected_home = homes[int(select.values[0])]

            formatted_home = f"{selected_home['price']:,}₽".replace(',', '.')

            with sqlite3.connect(f'utils/cache/database/{inter.guild_id}.db') as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT cash FROM users WHERE id = ?", (interaction.user.id,))
                user_cash = cursor.fetchone()
                user_cash = user_cash[0] if user_cash else 0

            cursor.execute(
                "SELECT COUNT(*) FROM home WHERE user_id = ? AND home_name = ?",
                (interaction.user.id, selected_home['name'])
            )
            has_car = cursor.fetchone()[0]

            if has_car > 0:
                embed = disnake.Embed(
                    title=f"{selected_home['name']}",
                    description=f'У вас уже есть {selected_home["name"]}!',
                    color=chosen_color
                )
                embed.set_footer(text=f'Стоимость: {formatted_home}') 
                embed.set_image(url=selected_home['image'])
                await interaction.response.edit_message(embed=embed)
                return

            buy_button = disnake.ui.Button(label="Купить", style=disnake.ButtonStyle.green)

            if user_cash < selected_home['price']:
                embed = disnake.Embed(
                    title=f"{selected_home['name']}",
                    description=f'У вас недостаточно средств для покупки {selected_home["name"]}.',
                    color=chosen_color
                )
                embed.set_footer(text=f'Стоимость: {formatted_home}') 
                embed.set_image(url=selected_home['image'])
                view = disnake.ui.View()
                view.add_item(select)
                view.remove_item(buy_button)
                await interaction.response.edit_message(embed=embed, view=view)
                return

            embed = create_embed(
                '',
                f'{selected_home["description"]}',
                color=chosen_color
            )
            embed.set_footer(text=f'Стоимость: {formatted_home}') 
            embed.set_image(url=selected_home['image'])

            view = disnake.ui.View()
            view.add_item(buy_button)

            buy_button.callback = lambda interaction: buy_button_callback(interaction, view, buy_button) 
    
            async def buy_button_callback(interaction: disnake.MessageInteraction):
                nonlocal select

                selected_home = homes[int(select.values[0])]

                if interaction.user != inter.user: 
                    embed = disnake.Embed(
                    title=f"Ошибка при попытке использовать команду",
                    description=f'{base["ICON_PERMISSION"]} Ты не можешь купить это!',
                    color=chosen_color
                    )
                    embed.set_footer(text=f'Стоимость: {formatted_home}') 
                    embed.set_image(url=selected_home['image'])
                    message = await inter.edit_original_response(embed=embed)
                    await asyncio.sleep(5)
                    await message.delete()
                    return

                with sqlite3.connect(f'utils/cache/database/{inter.guild_id}.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT cash FROM users WHERE id = ?", (interaction.user.id,))
                    user_cash = cursor.fetchone()
                    user_cash = user_cash[0] if user_cash else 0

                if user_cash < selected_home['price']:
                    embed = disnake.Embed(
                        title=f"{selected_home['name']}",
                        description=f'У вас недостаточно средств для покупки {selected_home["name"]}.',
                        color=chosen_color
                    )
                    embed.set_footer(text=f'Стоимость: {formatted_home}') 
                    embed.set_image(url=selected_home['image'])
                    view.remove_item(buy_button)
                    await interaction.response.edit_message(embed=embed, view=view)
                    return

                with sqlite3.connect(f'utils/cache/database/{inter.guild_id}.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?", (selected_home['price'], interaction.user.id))
                    cursor.execute(
                        "INSERT INTO home (user_id, home_name, home_price, home_image_url, home_info, home_buy_date) VALUES (?, ?, ?, ?, ?, ?)",
                        (interaction.user.id, selected_home['name'], selected_home['price'], selected_home['image'], selected_home['info'], datetime.datetime.now())
                    )
                    connection.commit()

                embed = disnake.Embed(
                    title="Поздравляем!",
                    description=f"Вы успешно купили {selected_home['name']} за {formatted_home}!",
                    color=chosen_color
                )
                embed.set_footer(text=f'Стоимость: {formatted_home}') 
                embed.set_image(url=selected_home['image'])
                select.disabled = False  
                view.remove_item(buy_button)
                await interaction.response.edit_message(embed=embed, view=view) 

            buy_button.callback = buy_button_callback
            view = disnake.ui.View()
            view.add_item(buy_button)
            view.add_item(select)

            await interaction.response.edit_message(embed=embed, view=view)
        select.callback = select_callback
        view = disnake.ui.View()
        view.add_item(select)
        embed=create_embed('Home S+',           
                            "**О доме:**\n" 
                            "Дом 600 м². 52,3 сот.\n"                             
                            "Количество комнат: 4\n" 
                            "Площадь дома: 600 м²\n"              
                            "Площадь участка: 52.3 сот.\n"              
                            "Этажей в доме: 2\n"              
                            "Категория земель: индивидуальное жилищное строительство\n"             
                            "Материал стен: кирпич\n"             
                            "Ремонт: дизайнерский\n"             
                            "Расстояние от МКАД: 14 км\n", color=chosen_color)
        embed.set_image(url='https://i.pinimg.com/originals/de/49/8e/de498e564f09f479af15e8938c61cc6e.jpg')
        await inter.edit_original_message(embed=embed, view=view)

        await asyncio.sleep(120)
        await inter.edit_original_message(embed=embed, view=None)
