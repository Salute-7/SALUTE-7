import os
import json
import time
import disnake
from datetime import datetime, timedelta
from disnake.ext import commands
from utils.base.colors import colors

bot = commands.InteractionBot(intents=disnake.Intents.all())
latency = 54

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

base = load_base()
start_time = time.time()

class helpcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('Файл Commands/Other/help.py Загружен!')
        self.start_time = time.time()
        self.last_reset_time = datetime.now()

    @commands.slash_command(name='help', description='Отобразит краткую информацию по боту (🌎)')
    async def help(self, interaction: disnake.ApplicationCommandInteraction):
        global servers_added_today
        guild_id = interaction.guild.id
        settings = load_config(guild_id)

        # Проверяем, нужно ли сбрасывать счетчики
        if datetime.now() - self.last_reset_time > timedelta(days=1):
            servers_added_today = 0
            self.last_reset_time = datetime.now()

        total_servers = len(self.bot.guilds)
        total_members = sum(len(guild.members) for guild in self.bot.guilds)
        total_channels = sum(len(guild.channels) for guild in self.bot.guilds)

        uptime_seconds = time.time() - self.start_time
        latency = self.bot.latency * 1000

        if uptime_seconds < 60:
            uptime = time.strftime("%S секунд назад", time.gmtime(uptime_seconds))
        elif uptime_seconds < 3600:
            uptime = time.strftime("%M минут назад", time.gmtime(uptime_seconds))
        elif uptime_seconds < 86400:
            uptime = time.strftime("%H часов назад", time.gmtime(uptime_seconds))
        else:
            uptime = f"{int(uptime_seconds // 86400)} дней назад"

        chosen_color = get_color_from_config(settings)

        pages = [
            disnake.Embed(title="Статистика SALUTE - 1", color=chosen_color)
                .set_thumbnail(url=interaction.author.display_avatar)
                .add_field(
                    name="Основная",
                    value=f"""
                    Сборка: {base['UPDATE']}
                    Програмное: {base['VERSION']}
                    Разработчик: {base['RAZRAB']}
                    Всего участников: {total_members}""", inline=True)

                .add_field(
                    name="Платформа",
                    value=f"""
                    Серверов: {total_servers}
                    Задержка: {latency:.0f} мс
                    Обновлён: {uptime}
                    Всего каналов: {total_channels}""", inline=True),

            disnake.Embed(title="Общие команды", color=chosen_color)
                .set_thumbnail(url=interaction.author.display_avatar)
                .add_field(
                    name="</pay:1283133506578288681>   💵",
                    value="Отправить деньги другому пользователю.",
                    inline=False)
                .add_field(
                    name="</profile:1286075944527986688>   📊",
                    value="Проверить текущий баланс.",
                    inline=False)
                .add_field(
                    name="</buy_car:1284829906865225809>   🚗",
                    value="Купить новый автомобиль.",
                    inline=False)
                .add_field(
                    name="</reward:1284829906865225811>   🎉",
                    value="Получить свою зарплату.",
                    inline=False)
                .add_field(
                    name="</sellcar:1284829906865225810>   🚗",
                    value="Продать свой автомобиль.",
                    inline=False)
                .add_field(
                    name="</top_active:1283133506297266340>   🌟",
                    value="Показать 10 самых активных пользователей.",
                    inline=False)
                .add_field(
                    name="</top_balance:1283133506297266341>   💰",
                    value="Показать 10 пользователей с наибольшим балансом.",
                    inline=False)
                .add_field(
                    name="</duel:1283133506297266342>   ⚔️",
                    value="Вызвать другого пользователя на дуэль.",
                    inline=False)

                .add_field(
                    name="</buy_home:1285691163843629078>   🏡",
                    value="Купить дом/квартиру/особняк.",
                    inline=False)

                .add_field(
                    name="</sellhome:1285691163843629077>  🏡",
                    value="Продать дом/квартиру/особняк.",
                    inline=False),                 

            disnake.Embed(title="Команды для персонала", color=chosen_color)
                .set_thumbnail(url=interaction.author.display_avatar)
                .add_field(
                    name="</add:1283133506708308021>   ➕",
                    value="Добавить монеты пользователю.",
                    inline=False)
                .add_field(
                    name="</set:1283133506708308023>   🏦",
                    value="Установить баланс для пользователя.",
                    inline=False)
                .add_field(
                    name="</take:1283133506708308022>   ➖",
                    value="Убрать монеты у пользователя.",
                    inline=False)
                .add_field(
                    name="</clear:1283133506578288687>   🧼",
                    value="Очистить чат от сообщений.",
                    inline=False),

            disnake.Embed(title="Команды для тех. персонала", color=chosen_color) 
                .set_thumbnail(url=interaction.author.display_avatar) 
                .add_field(
                    name="</settings:1283133506297266344>   🌐",
                    value="Посмотреть текущие настройки сервера.",
                    inline=False) 
                .add_field(
                    name="</set_pay:1283133506444202057>   💸",
                    value="Установить новый канал для платежей на сервере.",
                    inline=False) 
                .add_field(
                    name="</set_logs:1283133506444202059>   📜",
                    value="Установить канал для логов администрации.",
                    inline=False) 
                .add_field(
                    name="</set_color:1283133506297266343>   🎨",
                    value="Выбрать цвет для сообщений бота.",
                    inline=False)
                .add_field(
                    name="</set_moderator:1283133506444202055>   📝",
                    value="Добавить новые id для стажёров сервера.",
                    inline=False)

                .add_field(
                    name="</set_global_chat:1285691163843629076>   🌍",
                    value="Добавить глобальный чат для этого сервера.",
                    inline=False)

                .add_field(
                    name="</set_welcome_channel:1286251791012335730>   💼",
                    value="Добавить канал для приветствия пользователей.",
                    inline=False)

                .add_field(
                    name="</set_administrator:1283133506444202056>   ⚙️",
                    value="Добавить новые id для персонала сервера.",
                    inline=False),

            disnake.Embed(title="История обновлений SALUTE - 1", color=chosen_color) 
                .set_thumbnail(url=interaction.author.display_avatar) 
                .add_field(
                    name="",
                    value=f"Дата создания: 30 мар. 2024г.\nТекущая версия: {base['VERSION']}\nРазработчиков: 1\nХранение: VDS Hosting.",               
                    inline=False)

        ]

        update = [
            disnake.Embed(title="История обновлений SALUTE - 1 (1.6.5) (18.09.2024)", color=chosen_color) 
            .set_thumbnail(url=interaction.author.display_avatar) 
            .add_field(
                name="",
                value=
                "**Обновление глобального чата (</set_global_chat:1285691163843629076>)**\n"
                "\n**Добавлено:**\n"
                "Возможность отправлять .png, .jpg, .webp и др.\n"                                        
                "\n**Изменено:**\n"
                "Переработан вид сообщений.\n"
                "\n**Убрано:**\n"
                "Лишняя, не несущая смысловой нагрузки информация.\n"
                "\n**Исправлено:**\n"
                "Различные ошибки.\n"                                 
                "\n**Обновление общей информации (</profile:1286075944527986688>)**\n"                                   
                "\n**Изменено:**\n"
                "Теперь основная информация показывается в /profile, заместо /balance.\n"   
                "\n**Исправлено:**\n"
                "Различные ошибки.\n"        
                "\n**Обновление информации в /help (</help:1283133506297266336>)**\n"  
                "\n**Добавлено:**\n"
                "Раздел « История обновлений SALUTE - 1 »\n"                                                        
                "\n**Изменено:**\n"
                "Теперь команды отображаются через </name:id>\n"
                "\n**Исправлено:**\n"
                "Различные ошибки.",                     
                inline=False),

            disnake.Embed(title="История обновлений SALUTE - 1 (1.7.6) (19.09.2024)", color=chosen_color) 
            .set_thumbnail(url=interaction.author.display_avatar) 
            .add_field(
                name="",
                value=
                "**Обновление /settings (</settings:1283133506297266344>)**\n"                                      
                "\n**Изменено:**\n"
                "Переработан вид сообщений.\n"   
                "\n**Обновление глобального чата (</set_global_chat:1285691163843629076>)**\n"
                "\n**Добавлено:**\n"
                "Возможность отправлять .mp3\n"                                        
                "\n**Изменено:**\n"
                "Переработан вид сообщений.\n",
                inline=False)
        ]      

        select = disnake.ui.Select(
            options=[
                disnake.SelectOption(label="Основная информация", value="page1"),
                disnake.SelectOption(label="Общие команды",value="page2"),
                disnake.SelectOption(label="Команды для персонала", value="page3"),
                disnake.SelectOption(label="Команды для тех. персонала", value="page4"),
                disnake.SelectOption(label="История обновлений SALUTE - 1", value="page5"),
            ],
            placeholder="Выберите одну из страниц",
            min_values=1,
            max_values=1,
        )

        view = disnake.ui.View()
        view.add_item(select) 

        # Второй выпадающий список для версий
        version_button = disnake.ui.Select(
            options=[
                disnake.SelectOption(label="SALUTE - 1 (1.6.5)", value="upd1"),
                disnake.SelectOption(label="SALUTE - 1 (1.7.6)", value="upd2"),
            ],
            placeholder="Выберите одну из доступных версий",
            min_values=1,
            max_values=1,
        ) 

        async def version_button_callback(interaction: disnake.Interaction):
            if version_button.values[0] == 'upd1':
                await interaction.response.edit_message(embed=update[0], view=view)  
            elif version_button.values[0] == 'upd2':
                await interaction.response.edit_message(embed=update[1], view=view)
        version_button.callback = version_button_callback
        
        async def select_callback(interaction: disnake.Interaction):
            if select.values[0] == 'page1': 
                await interaction.response.edit_message(embed=pages[0], view=view)
            elif select.values[0] == 'page2':
                await interaction.response.edit_message(embed=pages[1], view=view)
            elif select.values[0] == 'page3':
                await interaction.response.edit_message(embed=pages[2], view=view)
            elif select.values[0] == 'page4':
                await interaction.response.edit_message(embed=pages[3], view=view)
            elif select.values[0] == 'page5':
                view.add_item(version_button)           
                await interaction.response.edit_message(embed=pages[4], view=view)

        select.callback = select_callback 

        # Отправляем начальное сообщение
        await interaction.response.send_message(embed=pages[0], view=view)

