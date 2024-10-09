import os
import json
import sqlite3
import disnake
import asyncio
from utils.base.colors import colors
from disnake.ext import commands
from datetime import datetime

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

class sellcar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='sellcar', description='Продать свою машину.')
    async def sell_car(self, interaction: disnake.ApplicationCommandInteraction):
        guild_id = interaction.guild.id
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        cursor.execute("SELECT car_name, purchase_price, purchase_date, car_image_url FROM purchases WHERE user_id = ?", (interaction.author.id,))
        car_info = cursor.fetchall()

        if not car_info:
            embed = disnake.Embed(
                title=f"Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} У вас нет машины для продажи.",
                color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer()

        cars_for_sale = []
        for car_name, purchase_price, purchase_date, car_image_url in car_info:
            sale_price = purchase_price * 0.75
            cars_for_sale.append((car_name, sale_price, purchase_price, purchase_date, car_image_url))

        embed = disnake.Embed(
            title="Ваши машины:",
            description="",
            color=chosen_color
        )

        for i, (car_name, sale_price, purchase_price, purchase_date, car_image_url) in enumerate(cars_for_sale):
            formatted_balance = f"{purchase_price:,.0f}₽".replace(',', '.')
            formatted_sale_price = f"{sale_price:,.0f}₽".replace(',', '.')
            purchase_date_dt = datetime.strptime(purchase_date, '%Y-%m-%d %H:%M:%S.%f')
            formatted_date = purchase_date_dt.strftime('%d.%m.%Y')
            embed.add_field(
                name=car_name,
                value=f"Дата покупки: {formatted_date}\nЦена покупки: {formatted_balance}\nЦена продажи: {formatted_sale_price}",
                inline=False
            )
            if car_image_url:
                embed.set_image(url=car_image_url)
                break 

        view = disnake.ui.View()
        select = disnake.ui.Select(placeholder='Выберите машину для продажи', options=[
            disnake.SelectOption(label=f"{car_name}", value=f"{i}_{car_name}")
                            for i, (car_name, sale_price, purchase_price, purchase_date, car_image_url) in enumerate(cars_for_sale)
        ])
        view.add_item(select)

        async def select_callback(interaction: disnake.MessageInteraction):
            await interaction.response.defer()
            selected_car_value = select.values[0]
            author_id = interaction.author.id
            if interaction.author.id != author_id:
                embed = disnake.Embed(
                title=f"",
                description=f"{base['ICON_PERMISSION']} Вы не можете выбрать машину для продажи, так как не являетесь владельцем.",
                color=chosen_color
                )
                await interaction.edit_original_response(embed=embed)
                return
            if selected_car_value is not None and '_' in selected_car_value:
                try:
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
                    pass

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

                confirm_view = disnake.ui.View()
                confirm_button = disnake.ui.Button(label="Подтвердить", style=disnake.ButtonStyle.green)
                cancel_button = disnake.ui.Button(label="Отменить", style=disnake.ButtonStyle.red)

                async def confirm_callback(button_interaction: disnake.MessageInteraction):
                    cursor.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ? AND car_name = ?", (interaction.user.id, selected_car_name))
                    car_exists = cursor.fetchone()[0] > 0

                    if not car_exists:
                        embed = disnake.Embed(
                            title=f"Ошибка при попытке использовать команду",
                            description=f"{base['ICON_PERMISSION']} Это имущество больше не принадлежит вам.",
                            color=chosen_color)
                        message = interaction.edit_original_response(embed=embed)
                        await asyncio.sleep(5)
                        await message.delete()
                        return

                    cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (selected_sale_price, interaction.author.id))
                    cursor.execute("DELETE FROM purchases WHERE user_id = ? AND car_name = ?", (interaction.user.id, selected_car_name))
                    connection.commit()

                    formatted_balance = f"{selected_purchase_price:,.2f}₽".replace(',', '.')
                    formatted_balance2 = f"{selected_sale_price:,.2f}₽".replace(',', '.')
                    purchase_date_dt = datetime.strptime(selected_purchase_date, '%Y-%m-%d %H:%M:%S.%f')
                    formatted_date = purchase_date_dt.strftime('%d.%m.%Y')

                    confirmation_embed.title = f"{selected_car_name} был продан за {formatted_balance2}"
                    confirmation_embed.description = ""

                    await button_interaction.response.edit_message(embed=confirmation_embed, view=None)

                async def cancel_callback(button_interaction: disnake.MessageInteraction):
                    await button_interaction.response.edit_message(embed=confirmation_embed, view=None)

                confirm_view.add_item(confirm_button)
                confirm_view.add_item(cancel_button)
                confirm_button.callback = confirm_callback
                cancel_button.callback = cancel_callback
                await interaction.edit_original_response(embed=confirmation_embed, view=confirm_view)

        select.callback = select_callback
        await interaction.edit_original_response(embed=embed, view=view)

        await asyncio.sleep(120)
        await interaction.edit_original_message(embed=embed, view=None)

