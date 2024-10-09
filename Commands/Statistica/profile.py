import os
import json
import math
import disnake
import requests
import asyncio
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

def load_base():
    config_path = os.path.join('utils/global', f'main.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed
base = load_base()

def load_vip_users():
    try:
        with open('utils/global/vip_users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
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

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

class profile(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @commands.slash_command(name='profile', description='Узнать текущий баланс.')
    async def balance(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        chosen_color = get_color_from_config(settings)

        try:
            if user is None:
                user = interaction.author

            global_channel_id = settings.get("GLOBAL", None)
            cursor.execute("SELECT cash FROM users WHERE id = ?", (user.id,))
            balance_info = cursor.fetchone()

            if balance_info is not None:
                balance = balance_info[0]
                balance = 0 if balance <= 0.9 else math.floor(balance)
                formatted_balance = f"{balance:,}".replace(',', '.')
            else:
                formatted_balance = "Информация отсутствует"

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

            cursor.execute("SELECT home_name, home_image_url FROM home WHERE user_id = ? ORDER BY home_price DESC", (user.id,))
            home_info = cursor.fetchone()

            if home_info:
                home_name = home_info[0]
            else:
                home_name = "-------------"

        except Exception as e:
            pass
        try:
            embed = disnake.Embed(title="", description="", color=chosen_color)

            vip_users = load_vip_users()
            admin_users = load_admin_users()
            is_blocked = load_blocked()
            user_id_str = str(user.id)

            if any(blocked_user["id"] == str(interaction.author.id) for blocked_user in is_blocked.get("blocked_users", [])):
                embed.set_author(name=f"⛔ Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)

            elif str(user_id_str) in admin_users:
                embed.set_author(name=f"🛡️ Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)

            elif str(user_id_str) in vip_users:
                embed.set_author(name=f"👑 Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)
            else:
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
                    pass
            ROLE_IDS_ADMIN = []
            for role_id in settings['ROLE_ADMIN'].split(','):
                try:
                    ROLE_IDS_ADMIN.append(int(role_id.strip()))
                except ValueError:
                    pass

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

            cursor.execute("SELECT reputation FROM reputation WHERE user_id = ?", (user.id,))
            result = cursor.fetchone()
            if result is not None:
                result = result[0]
            else:
                result = None
                
            if result == None:
                pass

            elif result == 0:
                pass

            else:
                embed.set_footer(text=f"Репутация: {result} 🔥")

            await interaction.response.send_message(embed=embed)
        except:
            embed = disnake.Embed(title="", description="", color=chosen_color)

            vip_users = load_vip_users()
            admin_users = load_admin_users()
            user_id_str = str(user.id)

            if any(blocked_user["id"] == str(user_id_str) for blocked_user in is_blocked.get("blocked_users", [])):
                embed.set_author(name=f"⛔ Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)

            elif str(user_id_str) in admin_users:
                embed.set_author(name=f"🛡️ Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)

            elif str(user_id_str) in vip_users:
                embed.set_author(name=f"👑 Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)
            else:
                embed.set_author(name=f"Ссылка на профиль",
                            url=f"https://discord.com/users/{user.id}",
                            icon_url=user.avatar.url)

            embed.add_field(
                name="",
                value=
                f"***Создан:***\n```{user.created_at.strftime('%d.%m.%Y %H:%M:%S')}```",
                inline=True)
            embed.add_field(name="", value=f"***UserID:***\n```{user.id}```", inline=True)
            for guild in self.bot.guilds:
                if user in guild.members:
                    embed.add_field(name="", value=f"***UserMention: {user.mention}***\n```{user.display_name} | @{user.name} | {user.name}#{user.discriminator}```", inline=False)
                    break 
            else:
                embed.add_field(name="", value=f"***UserMention:***\n```{user.display_name} | @{user.name} | {user.name}#{user.discriminator}```",inline=False)

            embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.response.send_message(embed=embed)
            
def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}
    
def load_blocked():
    try:
        with open('utils/global/blocked.json', 'r', encoding='utf-8') as f:
            blocked_users = json.load(f)
            return blocked_users
    except FileNotFoundError:
        return {}    