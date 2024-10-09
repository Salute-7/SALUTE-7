import os
import json
import sqlite3
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

class pay(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @bot.slash_command(name="pay", description="Отправить деньги другому пользователю.")
    async def pay(self, inter: disnake.ApplicationCommandInteraction,
                  user: disnake.Member, amount: int):
        guild_id = inter.guild.id
        settings = load_config(guild_id)
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        chosen_color = get_color_from_config(settings)

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == inter.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return 

        try:
            if amount < 50000:
                embed = create_embed(
                    title="Ошибка при попытке использовать команду",
                    description=
                    f"{base['ICON_PERMISSION']} Сумма должна быть больше 50.000₽",
                    color=chosen_color)
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            formatted = f"{amount:,}".replace(',', '.')

            if user is inter.author:
                embed = create_embed(
                    title="Ошибка при попытке использовать команду",
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
                    title="Ошибка при попытке использовать команду",
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

            CHANNEL_CANAl_ID_LOGS = settings.get('ADMIN_LOGS', [])

            if CHANNEL_CANAl_ID_LOGS:  
                admin_channel = inter.guild.get_channel(int(CHANNEL_CANAl_ID_LOGS[0]))
                if admin_channel is not None:
                    await admin_channel.send(embed=log_embed)

        except sqlite3.Error as e:
            embed = create_embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Произошла ошибка при выполнении операции.",
                color=chosen_color)
            await inter.edit_original_message(embed=embed)
        except Exception as e:
            embed = create_embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Произошла ошибка. Пожалуйста, попробуйте позже или заполните /settings.",
                color=chosen_color)
            await inter.edit_original_message(embed=embed)

