import os
import json
import sqlite3
import disnake
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

async def check_permissions(guild_id, ctx):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    def get_role_ids(role_key):
        return [
            int(role_id) for role_id in settings.get(role_key, [])
            if isinstance(role_id, (str, int)) and str(role_id).strip()
        ]
    
    ROLE_IDS_MODERATOR = get_role_ids('ROLE_MODER')
    ROLE_IDS_ADMIN = get_role_ids('ROLE_ADMIN')
    is_admin = ctx.author.guild_permissions.administrator
    has_role = any(
        role.id in ROLE_IDS_ADMIN or role.id in ROLE_IDS_MODERATOR 
        for role in ctx.author.roles)
    if not has_role and not is_admin:  
        await ctx.send(embed=create_embed(
            "",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

class take(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot
        print('Файл Commands/Economy/take.py Загружен!')

 
    @bot.slash_command(name='take', description='Убавить указанную сумму от основного баланса (🎓)')
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
                "",
                f"{base['ICON_PERMISSION']} Укажите сумму не меньше 1",
                color=chosen_color),
                           ephemeral=True)
            return

        try:
            amount = int(amount)  
        except ValueError:
            await ctx.send(embed=create_embed(
                "",
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

        admin_channel = ctx.guild.get_channel(int(CHANNEL_CANAl_ID))

        if admin_channel is None:
            return

        message = await admin_channel.send(embed=log_embed)       