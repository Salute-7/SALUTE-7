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

class management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="management", description="Данная команда не предназначена для общего использования. (⛔)")
    async def update_blocked(self, interaction: disnake.ApplicationCommandInteraction, 
                            uid: str = None, gid: str = None, action: str = commands.Param(choices=["заблокирован", "разблокирован"], default="заблокирован"), 
                            reason: str = None):
        member = interaction.author  
        guild_id = member.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        admin_users = load_admin_users()

        if str(interaction.author.id) in admin_users:
            if uid or gid:
                try:
                    with open("utils/global/blocked.json", "r") as f:
                        data = json.load(f)
                except FileNotFoundError:
                    data = {"blocked_users": [], "blocked_guilds": []}
                
            if uid:
                if action == "заблокирован":
                    if {"id": uid, "reason": reason} not in data["blocked_users"]:
                        data["blocked_users"].append({"id": uid, "reason": reason})
                elif action == "разблокирован":
                    data["blocked_users"] = [
                        item for item in data["blocked_users"] if item["id"] != uid
                    ]

            elif gid:
                if action == "заблокирован":
                    if {"id": gid, "reason": reason} not in data["blocked_guilds"]:
                        data["blocked_guilds"].append({"id": gid, "reason": reason})
                elif action == "разблокирован":
                    data["blocked_guilds"] = [item for item in data["blocked_guilds"] if item["id"] != gid]

            with open("utils/global/blocked.json", "w") as f:
                json.dump(data, f, indent=4)

            embed = disnake.Embed(
                title="Список заблокированных обновлен", 
                description=f"{base['APPROVED']} Пользователь {uid} был {action}" if uid else f"Сервер {gid} был {action}",
                color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            #os.execv(sys.executable, ['python'] + sys.argv)
            #os.execv('/usr/bin/python3', ['python3'] + sys.argv)  
        else:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду", 
                description=f"{base['ICON_PERMISSION']} У вас нет доступа к этой команде.", 
                color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        admin_channel_id = 1287408669083959306
        admin_channel = self.bot.get_channel(admin_channel_id)

        if admin_channel:
            log_message = disnake.Embed(title="", description=f"""
            Действие: {action}
            Исполнитель: {interaction.author.mention}
            Цель: {uid if uid else gid}
            Тип: {"UID" if uid else "GID"}
            Причина: {reason}
            """, color=chosen_color, timestamp=interaction.created_at)

            try:
                log_message.set_footer(text=f"🛡️ UID: {interaction.author.id} • GID: {interaction.guild.id}", icon_url=interaction.author.display_avatar.url)
                if uid:
                    user = await self.bot.fetch_user(uid)
                    log_message.set_thumbnail(url=user.avatar.url)
                elif gid:
                    guild = self.bot.get_guild(int(gid))
                    log_message.set_thumbnail(url=guild.icon.url)
            except (AttributeError, TypeError):
                pass

            await admin_channel.send(embed=log_message)

def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}
