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

    is_admin = ctx.author.guild_permissions.administrator
    is_owner = str(ctx.author.id) in admin_users
    if not is_admin and not is_owner:  
        await ctx.send(embed=create_embed(
            "Ошибка при попытке использовать команду",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

class set_moderator(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @bot.slash_command(name="set_moderator", description="Изменить ID ролей (Модератор)")
    async def set_moderator_id(ctx, new_role: disnake.Role = None, delete: bool = False):
        guild_id = ctx.guild.id
        if not await check_permissions(guild_id, ctx):
            return
        
        guild_id = ctx.guild.id
        config_data = load_config(guild_id)
        chosen_color = get_color_from_config(config_data)
        
        if delete:
            if 'ROLE_MODER' in config_data:
                config_data['ROLE_MODER'] = "" 
                with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
                    json.dump(config_data, config_file, indent=4)
                
                embed = disnake.Embed(
                    title="Действие выполнено",
                    description=f"{base['APPROVED']} Значени mod-role успешно отключёно.",
                    color=chosen_color
                )
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Значение mod-role не было установлено.",
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
            config_data['ROLE_MODER'] = str(new_role.id)
            with open(os.path.join('utils/cache/configs', f'{guild_id}.json'),
                      'w') as config_file:
                json.dump(config_data, config_file, indent=4)

        embed = create_embed("Действие выполнено", f"{base['APPROVED']} ID ролей успешно изменен на {new_role.mention}.", color=chosen_color)
        await ctx.send(embed=embed, ephemeral=True)