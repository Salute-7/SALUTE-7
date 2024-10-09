import disnake
from disnake.ext import commands, tasks
import os
import json
import sqlite3
from utils.base.colors import colors

images_path = "images"

def load_base():
    config_path = os.path.join('utils/global', f'main.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
base = load_base()

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

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

class respect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="respect", description="Добавить или убрать репутацию пользователя.")
    async def respect(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.User, action: str = commands.Param(choices=["Добавить", "Убрать"], default="Добавить")):
        user_id = str(user.id)
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        database_path = f'utils/cache/database/{guild_id}.db'

        try:
            with sqlite3.connect(database_path) as conn:
                c = conn.cursor()

                c.execute("SELECT action FROM actions WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
                action_result = c.fetchone()

                if action_result:
                    if action_result[0] == action:
                        embed = disnake.Embed(
                            title=f"Репутация пользователя {user.name}",
                            description=f"Вы уже изменили репутацию пользователя {user.mention}.\nХотите изменить действие? Выберите другое действие для подтверждения.",
                            color=chosen_color
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

                if user_id == interaction.author.id:
                    embed = disnake.Embed(
                        title=f"Репутация пользователя {user.name}",
                        description=f"Вы не можете изменить свою собственную репутацию.",
                        color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                c.execute("INSERT OR REPLACE INTO actions (user_id, guild_id, action) VALUES (?, ?, ?)", (user_id, guild_id, action))
                conn.commit()

                new_reputation = 0

                embed = disnake.Embed(
                    title=f"Репутация пользователя {user.name}",
                    description=f"Репутация пользователя {user.mention} успешно изменена.",
                    color=chosen_color
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

                if user_id == interaction.author.id:
                    embed = disnake.Embed(
                        title=f"Репутация пользователя {user.name}",
                        description=f"Вы не можете изменить свою собственную репутацию.",
                        color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                if action == "Добавить":
                    c.execute("SELECT reputation FROM reputation WHERE user_id = ?", (user_id,))
                    result = c.fetchone()
                    if result:
                        new_reputation = result[0] + 1
                        c.execute("UPDATE reputation SET reputation = ? WHERE user_id = ?", (new_reputation, user_id))
                    else:
                        new_reputation = 1
                        c.execute("INSERT INTO reputation (user_id, reputation) VALUES (?, ?)", (user_id, new_reputation))
                    conn.commit()

                    embed = disnake.Embed(
                        title=f"Репутация пользователя {user.name}",
                        description=f"Вы добавили репутацию пользователю {user.mention}. Его текущая репутация: {new_reputation}",
                        color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                elif action == "Убрать":
                    c.execute("SELECT reputation FROM reputation WHERE user_id = ?", (user_id,))
                    result = c.fetchone()
                    if result and result[0] > 0:
                        new_reputation = result[0] - 1
                        c.execute("UPDATE reputation SET reputation = ? WHERE user_id = ?", (new_reputation, user_id))
                        conn.commit()

                        embed = disnake.Embed(
                            title=f"Репутация пользователя {user.name}",
                            description=f"Вы убрали репутацию пользователю {user.mention}. Его текущая репутация: {new_reputation}",
                            color=chosen_color
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    elif result and result[0] <= 0:
                        embed = disnake.Embed(
                            title=f"Репутация пользователя {user.name}",
                            description=f"У пользователя {user.mention} нет репутации, чтобы ее убрать.",
                            color=chosen_color
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                c.execute("INSERT INTO actions (user_id, guild_id, action) VALUES (?, ?, ?)", (user_id, guild_id, action))
                conn.commit()
                conn.close()
        except:
            pass