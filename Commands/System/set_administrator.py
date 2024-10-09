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

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed
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

class set_administrator(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @bot.slash_command(name="set_administrator", description="Изменить ID ролей (Администратор)")
    async def set_administrator_id(ctx, new_role: disnake.Role = None, delete: bool = False):
        guild_id = ctx.guild.id
        if not await check_permissions(guild_id, ctx):
            return

        guild_id = ctx.guild.id
        config_data = load_config(guild_id)
        chosen_color = get_color_from_config(config_data)

        if delete:
            if 'ROLE_ADMIN' in config_data:
                config_data['ROLE_ADMIN'] = "" 
                with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
                    json.dump(config_data, config_file, indent=4)
                
                embed = disnake.Embed(
                    title="Действие выполнено",
                    description=f"{base['APPROVED']} Значени adm-role успешно отключёно.",
                    color=chosen_color
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Значение adm-role не было установлено.",
                    color=disnake.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
            return

        if new_role is None:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} Вы не указали все необходимые для команды аргументы.",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            return

        if config_data is not None:
            config_data['ROLE_ADMIN'] = str(new_role.id)
            with open(os.path.join('utils/cache/configs', f'{guild_id}.json'),
                      'w') as config_file:
                json.dump(config_data, config_file, indent=4)

        embed = create_embed(
            "Действие выполнено",
            f"{base['APPROVED']} ID ролей успешно изменен на {new_role.mention}.",
            color=chosen_color)
        await ctx.send(embed=embed, ephemeral=True)