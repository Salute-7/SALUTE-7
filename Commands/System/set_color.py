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

color_map = {
    "orange": disnake.Color.orange(),
    "red": disnake.Color.red(),
    "green": disnake.Color.green(),
    "blue": disnake.Color.blue(),
    "purple": disnake.Color.purple(),
    "yellow": disnake.Color.gold(),
    "pink": disnake.Color.from_rgb(255, 105, 180),
    "cyan": disnake.Color.from_rgb(0, 255, 255),
    "lime": disnake.Color.from_rgb(50, 205, 50),
    "brown": disnake.Color.from_rgb(139, 69, 19),
    "grey": disnake.Color.from_rgb(128, 128, 128),
    "navy": disnake.Color.from_rgb(0, 0, 128),
    "teal": disnake.Color.from_rgb(0, 128, 128),
    "gold": disnake.Color.from_rgb(255, 215, 0),
    "salmon": disnake.Color.from_rgb(250, 128, 114),
    "orchid": disnake.Color.from_rgb(218, 112, 214),
    "default": disnake.Color.from_rgb(168,166,240),
}

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed

def load_config(guild_id):
    config_path = os.path.join('utils/cache/configs', f'{guild_id}.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            return config_data
    else:
        return {}

def get_color_from_config(config_data):
    chosen_color = config_data.get('COLOR', 'default')
    return color_map.get(chosen_color, disnake.Color.default())

class ColorSelect(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label="Оранжевый", value="orange"),
            disnake.SelectOption(label="Красный", value="red"),
            disnake.SelectOption(label="Зеленый", value="green"),
            disnake.SelectOption(label="Синий", value="blue"),
            disnake.SelectOption(label="Фиолетовый", value="purple"),
            disnake.SelectOption(label="Желтый", value="yellow"),
            disnake.SelectOption(label="Розовый", value="pink"),
            disnake.SelectOption(label="Голубой", value="cyan"),
            disnake.SelectOption(label="Лайм", value="lime"),
            disnake.SelectOption(label="Коричневый", value="brown"),
            disnake.SelectOption(label="Серый", value="grey"),
            disnake.SelectOption(label="Морской", value="navy"),
            disnake.SelectOption(label="Бирюзовый", value="teal"),
            disnake.SelectOption(label="Золотой", value="gold"),
            disnake.SelectOption(label="Лососевый", value="salmon"),
            disnake.SelectOption(label="Орхидея", value="orchid"),
            disnake.SelectOption(label="Стандартный", value="default"),
        ]
        super().__init__(placeholder="Выберите цвет...", options=options)

    async def callback(self, interaction: disnake.MessageInteraction):
        guild_id = interaction.guild.id
        color_value = self.values[0]

        config_data = load_config(guild_id)
        config_data['COLOR'] = color_value.lower()

        with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

        embed = create_embed(f"Действие выполнено", f"Цвет изменён на {color_value}.", color=color_map[color_value])
        await interaction.response.edit_message(embed=embed) 

class ColorDropdown(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ColorSelect())

class set_color(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="set_color", description="Изменить цвет для сообщений.")
    @commands.has_guild_permissions(manage_channels=True)
    async def set_color(self, interaction: disnake.ApplicationCommandInteraction):

        guild_id = interaction.guild.id
        config_data = load_config(guild_id)
        chosen_color = get_color_from_config(config_data)
        view = ColorDropdown()

        global_channel_id = config_data.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return


        embed = create_embed("Выберите желаемый цвет:", " ", color=chosen_color)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)