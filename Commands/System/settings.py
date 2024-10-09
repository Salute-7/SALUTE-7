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

async def check_permissions_2(guild_id, interaction):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    admin_users = load_admin_users()

    is_admin = interaction.author.guild_permissions.administrator
    is_owner = str(interaction.author.id) in admin_users
    if not is_admin and not is_owner:  
        await interaction.send(embed=create_embed(
            "Ошибка при попытке использовать команду",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

class settings(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @commands.slash_command(name="settings", description="Настройки бота.")
    async def settings(self, interaction: disnake.ApplicationCommandInteraction):
        guild = interaction.guild
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
  
        if not await check_permissions_2(guild_id, interaction):
            return
        try:
            embed = disnake.Embed(title="Настройки", color=chosen_color)
            
            roles_display = {
                f"{base['MODERI']} Модераторы": settings.get('ROLE_MODER'),
                f"{base['ADMINI']} Администраторы": settings.get('ROLE_ADMIN'),
                f"{base['NEW_ROLE']} Роль для гостей": settings.get('ROLE_ID')
            }

            embed.add_field(
                name="",
                value="\n".join(
                    f"**{role_name}:**\n<@&{role_id}>" if role_id else f"**{role_name}:**\nРоль не найдена"
                    for role_name, role_id in roles_display.items()
                ),
                inline=True
            )

            channel_info = []

            if settings.get('ADMIN_LOGS'):
                channel_info.append(f"{base['LOGI_2']} **Канал с логами:**\n<#{settings.get('ADMIN_LOGS')}>\n")
            else:
                channel_info.append(f"{base['LOGI_2']} **Канал с логами:**\nКанал не установлен\n")

            if settings.get('WELCOME_CHANNEL'):
                channel_info.append(f"{base['LOGI_2']} **Канал с приветом:**\n<#{settings.get('WELCOME_CHANNEL')}>\n")
            else:
                channel_info.append(f"{base['LOGI_2']} **Канал с приветом:**\nКанал не установлен\n")

            if settings.get('GLOBAL'):
                channel_info.append(f"{base['LOGI_2']} **Канал с глоб. чатом:**\n<#{settings.get('GLOBAL')}>\n")
            else:
                channel_info.append(f"{base['LOGI_2']} **Канал с глоб. чатом:**\nКанал не установлен\n")

            embed.add_field(
                name="",
                value="".join(channel_info), 
                inline=True
            )

            embed.set_footer(text=f"Guild ID: {guild_id}")

            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)

            await interaction.send(embed=embed, ephemeral=True)          
        except Exception as e:
            pass