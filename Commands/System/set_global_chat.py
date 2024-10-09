import os
import json
import disnake
import asyncio
import requests
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
            config = json.load(config_file)
            if "WEBHOOK" not in config:
                config["WEBHOOK"] = ""
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
            return config
    else:
        config = {"WEBHOOK": ""}
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return config

def create_embed(title, description, color, timestamp):
    embed = disnake.Embed(title=title, description=description, color=color, timestamp=timestamp)
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

class set_global_chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Установить или удалить текстовый канал для глобального чата.")
    async def set_global_chat(self, interaction: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel = None, delete: bool = False):
        guild_id = interaction.guild.id
        config_data = load_config(guild_id) 
        chosen_color = get_color_from_config(config_data)

        if not await check_permissions(guild_id, interaction):
            return

        if delete:
            if 'GLOBAL' in config_data:
                config_data['GLOBAL'] = "" 
                with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
                    json.dump(config_data, config_file, indent=4)
                
                embed = disnake.Embed(
                    title="Действие выполнено",
                    description=f"{base['APPROVED']} Глобальный чат успешно отключён.",
                    color=chosen_color
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Глобальный чат не был установлен.",
                    color=disnake.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not channel.permissions_for(interaction.guild.me).send_messages:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} У бота нет прав на отправку сообщений в канал {channel.mention}.",
                color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if channel is None:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']} Вы не указали все необходимые для команды аргументы.",
                color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if channel is not None:
            if not channel.permissions_for(interaction.guild.me).send_messages:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} У бота нет прав на отправку сообщений в канал {channel.mention}.",
                    color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            config_data['GLOBAL'] = str(channel.id)

            with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
                json.dump(config_data, config_file, indent=4)

            server_name = interaction.guild.name
            member_count = interaction.guild.member_count
            created_at = interaction.guild.created_at.strftime("%d.%m.%Y")

            global_servers = []
            for guild in self.bot.guilds:
                guild_config = load_config(guild.id)
                if guild_config and guild_config.get("GLOBAL"):
                    global_servers.append(guild.name)

            try:
                embed = disnake.Embed(title="", description=f"{base['APPROVED']} ID канала с глобальным чатом успешно изменен на {channel.mention}.", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)

                embed2 = disnake.Embed(
                    title=f"{server_name} подключается к чату!",
                    description=f"\nКоличество участников: {member_count}"
                                f"\nСервер был создан: {created_at}"
                                f"\nВсего серверов, подключённых к глобальному чату: {len(global_servers)}"
                                f"\nЕсли вы ещё не прочитали правила чата - [прочитайте их.](https://text-host.ru/politika-ispolzovaniya-globalnogo-chata)",
                    color=chosen_color, timestamp=interaction.created_at)
                
                embed2.set_footer(text=f"UID: {interaction.author.id} • GID: {guild_id}", icon_url=interaction.author.display_avatar.url)

                if interaction.guild.icon:
                    embed2.set_thumbnail(url=interaction.guild.icon.url)

                for guild in self.bot.guilds:
                    other_config_data = load_config(guild.id)
                    other_channel_id = other_config_data.get("GLOBAL", None)

                    if other_channel_id:
                        other_global_channel = self.bot.get_channel(int(other_channel_id))
                        if other_global_channel:
                            webhooks = await other_global_channel.webhooks()
                            webhook = None
                            
                            for wh in webhooks:
                                if wh.name == "GlobalChat":
                                    webhook = wh
                                    break
                            
                            if not webhook:
                                webhook = await other_global_channel.create_webhook(name="SALUTE-GlobalChat")

                            embed_dict = {
                                "title": embed2.title,
                                "description": embed2.description,
                                "color": embed2.color.value,
                                "footer": {"text": embed2.footer.text},
                                "timestamp": embed2.timestamp.isoformat(),
                                "thumbnail": {"url": embed2.thumbnail.url} if embed2.thumbnail else None,
                            }

                            payload = {
                                'username': f"{interaction.author.display_name} ({interaction.author.id}) [{guild_id}]",
                                'embeds': [embed_dict],
                                'avatar_url': interaction.author.avatar.url if interaction.author.avatar else None,
                            }

                            response = requests.post(webhook.url, json=payload)
                            
                            if response.status_code != 204:
                                print(f"Ошибка при отправке сообщения через вебхук на сервере {guild.name}: {response.status_code}, {response.text}")

            except disnake.errors.NotFound:
                pass

