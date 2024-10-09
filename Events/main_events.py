import os
import json
import disnake
import tqdm
import requests
import asyncio
import re
import time
from colorama import Fore, Style
import sqlite3
from utils.base.config_data import config_data
from utils.base.colors import colors
from disnake.ext import commands

bot = commands.InteractionBot(intents=disnake.Intents.all())

def load_base():
    config_path = os.path.join('utils/global', f'main.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
base=load_base()

def load_config(guild_id):
    config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            if "WEBHOOK" not in config:
                config["WEBHOOK"] = ""
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
            return config
    else:
        config = {"WEBHOOK": ""}
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return config

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed

def load_vip_users():
    try:
        with open('utils/global/vip_users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}

def load_blocked_users():
    config_path = os.path.join('utils/global/blocked.json')
    try:
        with open(config_path, 'r') as f:
            data = json.load(f) 
            return {int(user['id']): user['reason'] for user in data['blocked_users']} 
    except FileNotFoundError:
        return {}

def check_if_user_blocked(user_id):
    blocked_users = load_blocked_users()
    if user_id in blocked_users:
        return True, blocked_users[user_id]
    return False, None

def load_blocked_guilds():
    config_path = os.path.join('utils/global/blocked.json')
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            return {int(guild['id']): guild['reason'] for guild in data['blocked_guilds']}
    except FileNotFoundError:
        return {}

def check_if_guild_blocked(guild_id):
    blocked_guilds = load_blocked_guilds()
    if guild_id in blocked_guilds:
        return True, blocked_guilds[guild_id]
    return False, None

async def check_if_blocked(user_id, guild_id):
    is_user_blocked, user_reason = check_if_user_blocked(user_id)
    if is_user_blocked:
        return True, user_reason
    is_guild_blocked, guild_reason = check_if_guild_blocked(guild_id)
    if is_guild_blocked:
        return True, guild_reason

    return False, None

def create_server_data(guild):
    guild_id = guild.id
    db_path = os.path.join('utils/cache/database', f'{guild_id}.db')
    config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
    tasks = [
        "Создание базы данных",
        "Создание таблицы пользователей",
        "Создание таблицы просмотренных изображений",
        "Создание таблицы покупок",
        "Создание таблицы домов",
        "Создание таблицы репутации",
        "Создание таблицы действий",
        "Вставка начальных данных",
        "Создание конфигурационного файла",
        "Создание завершено",
    ]

    with tqdm.tqdm(
        total=len(tasks),
        desc=Fore.YELLOW + "Создание данных сервера" + Style.RESET_ALL, 
        bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} \033[0m \033[31m[{elapsed}<{remaining}, {rate_fmt} задача/s]\033[0m',
        colour="#028000",  
    ) as pbar:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание базы данных" + Style.RESET_ALL) 
            pbar.update(1) 

            cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                name TEXT,
                id INT PRIMARY KEY,
                cash BIGINT,
                used_promocodes TEXT                       
            )""")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание таблицы пользователей" + Style.RESET_ALL)   
            pbar.update(1) 
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS seen_images (
                user_id INTEGER,
                image INTEGER
            )""")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание таблицы просмотренных изображений" + Style.RESET_ALL) 
            pbar.update(1)  
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                car_name TEXT NOT NULL,
                car_image_url TEXT NOT NULL,
                purchase_date DATETIME NOT NULL,
                purchase_price INTEGER NOT NULL
            )""")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание таблицы покупок" + Style.RESET_ALL) 
            pbar.update(1)  
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS home (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                home_name TEXT NOT NULL,
                home_image_url TEXT NOT NULL,
                home_buy_date DATETIME NOT NULL,
                home_price INTEGER NOT NULL,
                home_info INTEGER NOT NULL
            )""")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание таблицы домов" + Style.RESET_ALL) 
            pbar.update(1)  
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS reputation (
                user_id INTEGER PRIMARY KEY,
                reputation INTEGER
            )""")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание таблицы репутации" + Style.RESET_ALL) 
            pbar.update(1)
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS actions (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                action TEXT
            )""")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание таблицы действий" + Style.RESET_ALL) 
            pbar.update(1)  
            
            cursor.execute(
                "INSERT OR IGNORE INTO seen_images (image) VALUES (0)")
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Вставка начальных данных" + Style.RESET_ALL) 
            pbar.update(1)  

        with open(config_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)
            pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание конфигурационного файла" + Style.RESET_ALL) 
            pbar.update(1)  
        pbar.set_description(Fore.YELLOW + f"Создание файлов для сервера {guild.name}: Создание завершено" + Style.RESET_ALL)         
        pbar.update(1)

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        for member in guild.members:
            cursor.execute(
                "INSERT OR IGNORE INTO users (name, id, cash, used_promocodes) VALUES (?, ?, ?, ?)",
                (str(member), member.id, 0, ''))
        db.commit()  

def create_webhook_for_guild(self, guild):
    settings = load_config(guild.id)
    global_channel_id = settings.get("GLOBAL")
    if global_channel_id and global_channel_id.isdigit():
        global_channel = self.bot.get_channel(int(global_channel_id))
        if global_channel:
            try:
                webhook = disnake.utils.get(global_channel.webhooks, name="SALUTE-GlobalChat") 
                if not webhook:
                    webhook = global_channel.create_webhook(name="SALUTE-GlobalChat")
                self.webhooks[guild.id] = webhook.url
            except Exception as e:
                pass

async def check_permissions(guild_id, ctx):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    admin_users = load_admin_users()

    is_admin = ctx.author.guild_permissions.administrator
    is_owner = str(ctx.author.id) in admin_users
    if not is_admin and not is_owner:  
        await ctx.send(embed=create_embed(
            "Ошибка при попытке использовать команду:",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

start_time = time.time()
class events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_messages = {}
        self.webhooks = {}

        for guild in self.bot.guilds:
            self.create_webhook_for_guild(guild)

    @commands.slash_command(description="Если возникнут ошибки, попробуйте прописать эту команду.")
    async def restart(self, interaction: disnake.ApplicationCommandInteraction):
        guild = interaction.guild 
        guild_id = guild.id 
        config_data = load_config(guild_id) 
        chosen_color = get_color_from_config(config_data)

        if not await check_permissions(guild, interaction):  
            return
        create_server_data(guild) 

        embed = disnake.Embed(
            title="Процесс пересоздания файлов запущен...",
            description="Начинаю пересоздание. Пожалуйста, подождите.",
            color=chosen_color
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return 

        if message.guild is None:
            return  
        if message.guild not in self.bot.guilds:
            return 

        config_data = load_config(message.guild.id)
        chosen_color = get_color_from_config(config_data)
        guild_id = message.guild.id

        global_channel_id = config_data.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == message.channel.id:
            for other_guild in self.bot.guilds:
                if other_guild.id == message.guild.id:
                    continue  

                other_config_data = load_config(other_guild.id)
                other_channel_id = other_config_data.get("GLOBAL", None)

                if other_channel_id:
                    other_global_channel = self.bot.get_channel(int(other_channel_id))

                    if other_global_channel:
                        if message.id in self.sent_messages.get(other_global_channel.id, set()): 
                            continue 

                        user_id_to_check = message.author.id
                        is_blocked, reason = await check_if_blocked(user_id_to_check, guild_id) 
                        if is_blocked:
                            await message.delete()
                            embed = create_embed(  
                                "Ошибка при отправке сообщения в глобальный чат:",
                                f"Вы не можете использовать глобальный чат, так как вы или ваша гильдия заблокированы.",
                                color=chosen_color)

                            embed.add_field(
                                name=f"Причина:",
                                value=f"{reason}",
                                inline=True,
                            )

                            await message.author.send(embed=embed)
                            return

                        if re.search(r'@everyone|@here', message.content):
                            await message.delete()
                            embed = create_embed(
                                "Ошибка при отправке сообщения в глобальный чат:",
                                f"Упоминания @everyone и @here запрещены в глобальном чате.",
                                color=chosen_color
                            )
                            await message.author.send(embed=embed)
                            return

                        if re.search(r'https://discord.gg/[a-zA-Z0-9]+', message.content):
                            await message.delete()
                            embed = create_embed(
                                "Ошибка при отправке сообщения в глобальный чат:",
                                f"Ссылки на Discord сервера и прочие ресурсы запрещены в глобальном чате.",
                                color=chosen_color
                            )
                            await message.author.send(embed=embed)
                            return

                        webhook = self.webhooks.get(other_global_channel.id)
                        if not webhook:
                            webhooks = await other_global_channel.webhooks()
                            for wh in webhooks:
                                if wh.name == "GlobalChat":
                                    webhook = wh
                                    break
                            if not webhook:
                                webhook = await other_global_channel.create_webhook(name="GlobalChat")
                            self.webhooks[other_global_channel.id] = webhook

                        if message.reference:
                            referenced_message = await message.channel.fetch_message(message.reference.message_id)
                            message_content = f"{message.content}\n> {referenced_message.author.display_name} сказал(-а): {referenced_message.content}"
                        else:
                            message_content = message.content

                        payload = {
                            'username': f"{message.author.display_name} ({message.author.id}) [{guild_id}]",
                            'content': message_content,
                            'avatar_url': message.author.avatar.url if message.author.avatar else None,
                        }

                        if message.attachments:
                            files = []
                            for attachment in message.attachments:
                                file_path = await attachment.to_file()
                                files.append((attachment.filename, file_path.fp))
                            response = requests.post(webhook.url, data=payload, files=files)
                        else:
                            response = requests.post(webhook.url, json=payload)

                        if other_global_channel.id not in self.sent_messages:
                            self.sent_messages[other_global_channel.id] = set()
                        self.sent_messages[other_global_channel.id].add(message.id)

        else:
            return                                         

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        config_path = os.path.join('utils/cache/configs', f'{guild.id}.json')

        config_exists = os.path.exists(config_path)

        if not config_exists:
            create_server_data(guild)  

        total_guilds = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)

        first_channel = next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages), None)
        
        if first_channel:
            embed = disnake.Embed(
                title=f"Добро пожаловать на сервер {guild.name}! 🎉",
                description=(
                    f"Привет! Я - **Салют**, приложение для **вашего сервера!**\n\n"
                    "✨ **Спасибо, что добавили меня!** ✨\n\n"
                    "• 🔧 Чтобы начать пользоваться мной, пожалуйста, настройте мои параметры с помощью команды: </settings:1283133506297266344>\n\n"
                    "• 🌍 Если вы собираетесь добавить глобальный чат, для общения с другими серверами, используйте: </set_global_chat:1290700842361421927>\n\n"
                    "• ❗️ Без настроек я не смогу работать корректно.\n\n"
                    "> 🛠️ Нашли ошибку? [Сообщите мне!](https://disnake.com/users/936292219378348033)\n"
                    "> ✨ Оставьте отзыв! [top.gg](https://top.gg/bot/1223591886128939090) [bots.gg](https://bots.server-discord.com/1223591886128939090) [boti.cord~](https://boticord.top/bot/1223591886128939090)\n\n"
                    f"🌐 Я сейчас нахожусь на **{total_guilds} серверах** с **{total_members} участниками.**"
                ),
                color=disnake.Color.from_rgb(0, 255, 255)
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            await first_channel.send(embed=embed)

    directory = 'utils/cache/configs'
    if os.path.exists(directory):
        count = len(os.listdir(directory))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        db_path = os.path.join('utils/cache/database', f'{guild_id}.db')

        try:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute("SELECT 1 FROM users WHERE id = ?", (member.id,))
                user_exists = cursor.fetchone()

            if not user_exists:
                cursor.execute(
                "INSERT INTO users (name, id, cash, used_promocodes) VALUES (?, ?, ?, ?)",
                (member.display_name, member.id, 0, '')
                )
            else:
                ROLE_ID = settings.get('ROLE_ID')
                if ROLE_ID:
                    role = member.guild.get_role(int(ROLE_ID))
                    if role:
                        try:
                            await member.add_roles(role)
                        except disnake.HTTPException as e:
                            print(f"Ошибка при добавлении роли: {e}")
                    else:
                        print(f"Роль с ID {ROLE_ID} не найдена.")

        except Exception as e:
            print(f"Ошибка при работе с базой данных: {e}")

        embed = disnake.Embed(
            title=f"Добро пожаловать, {member.display_name}!",
            description=f"Мы рады видеть вас на {member.guild.name}! 🎉\n\n"
                        f"Имя: [{member.display_name}](https://discord.com/users/{member.id})\n"
                        f"UID: {member.id}\n"
                        f"Создан: {member.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n\n",
            color=chosen_color
        )

        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Информация о сервере:", value=f"👥 Пользователей: {len(member.guild.members)}", inline=True)

        CHANNEL_CANAl_ID = settings.get('WELCOME_CHANNEL', "")

        if CHANNEL_CANAl_ID:
            admin_channel = member.guild.get_channel(int(CHANNEL_CANAl_ID))
            if admin_channel is not None:
                await admin_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = member.guild.id
        settings = load_config(guild_id) 
        chosen_color = get_color_from_config(settings) 

        embed = disnake.Embed(
            title=f"До новых встреч, {member.display_name}!",
            description=f"Пользователь покинул {member.guild.name}! ⛔️\n\n"
                        f"Имя: [{member.display_name}](https://discord.com/users/{member.id})\n"
                        f"UID: {member.id}\n"
                        f"Создан: {member.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n\n",
            color=chosen_color
        )
        embed.set_thumbnail(url=member.display_avatar.url) 

        embed.add_field(name="Информация о сервере:", value=f"👥 Пользователей: {len(member.guild.members)}", inline=True)

        CHANNEL_CANAl_ID = settings.get('WELCOME_CHANNEL', "")

        if CHANNEL_CANAl_ID:
            admin_channel = member.guild.get_channel(int(CHANNEL_CANAl_ID))
            if admin_channel is not None:
                await admin_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        recreated_servers = 0 

        with tqdm.tqdm(
            total=len(self.bot.guilds),
            desc=Fore.YELLOW + "Загрузка серверов" + Style.RESET_ALL,
            bar_format='{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} \033[0m \033[31m[{elapsed}<{remaining}, {rate_fmt} задача/s]\033[0m', 
            colour="#ff0066") as pbar:

            for guild in self.bot.guilds:
                guild_id = guild.id
                config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
                db_path = os.path.join('utils/cache/database', f'{guild_id}.db')

                config_exists = os.path.exists(config_path)
                db_exists = os.path.exists(db_path)

                if not config_exists or not db_exists:
                    create_server_data(guild)  
                    recreated_servers += 1 
                    pbar.update(1)  
                    continue  

                with sqlite3.connect(db_path) as db:
                    cursor = db.cursor()

                    registered_users = {row[0] for row in cursor.execute("SELECT id FROM users").fetchall()}
                    new_users_count = 0  

                    for member in guild.members:
                        if member.id not in registered_users:  
                            cursor.execute(
                                "INSERT INTO users (name, id, cash, used_promocodes) VALUES (?, ?, ?, ?)",
                                (str(member), member.id, 0, '')
                            )
                            new_users_count += 1
                            pbar.update(1) 

                    db.commit()

                pbar.update(1)

        await self.bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name='Запущен менее минуты назад!'))
        self.bot.loop.create_task(change_activity(self.bot))
        self.bot.loop.create_task(self.update_global_channel_descriptions())

        total_guilds = len(self.bot.guilds)

        print(
            f"\n{Fore.GREEN}Бот {Fore.CYAN}{self.bot.user}{Fore.GREEN} успешно запущен!{Style.RESET_ALL}\n"
            f"{Fore.GREEN}Используется на {Fore.CYAN}{total_guilds}{Fore.GREEN} серверах.\n"
            f"{Fore.GREEN}Файлы пересозданы на {Fore.CYAN}{recreated_servers}{Fore.GREEN} серверах.{Style.RESET_ALL}\n"
        )
    async def update_global_channel_descriptions(self):
        while True:
            global_servers = []
            for guild in self.bot.guilds:
                guild_config = load_config(guild.id)
                if guild_config and guild_config.get("GLOBAL"):
                    global_servers.append(guild.name)

            for guild in self.bot.guilds:
                guild_config = load_config(guild.id)
                if guild_config and guild_config.get("GLOBAL"):
                    global_channel = guild.get_channel(int(guild_config["GLOBAL"]))  
                    if global_channel:

                        try:
                            await global_channel.edit(topic=None) 
                        except disnake.Forbidden:
                            print(f"Нет прав на удаление описания канала {global_channel.name} на сервере {guild.name}.")

                        new_description = f"В этом канале собрались участники из {len(global_servers)} серверов! Будьте вежливы, уважайте друг друга и наслаждайтесь общением!"
                        try:
                            await global_channel.edit(topic=new_description)
                        except disnake.Forbidden:
                            print(f"Нет прав на редактирование канала {global_channel.name} на сервере {guild.name}.")

            await asyncio.sleep(60)

async def change_activity(bot):
    while True:
        total_servers = len(bot.guilds)
        total_members = sum(len(guild.members) for guild in bot.guilds)

        messages=[
            f"{total_servers} серверов | {total_members} участников | /help v{base['VERSION']}",
            f"{total_servers} серверов | {total_members} участников | /help v{base['VERSION']}",
            f"{total_servers} серверов | {total_members} участников | /help v{base['VERSION']}",
            f"{total_servers} серверов | {total_members} участников | /help v{base['VERSION']}"
        ]

        for message in messages:
            await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name=message))
            await asyncio.sleep(60)

