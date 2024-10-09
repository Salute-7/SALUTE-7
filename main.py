import os
import json
import disnake
import tqdm
import time
import traceback
from utils.base.colors import colors
from disnake.ext import commands
from colorama import Fore, Style

from Events.main_events import events

from Commands.Moderator.clear import clear

from Commands.News.news import news
from Commands.News.info_news import info_news
from Commands.News.accept_trade import accept_trade
from Commands.News.trade_card import trade_card

from Commands.Admin.broadcast import broadcast
from Commands.Admin.vip import vip
from Commands.Admin.management import management
from Commands.Admin.r_vip import remove_vip
from Commands.Admin.show_blocked import show_blocked
from Commands.Admin.show_vip import show_vip
from Commands.Admin.show_admin import show_admin
from Commands.Admin.admin import admin
from Commands.Admin.r_admin import remove_admin

from Commands.Economy.pay import pay
from Commands.Economy.set import setcog
from Commands.Economy.add import add
from Commands.Economy.take import take
from Commands.Economy.reward import reward

from Commands.Game.duel import duel
from Commands.Game.krestiki import stonegame

from Commands.Other.help import helpcog
from Commands.News.news import news
from Commands.Other.report import report

from Commands.Shop.sellcar import sellcar
from Commands.Shop.buy_car import buy_car
from Commands.Shop.sellhome import sellhome
from Commands.Shop.buy_home import buy_home

from Commands.Statistica.respect import respect
from Commands.Statistica.profile import profile
from Commands.Statistica.top_active import top_active
from Commands.Statistica.top_balance import top_balance

from Commands.System.set_role_id import set_role_id
from Commands.System.set_logs import set_logs
from Commands.System.set_moderator import set_moderator
from Commands.System.set_administrator import set_administrator
from Commands.System.set_color import set_color
from Commands.System.settings import settings
from Commands.System.set_global_chat import set_global_chat
from Commands.System.set_welcome import set_welcome_channel

from Commands.Game.marinebattle import Battleship

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
            config = json.load(config_file)
            if "WEBHOOK" not in config:
                config["WEBHOOK"] = ""
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
            return config
    else:
        config = {"WEBHOOK": ""}
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return config

def get_color_from_config(settings):
    color_choice = settings.get('COLOR', 'default')
    return colors.get(color_choice.lower(), disnake.Color.orange())

def create_embed(title, description, color):
    embed = disnake.Embed(title=title, description=description, color=color)
    return embed
base = load_base()



def main():
    cogs = [
        respect,
        events,
        broadcast,
        news,
        info_news,
        accept_trade,
        trade_card,
        vip,
        remove_admin,
        admin,
        show_blocked,
        show_vip,
        show_admin,
        remove_vip,
        Battleship,
        report,
        management,
        set_welcome_channel,
        set_global_chat,
        set_role_id,
        set_logs,
        set_moderator,
        set_administrator,
        set_color,
        clear,
        settings,
        helpcog,
        reward,
        duel,
        setcog,
        stonegame,
        add,
        pay,
        take,
        profile,
        sellcar,
        buy_car,
        sellhome,
        buy_home,
        top_active,
        top_balance,
    ]

    tasks = [
        "Инициализация событий",
        "Загрузка команд",
        "Подключение к API",
        "Запуск бота",
    ]

    total_steps = len(cogs) + len(tasks)
    
    with tqdm.tqdm(total=total_steps, 
                    desc=Fore.YELLOW + "Запуск бота..." + Style.RESET_ALL,
                    bar_format='{desc}{percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} \033[0m \033[31m[{elapsed}<{remaining}, {rate_fmt} задача/s]\033[0m', 
                    colour="#a8a6f0") as pbar:   #a8a6f0  

        for cog in cogs:
            bot.add_cog(cog(bot))  
            time.sleep(0.1)
            pbar.set_description(Fore.YELLOW + f"Загрузка модуля: {cog.__name__}" + Style.RESET_ALL)
            pbar.update(1)

        for task in tasks:
            pbar.set_description(Fore.YELLOW + f"{task}" + Style.RESET_ALL)
            time.sleep(0.1)
            pbar.update(1)

    bot.run(base['TOKEN'])

if __name__ == "__main__":  
    main()