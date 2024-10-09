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

class User:
    def __init__(self):
        self.balance = 0
        self.last_reward_time = None

    def can_receive_reward(self):
        if self.last_reward_time is None:
            return True
        return datetime.now() - self.last_reward_time >= timedelta(hours=1)

    def receive_reward(self, job):
        if self.can_receive_reward():
            rewards = {
                "таксистом": (10000, 99000),
                "пилотом": (200000, 350000),
                "курьером": (20000, 75000),
                "учёным": (450000, 950000),
                "капитаном судна": (120000, 450000),
                "на нефтебазе": (175000, 350000),
                "дальнобойщиком": (150000, 300000),
                "автомехаником": (80000, 170000)
            }
            reward_amount = random.randint(*rewards[job])
            self.balance += reward_amount
            self.last_reward_time = datetime.now()
            return reward_amount
        else:
            return None

    def receive_penalty(self, job):
        penalties = {
            "таксистом": (3000, 8000),
            "пилотом": (10000, 45000),
            "курьером": (2000, 7000),
            "учёным": (100000, 250000),
            "капитаном судна": (50000, 100000),
            "на нефтебазе": (40000, 80000),
            "дальнобойщиком": (10000, 45000),
            "автомехаником": (8000, 34000)
        }
        penalty = random.randint(*penalties[job])
        if self.balance >= penalty:
            self.balance -= penalty
            return penalty
        else:
            return None

class reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}

    @commands.slash_command(name="reward", description="Получить зарплату за работу раз в час.")
    async def reward(self, interaction: disnake.ApplicationCommandInteraction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        settings = load_config(guild_id) 
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        chosen_color = get_color_from_config(settings) 

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        if user_id not in self.user_data:
            self.user_data[user_id] = User()

        user = self.user_data[user_id]

        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operation = random.choice(['+', '-', '*'])

        if operation == '+':
            correct_answer = num1 + num2
        elif operation == '-':
            correct_answer = num1 - num2
        else:
            correct_answer = num1 * num2

        example = f"{num1} {operation} {num2}"

        answer_input = disnake.ui.TextInput(label="Ваш ответ:", placeholder="Введите ваш ответ", required=True, custom_id="answer_input")
        
        modal = disnake.ui.Modal(title=f"Решите пример: {example}", components=[answer_input], timeout=60)

        await interaction.response.send_modal(modal)

        def check(m):
            return m.author.id == user_id and m.channel == interaction.channel

        try:
            modal_response = await self.bot.wait_for('modal_submit', check=check, timeout=60.0)

            user_answer_str = modal_response.text_values.get("answer_input")
            
            if user_answer_str is None:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Вы не ввели ответ или задача была решена неправильно.",
                    color=chosen_color  
                )                
                await interaction.send(embed=embed, ephemeral=True)
                return

            try:
                user_answer = int(user_answer_str)
            except ValueError:
                await interaction.send("Пожалуйста, введите корректный числовой ответ.", ephemeral=True)
                return

            if user_answer == correct_answer:
                kosyak = random.choice(["превышаете свои полномочия.", "забываете отметиться в журнале.", "выходите на работу с опозданием.", "выходите на работу пьяным.", "теряете несколько купюр.", "засыпаете на рабочем месте.", "конфликтуете с начальником."])
                job = random.choice(["таксистом", "пилотом", "курьером", "учёным", "капитаном судна", "на нефтебазе", "дальнобойщиком", "автомехаником"])
            else:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"Вы не решили задачу или задача была решена неправильно.",
                    color=chosen_color  
                )
                await modal_response.send(embed=embed, ephemeral=True)
            if user.can_receive_reward():
                reward_amount = user.receive_reward(job)
                penalty = user.receive_penalty(job)

                formatted_reward_amount = f"{reward_amount:,}".replace(',', '.') if reward_amount is not None else "0"

                formatted_penalty = f"{penalty:,}".replace(',', '.') if penalty is not None else "0"

                cursor.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
                balance_info = cursor.fetchone()
                
                if balance_info is not None:
                    balance = balance_info[0]
                    formatted_balance = f"{balance:,}".replace(',', '.')
                else:
                    formatted_balance = "0"

                cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (reward_amount, user_id))
                connection.commit()

                cursor.execute("SELECT cash FROM users WHERE id = ?", (user_id,))
                balance_info = cursor.fetchone()

                if balance_info is not None:
                    balance = balance_info[0]
                    formatted_balance = f"{balance:,}".replace(',', '.')
                else:
                    formatted_balance = "Информация отсутствует"

                if user.last_reward_time is not None:
                    next_reward_time = user.last_reward_time + timedelta(hours=1)
                    formatted_next_reward_time = next_reward_time.strftime("%H:%M:%S")
                else:
                    formatted_next_reward_time = "Неизвестно"

                embed = disnake.Embed(
                    title="Работа завершена",
                    description=(
                        f"Вы работаете {job}, но {kosyak}\n"
                        f"В следующий раз вы сможете выйти на работу в {formatted_next_reward_time}."
                    ),
                    color=chosen_color
                )
                embed.add_field(name="Получено:", value=f"```{formatted_reward_amount}₽```", inline=True)
                embed.add_field(name="Утеряно:", value=f"```{formatted_penalty}₽```", inline=True)                
                embed.add_field(name="Итог:", value=f"```{formatted_balance}₽```", inline=True)

                job_images = {
                    "таксистом": 'https://avatars.dzeninfra.ru/get-zen_doc/168279/pub_5cef7a2ae927bd00ae01a529_5cef8b9c1cd66200af7a458f/scale_1200',
                    "пилотом": 'https://i.pinimg.com/originals/53/52/57/535257b9fe97c87c077751a38704ba0e.jpg',
                    "курьером": 'https://s0.rbk.ru/v6_top_pics/media/img/2/39/347129397912392.webp',
                    "учёным": 'https://nenadzor.ru/img/news/kabelnaya-prohodka-v-atomnoj-otrasli-2.jpg',
                    "капитаном судна": 'https://i.pinimg.com/originals/ef/42/7c/ef427cec68961663c7d7a9c2e061919f.jpg',
                    "на нефтебазе": 'https://www.marsalis.ee/wp-content/uploads/2016/10/metall_bg.jpg',
                    "дальнобойщиком": 'https://akvilon-leasing.ru/upload/iblock/3ba/3baffda321df6080c033aec98121d6f6.jpg',
                    "автомехаником": 'https://avatars.mds.yandex.net/get-altay/4442047/2a00000178ad80465c98b781717df018f30b/orig'
                }

                if job in job_images:
                    embed.set_image(url=job_images[job])

                await modal_response.send(embed=embed) 
            else:
                if user.last_reward_time is not None:
                    next_reward_time = user.last_reward_time + timedelta(hours=1)
                    formatted_next_reward_time = next_reward_time.strftime("%H:%M:%S")
                else:
                    formatted_next_reward_time = "Неизвестно"
                embed = disnake.Embed(
                    title="Зарплата уже получена!",
                    description=f"Вы уже получали зарплату. Попробуйте снова в {formatted_next_reward_time}.",
                    color=chosen_color  
                )
                await modal_response.send(embed=embed, ephemeral=True)
                return

        except asyncio.TimeoutError:
            modal_response = None  
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Время на решение примера истекло.",
                color=chosen_color  
            )
            await modal_response.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            pass
