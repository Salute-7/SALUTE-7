import disnake
from disnake.ext import commands
import os
import random
import json
import time
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

class news(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_image_sent_time = {} 
        self.last_image_seen_time = {}
        self.seen_images = set() 
        self.image_cache = {} 
        self.news_channels = {} 
        self.news_task = None 
        self.images_path = 'images/base'

    @commands.slash_command(name="news", description="Показывает случайную картинку")
    async def news(self, interaction: disnake.ApplicationCommandInteraction):
        config_data = load_config(interaction.guild.id)
        chosen_color = get_color_from_config(config_data)
        user_id = interaction.author.id

        if not os.path.exists(self.images_path):
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Папка с изображениями не найдена!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        images = [f for f in os.listdir(self.images_path) if os.path.isfile(os.path.join(self.images_path, f))]

        if not images:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} В папке нет изображений!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        last_sent_time = self.last_image_sent_time.get(user_id)
        if last_sent_time is not None and time.time() - last_sent_time < 43200:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Вы уже забрали свою карточку :(!\nНо завтра вы снова сможете забрать ещё одну карточку :)!",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        connection = sqlite3.connect(f'utils/cache/database/{interaction.guild_id}.db')
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM seen_images WHERE user_id = ?", (user_id,))
        total_seen_images = cursor.fetchone()[0] + 1

        while True:
            image = random.choice(images)
            if image not in self.seen_images:
                break

        self.seen_images.add(image)

        cursor.execute("INSERT INTO seen_images (user_id, image) VALUES (?, ?)", (user_id, image))
        connection.commit()

        embed = disnake.Embed(
            title="", 
            description="", 
            color=chosen_color
        )

        embed.set_image(url=f"attachment://{image}")

        embed.add_field(name="Собрано карточек:", value=f"{total_seen_images} из {len(images)}", inline=False)

        embed.add_field(name="", value=f"Посмотреть доступные карточки: </info_news:1289624166021992461>", inline=False)        

        await interaction.response.send_message(embed=embed, file=disnake.File(os.path.join(self.images_path, image)))

        amount = 25000

        cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, user_id))
        connection.commit()

        self.last_image_sent_time[user_id] = time.time()

        self.news_channels[interaction.guild.id] = interaction.channel

        connection.close()
        
    async def send_news(self):
        while True:
            for guild_id, channel in self.news_channels.items():
                config_data = load_config(guild_id)
                chosen_color = get_color_from_config(config_data)
                user_id = channel.id 

                if not os.path.exists(self.images_path):
                    embed = disnake.Embed(
                        title="Ошибка при попытке использовать команду",
                        description=f"{base['ICON_PERMISSION']} Папка с изображениями не найдена!",
                        color=chosen_color
                    )
                    await channel.send(embed=embed)
                    continue

                images = [f for f in os.listdir(self.images_path) if os.path.isfile(os.path.join(self.images_path, f))]

                if not images:
                    embed = disnake.Embed(
                        title="Ошибка при попытке использовать команду",
                        description=f"{base['ICON_PERMISSION']} В папке нет изображений!",
                        color=chosen_color
                    )
                    await channel.send(embed=embed)
                    continue

                last_sent_time = self.last_image_sent_time.get(user_id)
                if last_sent_time is not None and time.time() - last_sent_time < 60:
                    continue

                connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
                cursor = connection.cursor()

                cursor.execute("SELECT COUNT(*) FROM seen_images WHERE user_id = ?", (user_id,))
                total_seen_images = cursor.fetchone()[0]

                while True:
                    image = random.choice(images)
                    if image not in self.seen_images:
                        break

                self.seen_images.add(image)

                cursor.execute("INSERT INTO seen_images (user_id, image) VALUES (?, ?)", (user_id, image))
                connection.commit()

                embed = disnake.Embed(
                    title="", 
                    description="", 
                    color=chosen_color
                )

                embed.set_image(url=f"attachment://{image}")

                embed = disnake.Embed(
                    title="",
                    description="",
                    color=chosen_color
                )

                embed.set_image(url=f"attachment://{image}")
                embed.add_field(name=f"Коллекционные карточки: {total_seen_images} из {len(images)}", value=f"", inline=False)
                embed.add_field(name=f"", value=f"Продать/подарить карточку: </trade_card:1289624166021992462>\nПосмотреть доступные карточки: </info_news:1289624166021992461>", inline=False)
                await channel.send(embed=embed, file=disnake.File(os.path.join(self.images_path, image)))

                self.last_image_sent_time[user_id] = time.time()

                connection.close()

            await disnake.utils.sleep(60)

def setup(bot):
    bot.loop.create_task(bot.get_cog("news").send_news())    