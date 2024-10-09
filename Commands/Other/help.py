import os
import json
import time
import disnake
import asyncio
from datetime import datetime, timedelta
from disnake.ext import commands
from utils.base.colors import colors

bot = commands.InteractionBot(intents=disnake.Intents.all())
latency = 54

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
start_time = time.time()

class MySelect(disnake.ui.Select):
    def __init__(self, pages: list[disnake.Embed]):
        super().__init__(
            options=[
                disnake.SelectOption(label="Основная информация", value="page1"),
                disnake.SelectOption(label="Общие команды",value="page2"),
                disnake.SelectOption(label="Команды для персонала", value="page3"),
                disnake.SelectOption(label="Команды для тех. персонала", value="page4"),
                disnake.SelectOption(label="Список серверов, подключённых к чату", value="page5"),
                disnake.SelectOption(label="Политика использования глобального чата", value="page6"),
            ],
            placeholder="Выберите одну из страниц",
            min_values=1,
            max_values=1,
        )
        self.pages = pages
        self.timeout = 30 
        self.message = None  

    async def callback(self, interaction: disnake.Interaction):
        page_index = int(self.values[0].split('page')[1]) - 1
        await interaction.response.edit_message(embed=self.pages[page_index], view=self.view)

    async def on_timeout(self):
        self.disabled = True

class MyView(disnake.ui.View):
    def __init__(self, pages: list[disnake.Embed]):
        super().__init__()
        self.add_item(MySelect(pages))
        self.message = None  
        self.timeout = 60  

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

class helpcog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.last_reset_time = datetime.now()

    @commands.slash_command(name='help', description='Отобразит краткую информацию по боту.')
    async def help(self, interaction: disnake.ApplicationCommandInteraction):
        global servers_added_today
        guild_id = interaction.guild.id
        settings = load_config(guild_id)
        chosen_color = get_color_from_config(settings)

        global_channel_id = settings.get("GLOBAL", None)
        if global_channel_id and int(global_channel_id) == interaction.channel.id:
            embed = create_embed(
                "Ошибка при попытке использовать команду",
                f"{base['ICON_PERMISSION']}  Команду нельзя использовать в канале глобального чата.",
                color=chosen_color
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        if datetime.now() - self.last_reset_time > timedelta(days=1):
            servers_added_today = 0
            self.last_reset_time = datetime.now()

        total_servers = len(self.bot.guilds)
        total_members = sum(len(guild.members) for guild in self.bot.guilds)
        total_channels = sum(len(guild.channels) for guild in self.bot.guilds)

        uptime_seconds = time.time() - self.start_time

        if uptime_seconds < 60:
            uptime = time.strftime("%S секунд назад", time.gmtime(uptime_seconds))
        elif uptime_seconds < 3600:
            uptime = time.strftime("%M минут назад", time.gmtime(uptime_seconds))
        elif uptime_seconds < 86400:
            uptime = time.strftime("%H часов назад", time.gmtime(uptime_seconds))
        else:
            uptime = f"{int(uptime_seconds // 86400)} дней назад"

        latency = self.bot.latency * 1000

        global_servers = []
        for guild in self.bot.guilds:
            guild_config = load_config(guild.id)
            if guild_config and guild_config.get("GLOBAL"):
                global_servers.append(guild.name)

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
                    name="• Игровые процессы:",
                    value="",
                    inline=False)
                .add_field(
                    name="</duel:1289624166416515162>   ⚔️",
                    value="Вызвать другого пользователя на дуэль.\nИспытайте свою удачу и стратегию в захватывающей схватке!",
                    inline=False) 
                .add_field(
                    name="</krestiki-noliki:1292244262972424283>   ❤️",
                    value="Начните классическую игру в крестики-нолики!\nПроверьте свою стратегию и постарайтесь победить противника.",
                    inline=False) 
                .add_field(
                    name="</start_game:1292549659369148477>   🚢",
                    value="Начните мини-игру морской бой!\nТопите корабли противника и покажите свою тактическую смекалку.",
                    inline=False) 
                .add_field(
                    name="</move:1292549659369148478>   🚀",
                    value="Атакуйте корабли противника в игре Морской бой.\nВыбирайте координаты и топите вражеские суда! ",
                    inline=False) 


                .add_field(
                    name="• Коллекционер карточек",
                    value="",
                    inline=False)
                .add_field(
                    name="</news:1289624166021992460>   🗞️",
                    value="Начните собирать карточки!\nПополняйте свою коллекцию уникальных карточек, погружаясь в мир увлекательных приключений.",
                    inline=False)
                .add_field(
                    name="</info_news:1289624166021992461>   🗞️",
                    value="Просмотрите свою коллекцию карточек!\nУзнайте, какие карточки у вас есть и сравнивайте свои достижения с другими коллекционерами!",
                    inline=False)



                .add_field(
                    name="• Взаимодействие с пользователями",
                    value="",
                    inline=False)
                .add_field(
                    name="</profile:1289624166504333396>   📊",
                    value="Посмотрите подробную статистику своего профиля.\nОтслеживайте свои достижения, рейтинг и  прогресс в различных играх.",
                    inline=False)
                .add_field(
                    name="</pay:1289624166416515165>   💵",
                    value="Отправьте деньги другому пользователю.\nПоделитесь своими заработанными ресурсами с друзьями или помогите нуждающимся. ",
                    inline=False)   
                .add_field(                 
                    name="</respect:1289624166021992459>   🔥",
                    value="Добавьте или уберите репутацию пользователя.\nОцените вклад других пользователей в сообщество и покажите им свою признательность!",
                    inline=False)                   
                .add_field(
                    name="</top_active:1289624166504333401>   🌟",
                    value="Посмотрите на 10 самых активных пользователей.\nУзнайте, кто из пользователей наиболее участвует в жизни сообщества! ",
                    inline=False)
                .add_field(
                    name="</top_balance:1289624166504333402>   💰",
                    value="Посмотрите на 10 пользователей с наибольшим балансом.\nУзнайте, кто из пользователей обладает наибольшим богатством!",
                    inline=False) 
                .add_field(
                    name="</report:1287062237248229407>   📝",
                    value="Отправьте жалобу на сообщение из глобального чата.\nСообщите модераторам о некорректном или нарушающем правила сообщества сообщении.",
                    inline=False)     



                .add_field(
                    name="• Взаимодействие с имуществом",
                    value="",
                    inline=False)
                .add_field(
                    name="</reward:1289624166416515161>   🎉",
                    value="Начните работать на одной из доступных работ.\nЗарабатывайте деньги, выполняя различные задания!",
                    inline=False)
                .add_field(
                    name="</buy_car:1289624166504333398>   🚗",
                    value="Купите новый автомобиль.\nВыбирайте из множества моделей и улучшайте свой автопарк!",
                    inline=False)
                .add_field(
                    name="</sellcar:1289624166504333397>   🚗",
                    value="Продайте свой автомобиль.\nОсвободите место для новых приобретений или получите дополнительный доход!",
                    inline=False)
                .add_field(
                    name="</buy_home:1289624166504333400>   🏡",
                    value="Купите дом/квартиру/особняк.\nОбзаведитесь собственным жильем и устройтесь поудобнее! ",
                    inline=False)
                .add_field(
                    name="</sellhome:1289624166504333399>  🏡",
                    value="Продайте дом/квартиру/особняк.\nПолучите прибыль от продажи недвижимости и инвестируйте в новые проекты!",
                    inline=False),                                

            disnake.Embed(title="Команды для персонала", color=chosen_color)
                .set_thumbnail(url=interaction.author.display_avatar)
                .add_field(
                    name="</add:1289624166416515164>   ➕",
                    value="Добавьте монеты пользователю.\nПополните баланс игрока и помогите ему продолжить приключения!",
                    inline=False)
                .add_field(
                    name="</set:1289624166416515163>   🏦",
                    value="Установите баланс для пользователя.\nИзмените количество монет на счету игрока.",
                    inline=False)
                .add_field(
                    name="</take:1289624166504333395>   ➖",
                    value="Уберите монеты у пользователя.\nСнимите монеты со счета игрока по необходимости.",
                    inline=False)
                .add_field(
                    name="</clear:1283133506578288687>   🧼",
                    value="Очистите чат от сообщений.\nУдалите ненужные сообщения и поддерживайте чистоту в чате.",
                    inline=False),

            disnake.Embed(title="Команды для тех. персонала", color=chosen_color) 
                .set_thumbnail(url=interaction.author.display_avatar) 
                .add_field(
                    name="</settings:1283133506297266344>   🌐",
                    value="Посмотреть текущие настройки сервера.\nПроверьте актуальные параметры и убедитесь в правильной работе сервера.",
                    inline=False) 
                .add_field(
                    name="</set_logs:1290700842361421929>   📜",
                    value="Установить канал для логов администрации.\nНастройте канал для отслеживания важных событий и действий администрации. ",
                    inline=False) 
                .add_field(
                    name="</set_color:1290700842361421932>   🎨",
                    value="Выбрать цвет для сообщений бота.\nИзмените цвет сообщений бота для более гармоничного внешнего вида.",
                    inline=False)
                .add_field(
                    name="</set_moderator:1290700842361421930>   📝",
                    value="Добавить новые id для стажёров сервера.\nРасширьте список стажеров и предоставьте им дополнительные возможности.",
                    inline=False)
                .add_field(
                    name="</set_global_chat:1290700842361421927>   🌍",
                    value="Добавить глобальный чат для этого сервера.\nСоздайте общее место для общения и обмена информацией между пользователями разных серверов.",
                    inline=False)
                .add_field(
                    name="</set_welcome_channel:1290700842361421926>   💼",
                    value="Добавить канал для приветствия пользователей.\nНастройте канал для приветствия новых пользователей и помогите им быстро адаптироваться на сервере.",
                    inline=False)
                .add_field(
                    name="</set_administrator:1290700842361421931>   ⚙️",
                    value="Добавить новые id для персонала сервера.\nРасширьте список персонала и предоставьте им дополнительные права и возможности.",
                    inline=False),

            disnake.Embed(title="Список серверов, подключённых к чату", color=chosen_color)
            .set_thumbnail(url=interaction.author.display_avatar)
            .add_field(
                name=f"Подключённые сервера:", 
                value=f"\n```{' • '.join(global_servers)}```" if global_servers else "Подключённых серверов сейчас нет.", 
                inline=False) 

            .add_field(
                name=f"Всего серверов: {len(global_servers)}" if global_servers else "", 
                value=f"", 
                inline=False),    

            disnake.Embed(title="Политика использования глобального чата", color=chosen_color) 
                .set_thumbnail(url=interaction.author.display_avatar) 

            .add_field(
                name="",
                value="**Общие положения:**\n"
                "1.0. Запрещён флуд и спам.\n"
                "1.1. Запрещены оскорбления в сторону других пользователей.\n"
                "1.2. Запрещено заводить темы о политике и религии.\n"
                "1.3. Запрещено рекламировать сервера и программы. (Исключение: YouTube)\n"
                "1.4. Запрещено злоупотребление ненормативной бранью.\n"
                "1.5. Запрещен любой порнографический контент.\n"
                "1.6. Запрещены теги @everyone и @here.\n"
                "1.7. Запрещено писать в чат бессмысленные наборы букв и умышленно коверкать слова вне шуточного контекста.\n"
                "1.8. Запрещено опубликовывать любую конфиденциальную информацию.\n"
                "1.9. Запрещено распространение фишинговых ссылок, сайтов, серверов (различные непонятные, малоизвестные, сомнительные ссылки).\n"
                "2.0. Запрещено публиковать личные переписки без разрешения всех участников переписки.\n\n", inline=False)

            .add_field(
                name="",
                value="**Ответственность:**\n"
                "2.1. За нарушение правил, к участникам применяются меры от предупреждения до ограничения доступа.\n"
                "2.2. Наказания действуют следующим образом:\n"
                "- Предупреждение Участник/Гильдия\n"
                "- Перманентный бан Участник/Гильдия\n"
                "2.3. Если в течение 30 дней после наказания пользователь совершает повторный проступок – применяется следующее в очереди наказание.\n"
                "2.4. В отдельных случаях, могут быть сделаны исключения в зависимости от тяжести проступка (на усмотрение модераторов).\n"
                "2.5. Если модерация не сможет получить доступ к общению с вами - вы будете заблокированы без предупреждений.\n"
                "2.6. Политика глобального чата может быть дополнена в любой момент, без упоминания и уведомления вас об этом.\n"
                "2.7. Если вы заметили нарушение в чате, используйте </report:1287062237248229407>.\n"
                "2.8. За ложный </report:1287062237248229407>, а также за подделку доказательств, предусмотрены наказания.", inline=False)

        ]
        view = MyView(pages)
        message = await interaction.send(embed=pages[0], view=view)
        view.message = message 
        view.children[0].message = message 

        await asyncio.sleep(120)
        await interaction.edit_original_message(embed=pages[0], view=None)