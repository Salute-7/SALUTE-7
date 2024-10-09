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

async def check_permissions(guild_id, ctx):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)

    def get_role_ids(role_key):
        return [
            int(role_id) for role_id in settings.get(role_key, [])
            if isinstance(role_id, (str, int)) and str(role_id).strip()
        ]
    
    ROLE_IDS_MODERATOR = get_role_ids('ROLE_MODER')
    ROLE_IDS_ADMIN = get_role_ids('ROLE_ADMIN')
    is_admin = ctx.author.guild_permissions.administrator
    has_role = any(
        role.id in ROLE_IDS_ADMIN or role.id in ROLE_IDS_MODERATOR 
        for role in ctx.author.roles)
    if not has_role and not is_admin:  
        await ctx.send(embed=create_embed(
            "",
            f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

color_map = {
    'orange': disnake.Colour(0xFFA500),
    'red': disnake.Colour(0xFF0000),
    'green': disnake.Colour(0x008000),
    'blue': disnake.Colour(0x0000FF),
    'purple': disnake.Colour(0x800080),
    'yellow': disnake.Colour(0xFFFF00),
    'pink': disnake.Colour(0xFFC0CB),
    'cyan': disnake.Colour(0x00FFFF),
    'lime': disnake.Colour(0x00FF00),
    'brown': disnake.Colour(0xA52A2A),
    'grey': disnake.Colour(0x808080),
    'navy': disnake.Colour(0x000080),
    'teal': disnake.Colour(0x008080),
    'gold': disnake.Colour(0xFFD700),
    'salmon': disnake.Colour(0xFA8072),
    'orchid': disnake.Colour(0xDA70D6),
    'black': disnake.Colour(0x000000),
}

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
            disnake.SelectOption(label="Чёрный", value="black"),
        ]
        super().__init__(placeholder="Выберите цвет...", options=options)

    async def callback(self, interaction: disnake.MessageInteraction):
        guild_id = interaction.guild.id
        color_value = self.values[0]

        config_data = load_config(guild_id)
        config_data['COLOR'] = color_value.lower()
        
        with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

        embed = create_embed(f"Цвет изменен на {color_value}.", f"Доступные цвета:"
                            "\nЛайм: lime"
                            "\nКоричневый: brown"
                            "\nОранжевый: orange"
                            "\nКрасный: red"
                            "\nЗеленый: green"
                            "\nСиний: blue"
                            "\nФиолетовый: purple"
                            "\nЖёлтый: yellow"
                            "\nСерый: grey"
                            "\nМорской: navy"
                            "\nБирюзовый: teal"
                            "\nЗолотой: gold"
                            "\nЛососевый: salmon"
                            "\nОрхидея: orchid"
                            "\nРозовый: pink"
                            "\nГолубой: cyan"
                            "\nЧёрный: black", color=color_map[color_value])
        await interaction.response.edit_message(embed=embed)  # Удаляем вид

class ColorDropdown(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ColorSelect())

class set_color(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('Файл Commands/Config/set_color.py Загружен!')

    @commands.slash_command(name="set_color", description="Изменить цвет для сообщений (💻)")
    async def set_color(self, interaction: disnake.ApplicationCommandInteraction):

        guild_id = interaction.guild.id
        config_data = load_config(guild_id)
        chosen_color = get_color_from_config(config_data)
        view = ColorDropdown()

        embed=create_embed("Доступные цвета:",
                "\nЛайм: lime"
                "\nКоричневый: brown"
                "\nОранжевый: orange"
                "\nКрасный: red"
                "\nЗеленый: green"
                "\nСиний: blue"
                "\nФиолетовый: purple"
                "\nЖёлтый: yellow"
                "\nСерый: grey"
                "\nМорской: navy"
                "\nБирюзовый: teal"
                "\nЗолотой: gold"
                "\nЛососевый: salmon"
                "\nОрхидея: orchid"
                "\nРозовый: pink"
                "\nГолубой: cyan"
                "\nЧёрный: black", color=chosen_color)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)