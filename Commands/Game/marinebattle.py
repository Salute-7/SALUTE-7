import os
import json
import disnake
from disnake.ext import commands
import random
from utils.base.colors import colors

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

games = {}

class BattleShipGame:
    def __init__(self):
        self.board = [['🌊' for _ in range(10)] for _ in range(10)]
        self.ships = self.place_ships()
        self.turn = 0

    def __init__(self):
        self.board = [['🌊' for _ in range(9)] for _ in range(9)]  
        self.ships = self.place_ships()
        self.turn = 0

    def place_ships(self):
        ships = []
        while len(ships) < 3:
            x, y = random.randint(0, 8), random.randint(0, 8)  
            if (x, y) not in ships:
                ships.append((x, y))
        return ships

    def make_move(self, x, y):
        x -= 1
        y -= 1

        if (x, y) in self.ships:
            self.board[y][x] = '💥'
            self.ships.remove((x, y))
            return True  
        else:
            self.board[y][x] = '❌' 
            return False  

    def is_game_over(self):
        return len(self.ships) == 0

    def get_board_string(self):
        board_string = "".join(str(i).center(3) for i in range(0, 10)) +" " + " \n"  
        for row in range(9):  
            board_string += str(row + 1).center(3) + ""
            for col in range(9):  
                board_string += self.board[row][col] + " "
            board_string += "\n"
        return board_string

    def print_board(self):
        print("\n" + " " * 15 + "Морской бой" + " " * 15 + "\n")
        print(self.get_board_string())
    
class Battleship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.slash_command(name="start_game", description="Начать новую игру")
    async def start_game(self, interaction: disnake.ApplicationCommandInteraction):
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        games[interaction.user.id] = BattleShipGame()
        game = games.get(interaction.user.id)
        embed = disnake.Embed(
            title="Отдать швартовы!",
            description=f"Игра началась! Используйте </move:1292549659369148478> для хода.",
            color=chosen_color
        )
        embed.add_field(name="", value=f"```ansi\n[2;40m[2;31m{game.get_board_string()}[0m[2;40m[0m\n```")
        await interaction.send(embed=embed, ephemeral=True)

    @bot.slash_command(name="move", description="Сделать ход")
    async def move(self, interaction: disnake.ApplicationCommandInteraction, x: int, y: int):
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        game = games.get(interaction.user.id)
        if not game:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Чтобы начать игру, необходимо использовать команду </start_game:1292549659369148477>",
                color=chosen_color
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        if x < 1 or x > 9 or y < 1 or y > 9:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Координаты должны быть от 1 до 9.",
                color=chosen_color
            )

            await interaction.send(embed=embed, ephemeral=True)
            return

        hit = game.make_move(x, y)

        if hit:
            pass
        
        else:
            pass

        embed = disnake.Embed(title="Морской бой", description=f"```ansi\n[2;40m[2;31m{game.get_board_string()}[0m[2;40m[0m\n```", color=chosen_color)
        await interaction.send(embed=embed, ephemeral=True)

        if game.is_game_over():
            embed = disnake.Embed(
                title="Победа!",
                description=f"Поздравляем! Вы потопили все корабли! Игра окончена.",
                color=chosen_color
            )

            await interaction.send(embed=embed, ephemeral=True)
            del games[interaction.user.id]     