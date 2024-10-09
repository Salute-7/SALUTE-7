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
base = load_base()

class broadcast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="broadcast", description="Данная команда не предназначена для общего использования. (⛔️)")
    async def broadcast(self, ctx, user: str, message: str):
        guild_id = ctx.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)
        admin_users = load_admin_users()

        embed = disnake.Embed(title="Системные сообщения", description=f"Здравствуйте, уважаемый пользователь.\n"
                                                                        f"Администратор отправил вам сообщение:\n"
                                                                        f"{message}"                                                                                                                                                                                                                     
                                                                        , color=chosen_color)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_footer(text=f"🛡️ UID: {ctx.author.id}")

        if str(ctx.author.id) in admin_users:
            try:
                user_id = int(user)  
                user = await self.bot.fetch_user(user_id) 

                if user.dm_channel:
                    await user.send(embed=embed)
                    await ctx.send(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed(
                        title="Ошибка при попытке использовать команду", 
                        description=f"{base['ICON_PERMISSION']} У этого пользователя закрыты личные сообщения.", 
                        color=chosen_color)
                    await ctx.send(embed=embed, ephemeral=True)

            except ValueError:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду", 
                    description=f"{base['ICON_PERMISSION']} Неверный ID пользователя.", 
                    color=chosen_color)
                await ctx.send(embed=embed, ephemeral=True)

            except disnake.Forbidden:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду", 
                    description=f"{base['ICON_PERMISSION']} У меня нет прав на отправку сообщений этому пользователю.", 
                    color=chosen_color)
                await ctx.send(embed=embed, ephemeral=True)

            except disnake.HTTPException:
                embed = disnake.Embed(
                    title="Ошибка при попытке использовать команду", 
                    description=f"{base['ICON_PERMISSION']} Не удалось отправить сообщение.", 
                    color=chosen_color)
                await ctx.send(embed=embed, ephemeral=True)

        else:
            embed = disnake.Embed(
                title="Ошибка при попытке использовать команду", 
                description=f"{base['ICON_PERMISSION']} У вас нет доступа к этой команде.", 
                color=chosen_color)
            await ctx.send(embed=embed, ephemeral=True)

def load_admin_users():
    try:
        with open('utils/global/admin_users.json', 'r', encoding='utf-8') as f:
            admin_users = json.load(f)
            return admin_users
    except FileNotFoundError:
        return {}
