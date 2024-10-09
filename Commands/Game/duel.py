import os
import json
import sqlite3
import disnake
import random
import asyncio
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

class DuelView(disnake.ui.View):
    active_duels = set() 
    duel_timeout = 60

    def __init__(self, target, author, amount, ctx):
        super().__init__()  
        self.target = target
        self.author = author
        self.amount = amount
        self.accepted = False
        self.ctx = ctx

        duel_pair = (min(self.author.id,
                         self.target.id), max(self.author.id, self.target.id))
        if duel_pair in DuelView.active_duels:
            raise ValueError(
                f"{base['ICON_PERMISSION']} Уже есть активная дуэль между участниками."
            )

        DuelView.active_duels.add(
            duel_pair)  

        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.timeout_duel())

    async def timeout_duel(self):
        await asyncio.sleep(DuelView.duel_timeout)
        if not self.accepted and (min(
                self.author.id,
                self.target.id), max(self.author.id,
                                     self.target.id)) in DuelView.active_duels:
            await self.decline_duel()

    async def decline_duel(self):
        DuelView.active_duels.remove(
            (min(self.author.id,
                 self.target.id), max(self.author.id, self.target.id)))
        for button in self.children:
            button.disabled = True

        guild_id = self.ctx.guild.id
        settings = load_config(guild_id)

        chosen_color = get_color_from_config(settings)

        embed = disnake.Embed(
            title=
            f"Дуэль {self.author.display_name} и {self.target.display_name} отменена!",
            description=
            f"\n \n \n{self.target.mention} **отклонил вызов.\n Используйте </duel:1283133506297266342>, чтобы отправь новый запрос.**",
            color=chosen_color)

        embed.set_thumbnail(url=self.target.display_avatar.url)

        await self.ctx.edit_original_message(embed=embed, view=None)

    @disnake.ui.button(label="Принять", style=disnake.ButtonStyle.green)
    async def accept_callback(self, button: disnake.ui.Button,
                              interaction: disnake.Interaction):
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        if interaction.user != self.target:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=
                f"{base['ICON_PERMISSION']} У вас нет доступа к этой кнопке!",
                color=chosen_color)

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        formatted = f"{self.amount:,}".replace(',', '.')

        if interaction.user == self.target and not self.accepted:
            self.accepted = True

            for button in self.children:
                button.disabled = True

            settings = load_config(interaction.guild.id)
            await interaction.response.edit_message(view=None)
            winner = random.choice([self.author, self.target])

            embed = disnake.Embed(
                title=
                f"Результат дуэли {self.author.display_name} и {self.target.display_name}!",
                description=
                f"\n **Победитель: {winner.mention}!**\n\n**:coin: Ставка:**\n```+{formatted}₽```",
                color=chosen_color)
            embed.set_thumbnail(url=winner.display_avatar.url)
            await interaction.message.edit(embed=embed)

            connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
            cursor = connection.cursor()

            if winner == self.author:
                cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?",
                               (self.amount, self.author.id))
                cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?",
                               (self.amount, self.target.id))
            else:
                cursor.execute("UPDATE users SET cash = cash + ? WHERE id = ?",
                               (self.amount, self.target.id))
                cursor.execute("UPDATE users SET cash = cash - ? WHERE id = ?",
                               (self.amount, self.author.id))
            connection.commit()
            connection.close()

            DuelView.active_duels.remove(
                (min(self.author.id,
                     self.target.id), max(self.author.id, self.target.id)))
            
    @disnake.ui.button(label="Отклонить", style=disnake.ButtonStyle.red)
    async def decline_callback(self, button: disnake.ui.Button,
                               interaction: disnake.Interaction):
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        if interaction.user != self.target and interaction.user != self.author:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=
                f"{base['ICON_PERMISSION']} У вас нет доступа к этой кнопке!",
                color=chosen_color)

            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            return

        for button in self.children:
            button.disabled = True

        await interaction.response.edit_message(view=self)

        embed = disnake.Embed(
            title=
            f"Дуэль {self.author.display_name} и {self.target.display_name} отменена!",
            description=f"\n{interaction.user.mention} **отклонил вызов.**",
            color=chosen_color)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.message.edit(embed=embed)

        await self.decline_duel()

class duel(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot

    @commands.slash_command(name="duel", description="Вызов на дуэль.")
    async def duel(self, ctx, target: disnake.Member, amount: int):

        user = ctx.author
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        connection = sqlite3.connect(f'utils/cache/database/{guild_id}.db')
        cursor = connection.cursor()
        chosen_color = get_color_from_config(settings)

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == ctx.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return 

        cursor.execute("SELECT cash FROM users WHERE id = ?",
                       (ctx.author.id, ))
        author_cash = cursor.fetchone()[0]
        if author_cash < amount:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=
                f"{base['ICON_PERMISSION']} У вас недостаточно средств для ставки.",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            connection.close()
            return

        if amount < 50000:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=
                f"{base['ICON_PERMISSION']} Минимальная ставка 50.000₽",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            return

        if target == ctx.author:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=
                f"{base['ICON_PERMISSION']} Вы не можете отправить дуэль самому себе.",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            return

        cursor.execute("SELECT cash FROM users WHERE id = ?", (target.id, ))
        target_cash = cursor.fetchone()[0]
        if target_cash < amount:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=
                f"{base['ICON_PERMISSION']} У {target.display_name} недостаточно средств для ставки.",
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)
            connection.close()
            return
        try:
            formatted = f"{amount:,}".replace(',', '.')
            embed = disnake.Embed(
                title=
                f"{ctx.author.display_name} вызвал на дуэль {target.display_name}!",
                description=
                f"**:coin: Ставка:**\n```{formatted}₽```",
                color=chosen_color)
            embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
            message = await ctx.send(embed=embed,
                                     view=DuelView(target, ctx.author, amount,
                                                   ctx))
        except ValueError as e:
            await ctx.send(str(e), ephemeral=True)        