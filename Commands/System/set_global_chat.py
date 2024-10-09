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

class set_global_chat(commands.Cog):
    def __init__(self, bot):  
        self.bot = bot
        print('Файл Commands/Config/set_global_chat Загружен!')

    @commands.slash_command(description="Установить текстовый канал для глобального чата.")
    async def set_global_chat(self, interaction: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        guild_id = interaction.guild.id
        config_data = load_config(guild_id)
        chosen_color = get_color_from_config(config_data)
        
        guild_id = interaction.guild.id
        
        if not await check_permissions(guild_id, interaction):
            return
        
        config_data = load_config(guild_id)
        if config_data is not None:
            config_data['GLOBAL'] = str(channel.id)
            
            with open(os.path.join('utils/cache/configs', f'{guild_id}.json'), 'w') as config_file:
                json.dump(config_data, config_file, indent=4)

            embed = create_embed("", f"{base['APPROVED']} ID канала с глобальным чатом успешно изменен на {channel.mention}.", color=chosen_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)



