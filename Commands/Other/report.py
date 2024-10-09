import os
import json
import disnake
from datetime import datetime, timedelta
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

def create_embed(title, description, color, timestamp):
    embed = disnake.Embed(title=title, description=description, color=color, timestamp=timestamp)
    return embed

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

async def check_permissions(guild_id, ctx):
    settings = load_config(guild_id)
    chosen_color = get_color_from_config(settings)
    is_admin = ctx.author.guild_permissions.administrator

    if not is_admin:  
        await ctx.send(embed=disnake.Embed(
            title="Ошибка при попытке использовать команду",
            description=f"{base['ICON_PERMISSION']} Недостаточно прав или Ваши права были заморожены!",
            color=chosen_color),
            ephemeral=True)
        return False
    return True

base = load_base()

class report(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="report", description="Пожаловаться на доказательства в глобальном чате.")
    async def report(self, ctx, message_id: str):
        config_data = load_config(ctx.guild.id)
        chosen_color = get_color_from_config(config_data)

        guild = ctx.guild

        message_channel = ctx.channel  
        try:
            original_message = await message_channel.fetch_message(message_id)
        except disnake.NotFound:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Сообщение не найдено.",
                color=chosen_color
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

        admin_channel_id = 1282089838123814912  
        admin_channel = self.bot.get_channel(admin_channel_id)

        if not admin_channel:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду",
                description=f"{base['ICON_PERMISSION']} Админ-канал не найден.",
                color=chosen_color
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
        original_author_id = original_message.author

        if "> " in original_message.content:
            embed = disnake.Embed(
                title=f"Жалоба от {ctx.author.display_name}",
                description=f"\n\nЖалоба на сообщение:\n{original_message.content}",
                color=chosen_color
            )

            if original_message.attachments:
                attachment_url = original_message.attachments[0].url
                embed.add_field(name="Вложения:", value=f"[Просмотреть в браузере?]({attachment_url})", inline=False)

            embed.set_footer(text=f"AID: {original_author_id} • UID: {ctx.author.id}")
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            await admin_channel.send(embed=embed)

            embed = disnake.Embed(
                title="Действие выполнено",
                description=f"{base['APPROVED']} Жалоба успешно отправлена.",
                color=chosen_color
            )

            await ctx.response.send_message(embed=embed, ephemeral=True)

        else:
            embed = disnake.Embed(
                title=f"Жалоба от {ctx.author.display_name}",
                description=f"Жалоба на сообщение: ```{original_message.content} ```",
                color=chosen_color
            )

            if original_message.attachments:
                attachment_url = original_message.attachments[0].url
                embed.add_field(name="Вложения:", value=f"[Просмотреть в браузере?]({attachment_url})", inline=False)

            embed.set_footer(text=f"AID: {original_author_id} • UID: {ctx.author.id}")
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            await admin_channel.send(embed=embed)

            embed = disnake.Embed(
                title="Действие выполнено",
                description=f"{base['APPROVED']} Жалоба успешно отправлена.",
                color=chosen_color
            )

            await ctx.response.send_message(embed=embed, ephemeral=True)


        