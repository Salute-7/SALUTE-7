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

class show_blocked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.slash_command(name="show_blocked", description="Данная команда не предназначена для общего использования. (⛔)")
    async def show_blocked(self, interaction: disnake.ApplicationCommandInteraction):
        try:
            with open("utils/global/blocked.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"blocked_users": [], "blocked_guilds": []}
        admin_users = load_admin_users()
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        if str(interaction.author.id) in admin_users:
            blocked_users_desc = "\n".join(f"```{item['id']} Причина: {item['reason']}```" for item in data["blocked_users"])
            blocked_guilds_desc = "\n".join(f"```{item['id']} Причина: {item['reason']}```" for item in data["blocked_guilds"])

            embed = disnake.Embed(
                title="Список заблокированных",
                color=chosen_color
            )
            embed.add_field(name="Заблокированные пользователи", value=blocked_users_desc or "```Нет заблокированных пользователей```")
            embed.add_field(name="Заблокированные сервера", value=blocked_guilds_desc or "```Нет заблокированных серверов```")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду", 
                description=f"{base['ICON_PERMISSION']} У вас нет доступа к этой команде.", 
                color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)

def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}