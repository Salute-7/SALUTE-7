import os
import json
import sqlite3
import disnake
from utils.base.colors import colors
from disnake.ext import commands

bot = commands.InteractionBot(intents=disnake.Intents.all())

def load_base():
    config_path = os.path.join('utils/cache/configs', f'main.json')
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
    color_choice = settings.get('COLOR', 'orange')
    return colors.get(color_choice.lower(), disnake.Color.orange())

base = load_base()

class pay(commands.Cog):
    def init(self, bot):  
        self.bot = bot
        print('Файл Commands/Economy/pay.py Загружен!')

    @bot.slash_command(name="pay", description="Отправить деньги другому пользователю (🌎)")
    async def pay(self, inter: disnake.ApplicationCommandInteraction,
                  user: disnake.Member, amount: int):
        guild_id = inter.guild.id
        settings = load_config(guild_id)
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        chosen_color = get_color_from_config(settings)
        try:
            if amount < 50000:
                embed = create_embed(
                    title="",
                    description=
                    f"{base['ICON_PERMISSION']} Сумма должна быть больше 50.000₽",
                    color=chosen_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            formatted = f"{amount:,}".replace(',', '.')

            if user is inter.author:
                embed = create_embed(
                    title="",
                    description=
                    f"{base['ICON_PERMISSION']} Вы не можете отправить деньги самому себе.",
                    color=chosen_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            cursor.execute("SELECT cash FROM users WHERE id = ?",
                           (inter.author.id, ))
            balance = cursor.fetchone()[0]
            if balance < amount:
                embed = create_embed(
                    title="",
                    description=
                    f"{base['ICON_PERMISSION']} У вас недостаточно средств.",
                    color=chosen_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            await inter.response.defer()

            cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?",
                           (amount, inter.author.id))
            cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?",
                           (amount, user.id))
            connection.commit()
            lich_embed = disnake.Embed(
                title=
                f"{inter.author.display_name} переводит средства {user.display_name}",
                description=
                f":coin: Сумма:**\n```+{formatted}₽```",
                color=chosen_color)

            ROLE_IDS_MODERATOR = [
                int(role_id) for role_id in settings['ROLE_MODER'].split(',')
            ]
            ROLE_IDS_ADMIN = [
                int(role_id) for role_id in settings['ROLE_ADMIN'].split(',')
            ]

            is_tech_specialist = any(role.id in ROLE_IDS_ADMIN
                                     for role in inter.author.roles)
            is_moderator = any(role.id in ROLE_IDS_MODERATOR
                               for role in inter.author.roles)

            if inter.author == inter.guild.owner:
                lich_embed.add_field(
                    name=
                    f"Сервер:\n{base['SERVERS']} {inter.guild.name}\nДеньги переведены от:",
                    value=
                    f"\n{base['ICON_OSNOVA']} **Основатель сервера {inter.author.display_name} ({inter.author.id})",
                    inline=False)
            elif is_tech_specialist:
                lich_embed.add_field(
                    name=
                    f"Сервер:\n{base['SERVERS']} {inter.guild.name}\nДеньги переведены от:",
                    value=
                    f"\n{base['ICON_ADMIN']} Администратор сервера {inter.author.display_name} ({inter.author.id})",
                    inline=False)
            elif is_moderator:
                lich_embed.add_field(
                    name=
                    f"Сервер:\n{base['SERVERS']} {inter.guild.name}\nДеньги переведены от:",
                    value=
                    f"\n{base['ICON_MODER']} Модератор сервера {inter.author.display_name} ({inter.author.id})",
                    inline=False)
            else:
                lich_embed.add_field(
                    name=
                    f"Сервер:\n{base['SERVERS']} {inter.guild.name}\nДеньги переведены от:",
                    value=
                    f"\n{base['ICON_OSNOVA']} Участник сервера {inter.author.display_name} ({inter.author.id})",
                    inline=False)

            lich_embed.set_thumbnail(url=inter.author.display_avatar)
            await user.send(embed=lich_embed)

            embed = disnake.Embed(
                title=
                f"{inter.author.display_name} переводит средства {user.display_name}",
                description=
                f"**:coin: Сумма:**\n```-{formatted}₽```",
                color=chosen_color)
            embed.set_thumbnail(url=inter.author.display_avatar)
            await inter.edit_original_response(embed=embed)

            log_embed = disnake.Embed(title="Перевод средств",
                                      color=chosen_color)
            log_embed.set_thumbnail(url=inter.author.display_avatar.url)
            log_embed.add_field(
                name="Отправитель",
                value=f"{inter.author.mention} (ID: {inter.author.id})",
                inline=False)
            log_embed.add_field(name="Получатель",
                                value=f"{user.mention} (ID: {user.id})",
                                inline=False)
            log_embed.add_field(name=":coin: Сумма:",
                                value=f"```{formatted}₽```",
                                inline=False)

            CHANNEL_CANAl_ID_LOGS = settings.get('PAY_LOGS', [])

            if CHANNEL_CANAl_ID_LOGS:
                admin_channel = inter.guild.get_channel(
                    int(CHANNEL_CANAl_ID_LOGS))
                if admin_channel is not None:  
                    await admin_channel.send(embed=log_embed)

        except sqlite3.Error as e:
            # Обработка ошибок базы данных
            print(f"Ошибка базы данных: {e}")
            embed = create_embed(
                title="",
                description=f"{base['ICON_PERMISSION']} Произошла ошибка при выполнении операции.",
                color=chosen_color)
            await inter.edit_original_message(embed=embed)
        except Exception as e:
            # Обработка всех остальных исключений
            print(f"Произошла ошибка: {e}")
            embed = create_embed(
                title="",
                description=f"{base['ICON_PERMISSION']} Произошла ошибка. Пожалуйста, попробуйте позже.",
                color=chosen_color)
            await inter.edit_original_message(embed=embed)
  