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
base = load_base()

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="admin", description="Данная команда не предназначена для общего использования. (⛔)")
    async def vip_command(self, ctx, user: str):
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        admin_users = load_admin_users()

        if ctx.author.id == 936292219378348033:
            if str(user) in admin_users:
                embed = disnake.Embed(title="Ошибка при попытке использовать команду", description=f"{base['ICON_PERMISSION']} {user} уже является admin-пользователем.", color=chosen_color)
                await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                admin_users[str(user)] = True
                save_admin_users(admin_users)
                embed = disnake.Embed(title="Действие выполнено", description=f"{base['APPROVED']} {user} добавлен в admin-пользователи.", color=chosen_color)
                await ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed(title="Ошибка при попытке использовать команду", description=f"{base['ICON_PERMISSION']} У вас нет доступа к этой команде.", color=chosen_color)
            await ctx.response.send_message(embed=embed, ephemeral=True)

def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}

def save_admin_users(vip_users):
    with open('utils/global/admin_users.json', 'w', encoding='utf-8') as f:
        json.dump(vip_users, f, indent=4)