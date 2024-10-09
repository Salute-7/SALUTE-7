import os
import re
import json
import sqlite3
import disnake
import traceback
import asyncio
from utils.base.config_data import config_data
from utils.base.colors import colors
from disnake.ext import commands

from Commands.Admin.clear import clear
from Commands.Economy.pay import pay
from Commands.Economy.set import setcog
from Commands.Economy.add import add
from Commands.Economy.take import take
from Commands.Economy.reward import reward
from Commands.Game.duel import duel
from Commands.Other.help import helpcog
from Commands.Shop.sellcar import sellcar
from Commands.Shop.buy_car import buy_car
from Commands.Shop.sellhome import sellhome
from Commands.Shop.buy_home import buy_home
from Commands.Statistica.profile import profile
from Commands.Statistica.top_active import top_active
from Commands.Statistica.top_balance import top_balance
from Commands.System.set_role_id import set_role_id
from Commands.System.set_logs import set_logs
from Commands.System.set_pay import set_pay
from Commands.System.set_moderator import set_moderator
from Commands.System.set_administrator import set_administrator
from Commands.System.set_color import set_color
from Commands.System.settings import settings
from Commands.System.set_global_chat import set_global_chat
from Commands.System.set_welcome import set_welcome_channel

bot = commands.InteractionBot(intents=disnake.Intents.all())

bot.add_cog(set_welcome_channel(bot))
bot.add_cog(set_global_chat(bot))
bot.add_cog(set_role_id(bot))
bot.add_cog(set_logs(bot))
bot.add_cog(set_pay(bot))
bot.add_cog(set_moderator(bot))
bot.add_cog(set_administrator(bot))
bot.add_cog(set_color(bot))
bot.add_cog(clear(bot))
bot.add_cog(settings(bot))
bot.add_cog(helpcog(bot))
bot.add_cog(reward(bot))
bot.add_cog(duel(bot))
bot.add_cog(setcog(bot))
bot.add_cog(add(bot))
bot.add_cog(pay(bot))
bot.add_cog(take(bot))
bot.add_cog(profile(bot))
bot.add_cog(sellcar(bot))
bot.add_cog(buy_car(bot))
bot.add_cog(sellhome(bot))
bot.add_cog(buy_home(bot))
bot.add_cog(top_active(bot))
bot.add_cog(top_balance(bot))

connection = sqlite3.connect(f'utils/cache/database/main.db')
cursor = connection.cursor()

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

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'orange')
    return colors.get(color_choice.lower(), disnake.Color.orange())

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed

def create_server_data(guild):
    guild_id = guild.id
    db_path = os.path.join('utils/cache/database', f'{guild_id}.db')
    config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
    print(f"Создан файл с хранилищем данных для сервера {guild.name} (ID: {guild_id})")

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            name TEXT,
            id INT PRIMARY KEY,
            cash BIGINT,
            used_promocodes TEXT,
            freeze_until DATETIME
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS settings (
            interest_rate INTEGER
        )""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            car_name TEXT NOT NULL,
            car_image_url TEXT NOT NULL,
            purchase_date DATETIME NOT NULL,
            purchase_price INTEGER NOT NULL
        )""")    

        cursor.execute("""CREATE TABLE IF NOT EXISTS home (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            home_name TEXT NOT NULL,
            home_image_url TEXT NOT NULL,
            home_buy_date DATETIME NOT NULL,
            home_price INTEGER NOT NULL,
            home_info INTEGER NOT NULL
        )""")            

        cursor.execute(
            "INSERT OR IGNORE INTO settings (interest_rate) VALUES (15)")
        db.commit()

    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        for member in guild.members:
            cursor.execute(
                "INSERT OR IGNORE INTO users (name, id, cash, used_promocodes) VALUES (?, ?, ?, ?)",
                (str(member), member.id, 0, ''))
        db.commit()     

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id

    # Загружаем настройки конфигурации
    settings = load_config(guild_id)
    channel_id = settings.get("GLOBAL", None)
    chosen_color = get_color_from_config(settings)

    server_name = message.guild.name

    if channel_id:
        global_channel = bot.get_channel(channel_id)

        # Проверка, что сообщение отправлено в правильном канале
        if message.channel.id == channel_id and global_channel:
            # НЕ удаляем сообщение сразу!

            # Обработка текста сообщения
            content = message.content[0] + message.content[1:] if len(message.content) > 1 else message.content

            # Обработка вложений (фото, стикеры, файлы)
            attachments = message.attachments

            # Флаг, чтобы определить, нужно ли удалять сообщение
            delete_message = False  # Начальное значение - True

            for guild in bot.guilds:
                other_settings = load_config(guild.id)
                other_channel_id = other_settings.get("GLOBAL", None)

                if other_channel_id:
                    other_global_channel = bot.get_channel(other_channel_id)
                    if other_global_channel:
                        embed = disnake.Embed(
                            title=f"{server_name}",
                            description=f"*{message.author.display_name}: {content}*",
                            color=chosen_color, # Добавляем временную метку
                            timestamp=message.created_at
                        )

                        embed.set_footer(text=f"Guild ID: {guild_id}",)

                        if attachments:
                            # Проверяем, есть ли изображения, MP3 или GIF-файлы
                            allowed_types = ["image", "audio/mpeg", "image/gif"]
                            if any(attachment.content_type.startswith(t) for t in allowed_types for attachment in attachments):
                                # Проверяем, есть ли изображения или GIF
                                if any(attachment.content_type.startswith("image") for attachment in attachments):
                                    # Берем первое изображение из вложений
                                    image_attachment = next(attachment for attachment in attachments if attachment.content_type.startswith("image"))
                                    embed.set_image(url=image_attachment.url)

                                # Проверяем, есть ли MP3
                                if any(attachment.content_type.startswith("audio/mpeg") for attachment in attachments):
                                    for attachment in attachments:
                                        if attachment.content_type.startswith("audio/mpeg"):
                                            # Используйте сервис для превью MP3 (например, https://www.youtube.com/watch?v=v-u-d-k9L_M)
                                            embed.add_field(name=f"ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤﾠ",
                                                            value=f"Файл: MP3. [Открыть в браузере?]({attachment.url})",
                                                            inline=True)

                        else:
                            embed.add_field(name=f"ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤﾠ",
                                            value=f"",
                                            inline=True)

                        embed.set_thumbnail(url=message.guild.icon.url if message.guild.icon else None)

                        await other_global_channel.send(embed=embed)

            try:
                await asyncio.sleep(1)
                await message.delete()
            except disnake.errors.NotFound:
                print(f"Сообщение с ID {message.id} не найдено или уже удалено.")



@bot.event
async def on_ready(): 

    recreated_servers = 0  # Счётчик пересозданий
    total_registered_users = 0  # Счётчик зарегистрированных пользователей
    total_members = 0  # Счётчик участников на всех серверах

    for guild in bot.guilds:
        guild_id = guild.id
        config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
        db_path = os.path.join('utils/cache/database', f'{guild_id}.db')

        # Проверка на существование конфигурации и базы данных
        config_exists = os.path.exists(config_path)
        db_exists = os.path.exists(db_path)

        if not config_exists or not db_exists:
            create_server_data(guild)  # Ваша функция для создания данных сервера
            recreated_servers += 1  # Увеличиваем счётчик пересозданий
            continue  # Переходим к следующему серверу

        # Обработка пользователей в базе данных
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()

            # Получаем список всех зарегистрированных пользователей на текущем сервере
            registered_users = {row[0] for row in cursor.execute("SELECT id FROM users").fetchall()}
            new_users_count = 0  # Счётчик новых пользователей для текущего сервера

            # Проверяем каждого участника сервера
            for member in guild.members:
                if member.id not in registered_users:  # Если участник не зарегистрирован
                    cursor.execute(
                        "INSERT INTO users (name, id, cash, used_promocodes) VALUES (?, ?, ?, ?)",
                        (str(member), member.id, 0, '')
                    )
                    new_users_count += 1  # Увеличиваем счётчик новых пользователей

            db.commit()
            
            total_members += len(guild.members)  # Увеличиваем общий счётчик участников

    total_guilds = len(bot.guilds)  # Общее количество серверов

    print(f"\nБот запущен как {bot.user}.\n"
          f"Бот используется на {total_guilds} серверах.\n"
          f"Пересоздание произошло на {recreated_servers} серверах.\n"
          f"Всего зарегистрировано новых пользователей: {total_registered_users}.\n"
          f"Общее количество участников на всех серверах: {total_members}.\n")

@bot.event
async def on_guild_join(guild):
    create_server_data(guild)
    print(f'Бот присоединился к новому серверу: {guild.name} (ID: {guild.id})')

    total_guilds = len(bot.guilds)
    total_members = sum(guild.member_count for guild in bot.guilds)

    first_channel = next((channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages), None)
    
    if first_channel:
        embed = disnake.Embed(
            title=f"🎉 Добро пожаловать на сервер {guild.name}! 🎉",
            description=(
                f"Привет! Я - **Салют**, приложение для **вашего сервера!**\n\n"
                "✨ **Спасибо, что добавили меня!** ✨\n\n"
                "• 🔧 Чтобы начать пользоваться мной, пожалуйста, настройте мои параметры с помощью команды </settings:1283133506297266344>\n\n"
                "• ❗️ Без настроек я не смогу работать корректно.\n\n"
                "🛠️ Нашли ошибку? [Сообщите мне!](https://discord.com/users/936292219378348033)\n\n"
                f"🌐 Я сейчас используюсь на **{total_guilds} серверах** с **{total_members} участниками.**"
            ),
            color=disnake.Color.from_rgb(0, 255, 255)
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await first_channel.send(embed=embed)

directory = 'utils/cache/configs'
if os.path.exists(directory):
    count = len(os.listdir(directory))
    print(f"Найдено {count} файлов в папке {directory}")  

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    # Проверка включенности приветствия
    if not settings.get('WELCOME_ENABLED', True):
        return

    db_path = os.path.join('utils/cache/database', f'{guild_id}.db')

    with sqlite3.connect(db_path) as db:
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM users WHERE id = ?", (member.id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            print(f"Зарегистрирован пользователь {member.display_name} [{member.name}] ({member.id}) для сообщества {member.guild.name} ({member.guild.id})")
            cursor.execute("INSERT INTO users (name, id, cash, used_promocodes) VALUES (?, ?, ?, ?)", (member.display_name, member.id, 0, ''))

    ROLE_ID = settings.get('ROLE_ID')
    if ROLE_ID:
        role = member.guild.get_role(int(ROLE_ID))  
        if role:
            try:
                await member.add_roles(role)
            except disnake.HTTPException as e:
                print(f"Не удалось добавить роль: {e}")

    # Создание красивого приветствия с дополнительной информацией
    embed = disnake.Embed(
        title=f"Добро пожаловать, {member.display_name}!",
        description=f"Мы рады видеть вас на {member.guild.name}! 🎉\n\n"
                    f"Ваше имя: {member.display_name}\n"
                    f"User ID: {member.id}\n"
                    f"Аккаунт создан: {member.created_at.strftime('%d.%m.%Y %H:%M:%S')}\n\n",
        color=chosen_color
    )

    # Добавляем аватарку участника
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    # Добавляем дополнительные поля
    embed.add_field(name="Информация о сервере:", value=f"👥 Пользователей: {len(member.guild.members)}", inline=True)

    # Отправляем приветствие в установленный канал для приветствий, если он есть
    welcome_channel_id = settings.get('WELCOME_CHANNEL')

    if welcome_channel_id:
        welcome_channel = member.guild.get_channel(welcome_channel_id)
        if welcome_channel and hasattr(welcome_channel, 'permissions_for'):
            if welcome_channel.permissions_for(member.guild.me).send_messages:
                await welcome_channel.send(embed=embed)
            else:
                # Если у бота нет прав, отправляем в любой доступный текстовый канал
                fallback_channel = next((ch for ch in member.guild.text_channels if ch.permissions_for(member.guild.me).send_messages), None)
                if fallback_channel:
                    await fallback_channel.send(embed=embed)
        else:
            # Если канал не найден, отправляем в любой доступный текстовый канал
            fallback_channel = next((ch for ch in member.guild.text_channels if ch.permissions_for(member.guild.me).send_messages), None)
            if fallback_channel:
                await fallback_channel.send(embed=embed)
    else:
        # Если канал для приветствий не установлен, отправляем в любой доступный текстовый канал
        fallback_channel = next((ch for ch in member.guild.text_channels if ch.permissions_for(member.guild.me).send_messages), None)
        if fallback_channel:
            await fallback_channel.send(embed=embed)

@bot.event
async def on_slash_command_error(ctx, error):
    guild_id = ctx.guild.id if ctx.guild else "Неизвестный сервер"
    guild_name = ctx.guild.name if ctx.guild else "Неизвестный сервер"
    settings = load_config(guild_id) 
    chosen_color = get_color_from_config(settings)

    tb_str = traceback.format_exception(type(error), error, error.__traceback__)
    error_line = tb_str[-1] if tb_str else "Неизвестная ошибка"

    if isinstance(error, commands.CommandInvokeError):
        original = error.original
        if isinstance(original, disnake.Forbidden):
            await ctx.send(embed=create_embed(
                "",
                f"{base['ICON_PERMISSION']} У меня нет прав для выполнения этой команды. Пожалуйста, пригласите меня заново с необходимыми правами.",
                color=disnake.Color.red()),
                ephemeral=True)
        else:
            try:
                await ctx.send(embed=create_embed(
                    "Упс... Вы столкнулись с ошибкой, не паникуйте!",
                    f"\n"
                    f"\nЕсть ряд причин, по которым ошибка могла произойти,\n постарайтесь набраться терпения и опробовать их все, пожалуйста."
                    f"\n"
                    f"\n**Попробуйте основные исправления**\n"
                    f"\nОбновите приложение Discord: Возможно, вы получаете ошибку “Сбой при взаимодействии” из-за устаревшего или глючащего приложения Discord. Попробуйте обновить приложение Discord на своем компьютере, чтобы узнать, поможет ли это.\nПроверьте, не работает ли Discord: Для таких служб, как Discord, нет ничего необычного в том, что время от времени сервер отключается. Следовательно, рекомендуется проверить состояние сервера Discord, прежде чем предпринимать другие действия.\nОтключите прокси-сервер или VPN: Использование прокси-сервера или VPN иногда может вызывать проблемы с подключением к серверам Discord. Чтобы исправить это, попробуйте отключить любой прокси-сервер или VPN-соединение на вашем ПК."
                    f"\n"
                    f"\n**Попробуйте дополнительные подсказки**"
                    f"\n"
                    f"\n1: заполните все поля в /settings"
                    f"\n2: проверьте, отключено ли приложение"
                    f"\n3: проверьте разрешения бота и настройки команд"
                    f"\n4: зайдите в настройки и отключите аппаратное ускорение"
                    f"\n5: попробуйте очистить кэш приложения"
                    f"\n6: убедитесь, правильно ли Вы вводите команду и её аргументы"
                    f"\n7: дайте приложению немного «отдохнуть», возможно, это поможет"
                    f"\n8: свяжитесь с разработчиками приложения, возможно, ошибка на их стороне",
                    color=chosen_color),
                    ephemeral=True)
                print(f"Ошибка при выполнении команды на сервере {guild_name}: {error_line}")
            except disnake.HTTPException as e:
                print(f"Ошибка при отправке сообщения: {e}")
    else:
        await ctx.send(embed=create_embed(
            "",
            f"{base['ICON_PERMISSION']} Попробуйте заполнить /settings.",
            color=disnake.Color.red()),
            ephemeral=True)
        print(f"Ошибка slash-команды на сервере {guild_name}: {error}")

base = load_base()
bot_run = bot.run(base['TOKEN'])

