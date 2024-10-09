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

class remove_vip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.slash_command(name="unvip", description="Данная команда не предназначена для общего использования. (⛔)")
    async def remove_vip_command(self, ctx, user: str):
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        vip_users = load_vip_users()
        admin_users = load_admin_users()

        if str(ctx.author.id) in admin_users:
            if str(user) in vip_users:
                del vip_users[str(user)]
                save_vip_users(vip_users)
                embed = disnake.Embed(title="Действие выполнено", description=f"{base['APPROVED']} {user} удален из VIP-пользователей.", color=chosen_color)
                await ctx.response.send_message(embed=embed, ephemeral=True) 
                admin_channel_id = 1287408669083959306 
                admin_channel = self.bot.get_channel(admin_channel_id)
                if admin_channel:
                    log_message = disnake.Embed(title="", description=f"""
                    Действие: забрал
                    Исполнитель: {ctx.author.mention}
                    Цель: {user}
                    Тип: VIP
                    """, color=chosen_color, timestamp=ctx.created_at)

                    try:
                        log_message.set_thumbnail(url=user.avatar.url)
                    except (AttributeError, TypeError):
                        pass

                    log_message.set_footer(text=f"🛡️ UID: {ctx.author.id} • GID: {ctx.guild.id}", icon_url=ctx.author.display_avatar.url)

                    await admin_channel.send(embed=log_message)

            else:
                embed = disnake.Embed(title="Ошибка при попытке использовать команду", description=f"{base['ICON_PERMISSION']} {user} не является VIP-пользователем.", color=chosen_color)
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

def load_vip_users():
    try:
        with open('utils/global/vip_users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_vip_users(vip_users):
    with open('utils/global/vip_users.json', 'w', encoding='utf-8') as f:
        json.dump(vip_users, f, indent=4)
