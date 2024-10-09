import os
import json
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

async def check_permissions_2(guild_id, interaction):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    def get_role_ids(role_key):
        return [
            int(role_id) for role_id in settings.get(role_key, [])
            if isinstance(role_id, (str, int)) and str(role_id).strip()
        ]
    
    ROLE_IDS_MODERATOR = get_role_ids('ROLE_MODER')
    ROLE_IDS_ADMIN = get_role_ids('ROLE_ADMIN')

    is_admin = interaction.author.guild_permissions.administrator
    has_role = any(
        role.id in ROLE_IDS_ADMIN or role.id in ROLE_IDS_MODERATOR 
        for role in interaction.author.roles)
    
    if not has_role and not is_admin: 
        await interaction.send(embed=create_embed(
            "",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

class settings(commands.Cog):
    def __init__(self, bot):  # Исправлено init на __init__
        self.bot = bot
        print('Файл Commands/Config/settings.py загружен!')

    @commands.slash_command(name="settings", description="Настройки бота (💻)")
    async def settings(self, interaction: disnake.ApplicationCommandInteraction):
        guild = interaction.guild
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        if not await check_permissions_2(guild_id, interaction):
            return

        embed = disnake.Embed(title="Настройки бота", color=chosen_color)
        
        roles_display = {
            f"{base['MODERI']} Модераторы": settings.get('ROLE_MODER'),
            f"{base['ADMINI']} Администраторы": settings.get('ROLE_ADMIN'),
            f"{base['NEW_ROLE']} Роль для гостей": settings.get('ROLE_ID')
        }

        embed.add_field(
            name="",
            value="\n".join(
                f"**{role_name}:**\n<@&{role_id}>" if role_id else f"**{role_name}:\nРоль не найдена**"
                for role_name, role_id in roles_display.items()
            ),
            inline=True
        )


        embed.add_field(
            name="",
            value=(
                f"{base['LOGI_2']} **Канал с логами:**\n"
                f"{('<#' + settings.get('ADMIN_LOGS', 'Канал не найден') + '>' if settings.get('ADMIN_LOGS') is not None else 'Канал не найден')}\n"
                f"{base['LOGI_2']} **Канал с приветом:**\n"
                f"{('<#' + settings.get('WELCOME_CHANNEL', 'Канал не найден') + '>' if settings.get('WELCOME_CHANNEL') is not None else 'Канал не найден')}\n"
                f"{base['LOGI_2']} **Канал с переводами:**\n"
                f"{('<#' + settings.get('PAY_LOGS', 'Канал не найден') + '>' if settings.get('PAY_LOGS') is not None else 'Канал не найден')}\n"
                f"{base['LOGI_2']} **Канал с глоб. чатом:**\n"
                f"{('<#' + settings.get('GLOBAL', 'Канал не найден') + '>' if settings.get('GLOBAL') is not None else 'Канал не найден')}"
            ),
            inline=True
        )

        embed.set_footer(text=f"Guild ID: {guild_id}")

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Создание выпадающего списка
        select = disnake.ui.Select(
            options=[
                disnake.SelectOption(label=f"Установить роль модератора", value="set_moderator"),
                disnake.SelectOption(label=f"Установить роль администратора", value="set_administrator"),
                disnake.SelectOption(label=f"Установить канал с логами", value="set_logs"),
                disnake.SelectOption(label=f"Установить канал с переводами", value="set_pay"),
                disnake.SelectOption(label=f"Установить канал с глобальным чатом", value="set_global_chat"),
                disnake.SelectOption(label=f"Установить канал с приветствием", value="set_welcome_channel"),
                disnake.SelectOption(label=f"Изменить цвет embed", value="set_color"),
            ],
            placeholder="Выберите действие",
            min_values=1,
            max_values=1,
        )

        view = disnake.ui.View()
        view.add_item(select)

        async def select_callback(interaction: disnake.Interaction):
            if select.values[0] == "set_moderator":
                embed = disnake.Embed(title="Используйте команду </set_moderator:1283133506444202055>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif select.values[0] == "set_administrator":
                embed = disnake.Embed(title="Используйте команду </set_administrator:1283133506444202056>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif select.values[0] == "set_logs":
                embed = disnake.Embed(title="Используйте команду </set_logs:1283133506444202059>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif select.values[0] == "set_pay":
                embed = disnake.Embed(title="Используйте команду </set_pay:1283133506444202057>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif select.values[0] == "set_global_chat":
                embed = disnake.Embed(title="Используйте команду </set_global_chat:1285691163843629076>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif select.values[0] == "set_color":
                embed = disnake.Embed(title="Используйте команду </set_color:1283133506297266343>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif select.values[0] == "set_welcome_channel":
                embed = disnake.Embed(title="Используйте команду </set_welcome_channel:1286251791012335730>", color=chosen_color)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = select_callback

        await interaction.send(embed=embed, view=view, ephemeral=True)                