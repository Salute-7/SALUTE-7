import os
import json
import sqlite3
import disnake
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

def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}

async def check_permissions(guild_id, ctx):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    admin_users = load_admin_users()
    
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

    is_admin = ctx.author.guild_permissions.administrator
    is_owner = str(ctx.author.id) in admin_users
    has_role = any(
        role.id in ROLE_IDS_ADMIN or role.id in ROLE_IDS_MODERATOR 
        for role in ctx.author.roles)
    if not has_role and not is_admin and not is_owner:  
        await ctx.send(embed=create_embed(
            "Ошибка при попытке использовать команду",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

class take(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

 
    @bot.slash_command(name='take', description='Убавить указанную сумму от основного баланса.')
    async def take(self, ctx, user: disnake.Member = None, amount: int = None):
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        if not await check_permissions(guild_id, ctx):
            return
        
        if user is None:
            user = ctx.author

        if amount is None:
            amount = 1000000

        if amount < 1:
            await ctx.send(embed=create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} Укажите сумму не меньше 1.",
                color=chosen_color),
                           ephemeral=True)
            return

        try:
            amount = int(amount)  
        except ValueError:
            await ctx.send(embed=create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} Укажите сумму числом.",
                color=chosen_color),
                           ephemeral=True)
            return

        formatted = f"{amount:,}".replace(',', '.')

        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE users SET cash = cash - {} WHERE id = {}".format(
                amount, user.id))
        connection.commit()

        embed = disnake.Embed(
            description=f"",
            color=chosen_color,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed = create_embed(f"**Баланс пользователя {user.display_name}**",
                             f"\n**:coin: Новый баланс:**"
                             f"\n```-{formatted}₽```",
                             color=chosen_color)
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)

        log_embed = disnake.Embed(
            description=f"",
            color=chosen_color,
        )
        log_embed = create_embed(
            f"**Баланс пользователя {user.display_name}**",
            f"\n**:coin: Новый баланс:**"
            f"\n```-{formatted}₽```",
            color=chosen_color)

        ROLE_IDS_MODERATOR = [int(role_id) for role_id in settings.get('ROLE_MODER', [])if isinstance(role_id, str)]
        ROLE_IDS_ADMIN = [int(role_id) for role_id in settings.get('ROLE_ADMIN', [])if isinstance(role_id, str)]

        is_tech_specialist = any(role.id in ROLE_IDS_ADMIN
                                 for role in ctx.author.roles)
        is_moderator = any(role.id in ROLE_IDS_MODERATOR
                           for role in ctx.author.roles)

        if ctx.author == ctx.guild.owner:
            log_embed.add_field(
                name=
                f"Действие для:\n{base['ICON_POLZOV']} **{user.display_name} ({user.id})**\nБаланс был изменён:",
                value=
                f"\n{base['ICON_OSNOVA']} **Основатель сервера {ctx.author.display_name} ({ctx.author.id})**",
                inline=False)
        elif is_tech_specialist:
            log_embed.add_field(
                name=
                f"Действие для:\n{base['ICON_POLZOV']} **{user.display_name} ({user.id})**\nБаланс был изменён:",
                value=
                f"\n{base['ICON_ADMIN']} **Администратор сервера {ctx.author.display_name} ({ctx.author.id})**",
                inline=False)
        elif is_moderator:
            log_embed.add_field(
                name=
                f"Действие для:\n{base['ICON_POLZOV']} **{user.display_name} ({user.id})**\nБаланс был изменён:",
                value=
                f"\n{base['ICON_MODER']} **Модератор сервера {ctx.author.display_name} ({ctx.author.id})**",
                inline=False)

        log_embed.set_thumbnail(url=user.display_avatar.url)

        CHANNEL_CANAl_ID = settings.get('ADMIN_LOGS', [])

        if CHANNEL_CANAl_ID:  
            admin_channel = ctx.guild.get_channel(int(CHANNEL_CANAl_ID[0]))
            if admin_channel is not None:
                await admin_channel.send(embed=log_embed)