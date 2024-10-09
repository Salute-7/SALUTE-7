import disnake
import sqlite3
import os
import json
import asyncio
from disnake.ext import commands
from utils.base.colors import colors
from disnake.ui import View, Button

bot = commands.InteractionBot(intents=disnake.Intents.all())

board = [":white_large_square:" for _ in range(9)]
current_player = None
game_over = False
player1 = None
player2 = None

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

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

def check_win():
    """Проверяет победителя на игровом поле."""
    winning_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]

    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != ":white_large_square:":
            return board[combo[0]]
 
    return None

def reset_game():
    global board
    board = [":white_large_square:" for _ in range(9)]

def update_board(position, player):
    board[position] = player

class TicTacToeView(View):
    def __init__(self, player1, player2, bet=None, timeout=180):
        super().__init__(timeout=timeout)
        global current_player
        self.player1 = player1
        self.player2 = player2
        self.bet = bet
        self.chosen_color = None
        current_player = self.player1

        for i in range(9):
            button = Button(label="⬜️", row=i // 3) 
            button.position = i
            button.disabled = False
            async def button_callback(interaction: disnake.MessageInteraction, button=button):
                global current_player, game_over, player1, player2
                guild_id = interaction.guild.id
                settings = load_config(guild_id)
                chosen_color = get_color_from_config(settings)

                if interaction.user != self.player1 and interaction.user != self.player2:
                    embed = disnake.Embed(
                    title=f"Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Вы не можете использовать это сейчас, попробуйте позже.",
                    color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                if game_over:
                    embed = disnake.Embed(
                    title=f"Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Вы не можете использовать это сейчас, попробуйте позже.",
                    color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                if interaction.user != current_player:
                    embed = disnake.Embed(
                    title=f"Ошибка при попытке использовать команду",
                    description=f"{base['ICON_PERMISSION']} Вы не можете использовать это сейчас, попробуйте позже.",
                    color=chosen_color
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                position = button.position
                if board[position] == ":white_large_square:":
                    update_board(position, ":regional_indicator_x:" if current_player == self.player1 else ":regional_indicator_o:")
                    button.label = "❌" if current_player == self.player1 else "⭕️"
                    button.disabled = True

                    winner = check_win()
                    if winner:
                        game_over = True
                        winner_player = player1 if winner == ":regional_indicator_x:" else player2
                        winner_name = winner_player.display_name

                        embed = display_board_embed(player1, player2, chosen_color, self.bet, winner_name)
                        await interaction.response.edit_message(embed=embed, view=None)

                    elif all(cell != ":white_large_square:" for cell in board): 
                        game_over = True
                        embed = display_board_embed(player1, player2, chosen_color, self.bet, winner_name="Ничья!") 
                        await interaction.response.edit_message(embed=embed, view=None)

                    else:
                        current_player = self.player2 if current_player == self.player1 else self.player1
                        await interaction.response.edit_message(embed=display_board_embed(player1, player2, chosen_color, self.bet), view=self)

            button.callback = button_callback
            self.add_item(button)

def display_board_embed(player1, player2, chosen_color, bet=None, winner_name=None):
    global current_player
    embed = disnake.Embed(title="Крестики-нолики",
        color=chosen_color
    )

    if bet is not None:
        bet = f"{int(bet):,}".replace(',', '.')
        embed.add_field(
            name=f"💰 Ставка {bet}₽",
            value="",
            inline=False
        )

    if winner_name:
        embed.add_field(
            name=f"🏆 {winner_name} побеждает!",
            value=f"",
            inline=False
        )
        embed.add_field(
            name=f"⚔️ {player1.display_name} сражался против {player2.display_name}",
            value="", 
            inline=False
        )

    else:
        embed.add_field(
            name=f"🏹 {current_player.display_name} думает над ходом...",
            value=f"",
            inline=False
        )
        embed.add_field(
            name=f"⚔️ {player1.display_name} сражается против {player2.display_name}",
            value="", 
            inline=False
        )
    embed.set_thumbnail(url=current_player.display_avatar.url)
    return embed
                                                            
            
class stonegame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="krestiki-noliki", description="Мини-игра крестики-нолики!")
    async def stonegame(self, interaction: disnake.ApplicationCommandInteraction, user: disnake.Member):
        global board, current_player, player1, player2 
        game_over = False 
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
            "Ошибка при попытке использовать команду",
            f"{base['ICON_PERMISSION']} Команду нельзя использовать в канале глобального чата.",
            color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        if user is interaction.author:
            embed = create_embed(
            title="Ошибка при попытке использовать команду",
            description=
            f"{base['ICON_PERMISSION']} Вы не можете отправить предложение самому себе.",
            color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if user is None:
            embed = disnake.Embed(
            title="Ошибка при попытке использовать команду",
            description=
            f"{base['ICON_PERMISSION']} Не удалось найти пользователя. Пожалуйста, проверьте, что вы упомянули правильного пользователя.",
            color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        bet = None
        player1 = interaction.author
        player2 = user
        
        reset_game()
        view = TicTacToeView(player1, player2)
        view.chosen_color = chosen_color
        message = await interaction.response.send_message(
            embed=display_board_embed(player1, player2, chosen_color, bet),
            view=view
        )
        