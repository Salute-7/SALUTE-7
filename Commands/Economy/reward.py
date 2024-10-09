import os
import json
import sqlite3
import disnake
import math
import random
import asyncio
from datetime import datetime, timedelta
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

user_data = {}

class User:
    def __init__(self):
        self.last_reward_time = None  # Время последнего получения награды
        self.balance = 0  # Баланс пользователя

    def can_receive_reward(self):
        if self.last_reward_time is None:
            return True
        return datetime.now() - self.last_reward_time >= timedelta(seconds=1)

    def receive_reward(self, job):
        if self.can_receive_reward():
            if job == "таксистом":
                reward_amount = random.randint(10000, 99000)
            elif job == "пилотом":
                reward_amount = random.randint(200000, 350000)
            elif job == "курьером":
                reward_amount = random.randint(20000, 75000)
            elif job == "учёным":
                reward_amount = random.randint(450000, 950000)
            elif job == "капитаном судна":
                reward_amount = random.randint(120000, 450000)
            elif job == "на нефтебазе":
                reward_amount = random.randint(175000, 350000)
            elif job == "дальнобойщиком":
                reward_amount = random.randint(150000, 300000)
            elif job == "автомехаником":
                reward_amount = random.randint(80000, 170000)
            self.balance += reward_amount
            self.last_reward_time = datetime.now()
            return reward_amount
        else:
            return None

    def receive_penalty(self, job):
        if job == "таксистом":
            penalty = random.randint(3000, 8000)
        elif job == "пилотом":
            penalty = random.randint(10000, 45000)
        elif job == "курьером":
            penalty = random.randint(2000, 7000)
        elif job == "учёным":
            penalty = random.randint(100000, 250000)
        elif job == "капитаном судна":
            penalty = random.randint(50000, 100000)
        elif job == "на нефтебазе":
            penalty = random.randint(40000, 80000)
        elif job == "дальнобойщиком":
            penalty = random.randint(10000, 45000)
        elif job == "автомехаником":
            penalty = random.randint(8000, 34000)       
        if self.balance >= penalty:
            self.balance -= penalty
            return penalty
        else:
            return 0  # Если недостаточно средств, штраф не применяется


class reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        print('Файл Commands/Economy/reward.py Загружен!')

    @commands.slash_command(name="reward", description="Получить зарплату за работу раз в час. (🌎)")
    async def reward(self, interaction: disnake.ApplicationCommandInteraction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        settings = load_config(guild_id)  # Предполагается, что эта функция определена где-то в вашем коде
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        chosen_color = get_color_from_config(settings)  # Функция для выбора цвета из конфигурации

        if user_id not in self.user_data:
            self.user_data[user_id] = User()

        user = self.user_data[user_id]

        # Случайный выбор работы
        kosyak = random.choice(["превышаете свои полномочия.", "забываете отметиться в журнале.", "выходите на работу c опозданием.", "выходите на работу пьяным.", "теряете несколько купюр.", "засыпаете на рабочем месте.", "конфликтуете с начальником."])
        job = random.choice(["таксистом", "пилотом", "курьером", "учёным", "капитаном судна", "на нефтебазе", "дальнобойщиком", "автомехаником"])
        reward_amount = user.receive_reward(job)
        penalty = user.receive_penalty(job)

        itog = (reward_amount - penalty) if reward_amount is not None else 0

        formatted_reward_amount = f"{itog:,}".replace(',', '.')
        formatted_reward = f"{reward_amount:,}".replace(',', '.') if reward_amount is not None else "Не удалось получить награду"
        formatted_penalty = f"{penalty:,}".replace(',', '.')

        next_reward_time = user.last_reward_time + timedelta(seconds=1)# Добавляем 1 час
        formatted_next_reward_time = next_reward_time.strftime("%H:%M:%S") # Форматируем время

        if reward_amount is not None:
            try:
                cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (reward_amount, user_id))
                connection.commit()

                cursor.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
                balance_info = cursor.fetchone()

                if balance_info is not None:
                    balance = balance_info[0]
                    formatted_balance = f"{balance:,}".replace(',', '.')
                else:
                    formatted_balance = "Информация отсутствует"

                embed = disnake.Embed(
                    title=f"",
                    description=(
                        f"Вы работаете {job}, но {kosyak}\n"
                        f"В следующий раз вы сможете выйти на работу в {formatted_next_reward_time}."
                    ),
                    color=chosen_color
                )
                embed.add_field(name="Получено:", value=f"```{formatted_reward_amount}₽```", inline=True)
                embed.add_field(name="Утеряно:", value=f"```{formatted_penalty}₽```", inline=True)                
                embed.add_field(name="Итог:", value=f"```{formatted_balance}₽```", inline=True)
                # Установка изображения в зависимости от работы
                if job == "таксистом":
                    car_image_url = 'https://avatars.dzeninfra.ru/get-zen_doc/168279/pub_5cef7a2ae927bd00ae01a529_5cef8b9c1cd66200af7a458f/scale_1200'
                    embed.set_image(url=car_image_url)
                elif job == "пилотом":
                    plane_image_url = 'https://i.pinimg.com/originals/53/52/57/535257b9fe97c87c077751a38704ba0e.jpg'  
                    embed.set_image(url=plane_image_url)
                elif job == "курьером":
                    plane_image_url = 'https://s0.rbk.ru/v6_top_pics/media/img/2/39/347129397912392.webp' 
                    embed.set_image(url=plane_image_url)
                elif job == "учёным":
                    plane_image_url = 'https://nenadzor.ru/img/news/kabelnaya-prohodka-v-atomnoj-otrasli-2.jpg'  
                    embed.set_image(url=plane_image_url)
                elif job == "капитаном судна":
                    plane_image_url = 'https://i.pinimg.com/originals/ef/42/7c/ef427cec68961663c7d7a9c2e061919f.jpg'  
                    embed.set_image(url=plane_image_url)
                elif job == "на нефтебазе":
                    plane_image_url = 'https://www.marsalis.ee/wp-content/uploads/2016/10/metall_bg.jpg'  
                    embed.set_image(url=plane_image_url)
                elif job == "дальнобойщиком":
                    plane_image_url = 'https://akvilon-leasing.ru/upload/iblock/3ba/3baffda321df6080c033aec98121d6f6.jpg'
                    embed.set_image(url=plane_image_url)
                elif job == "автомехаником":
                    plane_image_url = 'https://avatars.mds.yandex.net/get-altay/4442047/2a00000178ad80465c98b781717df018f30b/orig' 
                    embed.set_image(url=plane_image_url)
                await interaction.send(embed=embed)

            except sqlite3.Error as e:
                await interaction.send("Произошла ошибка при обновлении базы данных.")
                print(f"Database error: {e}")

        else:    
            embed = disnake.Embed(
                title="Зарплата уже получена!",
                description=f"Вы уже получали зарплату. Попробуйте снова в `{formatted_next_reward_time}.`",
                color=chosen_color)
            await interaction.send(embed=embed, ephemeral=True)
            return

        connection.close()
 