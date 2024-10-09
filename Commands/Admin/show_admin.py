import os
import json
import disnake
import sys
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

class show_admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="show_admins", description="Данная команда не предназначена для общего использования. (⛔)")
    async def show_admins(self, interaction: disnake.ApplicationCommandInteraction):
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        admin_users = load_admin_users()
        if interaction.author.id == 936292219378348033:
            if not admin_users:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['APPROVED']} Нет admin-пользователей в списке.",
                    color=chosen_color
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            embed = disnake.Embed(
                title="Персонал:",
                description=f"```{' • '.join(admin_users)}```",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            os.execv('/usr/bin/python3', ['python3'] + sys.argv) 
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
