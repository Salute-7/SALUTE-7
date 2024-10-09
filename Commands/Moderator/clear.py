import os
import json
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

class clear(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @commands.slash_command(name='clear', description='Удалить сообщения.')
    async def clear(self, ctx, amount: int = None):
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        
        if not await check_permissions(guild_id, ctx):
            return

        if amount is None:
            await ctx.send(embed=create_embed("Ошибка при попытке использовать команду", f"{base['ICON_PERMISSION']} Укажите количество сообщений.", color=chosen_color), ephemeral=True)
            return

        if amount <= 0:
            await ctx.send(embed=create_embed("Ошибка при попытке использовать команду", f"{base['ICON_PERMISSION']} Количество сообщений должно быть больше 0.", color=chosen_color), ephemeral=True)
            return

        try:
            await ctx.channel.purge(limit=amount)
            await ctx.send(embed=create_embed("Действие выполнено", f"{base['APPROVED']} Удалено {amount} сообщений.", color=chosen_color), ephemeral=True)
        except disnake.Forbidden:
            await ctx.send(embed=create_embed("Ошибка при попытке использовать команду", f"{base['ICON_PERMISSION']} У меня нет прав для удаления сообщений.", color=chosen_color), ephemeral=True)
        except Exception as e:
            await ctx.send(embed=create_embed("Ошибка при попытке использовать команду", f"{base['ICON_PERMISSION']} Произошла ошибка: {str(e)}", color=chosen_color), ephemeral=True)
