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

class set_welcome_channel(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot

    @commands.slash_command(name="set_welcome_channel", description="Устанавливает или удаляет канал для приветствий.")
    async def set_welcome_channel(self, ctx, channel: disnake.TextChannel = None, delete: bool = False):
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        if delete:
            if 'WELCOME_CHANNEL' in settings:
                settings['WELCOME_CHANNEL'] = "" 
                with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
                    json.dump(settings, config_file, indent=4)
                
                embed = create_embed(
                    "Действие выполнено",
                    f"{base['APPROVED']} Канал для приветствий отключён.",
                    color=chosen_color)
                await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Канал для приветствий не был установлен.",
                    color=disnake.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} У бота нет прав на отправку сообщений в канал {channel.mention}.",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            return

        if channel is None:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} Вы не указали все необходимые для команды аргументы.",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        settings['WELCOME_CHANNEL'] = str(channel.id)
        embed = create_embed(
            "Действие выполнено",
            f"{base['APPROVED']} Канал для приветствий установлен: {channel.mention}.",
            color=chosen_color)
        await ctx.send(embed=embed, ephemeral=True)

        with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
            json.dump(settings, config_file, indent=4)