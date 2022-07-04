import logging
import sys
from aiogram import Bot, Dispatcher, executor, types
import sqlite3
import json
import os

import secret_credentials

API_TOKEN = secret_credentials.bot['token']

REP_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_DIR = os.path.join(REP_DIR, 'users-info')
DB_ABSPATH = os.path.join(REP_DIR, 'data.db')

def create_logger():
    # Create logger for App
    logger = logging.getLogger('steam_accounts_checker')
    logger.setLevel(logging.DEBUG)

    # Create file handler with logs even debug messages
    # fh = logging.FileHandler('steam-accounts-checker.log', mode='w')
    # fh.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)8s --- %(message)s ' + '(%(filename)s:%(lineno)s)',datefmt='%Y-%m-%d %H:%M:%S')

    # fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)
    # logger.addHandler(fh)

    return logger

logger = create_logger()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_id
    await bot.send_message(user_id, """
You can send here a txt file with the accounts in the format:
login:password
login:password
login:password

Despite the fact that they use proxies, steem still asks for captcha, so for each account, you will need to enter your own captcha. Bot will send you captcha directly into the dialog and you will answer him. Your session is saved and you can stop at any time and continue at another time. Also, you can at any time unload a file with information about the accounts that the bot had time to check.

In order to start, just drop the file.

""")

@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    user_id = message.from_id
    await bot.send_message(user_id, 'Help your mom')

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def accounts_file(message: types.Message):
    if not message.from_user.is_bot:
        user_id = message.from_id
        
        user_dir_path = os.path.join(USERS_DIR, str(user_id))
        if not os.path.exists(user_dir_path):
            os.mkdir(user_dir_path)

        # Check if the session is closed
        session_lock_file_path = os.path.join(user_dir_path, '.session-lock')
        if os.path.exists(session_lock_file_path):
            await bot.send_message(user_id, 'First, finish working with the previous file.')
            return
        
        # Check if the user is in the table
        try:
            conn = sqlite3.connect(DB_ABSPATH)
            cur = conn.cursor()
            cur.execute(f'''SELECT * FROM Users WHERE telegram_id = "{user_id}"''')
            result = cur.fetchone()
        except Exception as e:
            pass
        
        # If the user is not in the table, add
        if result == None:
            try:
                conn = sqlite3.connect(DB_ABSPATH)
                cur = conn.cursor()
                cur.execute(f'''INSERT INTO Users(telegram_id, user_directory_abspath) VALUES("{user_id}", "{user_dir_path}")''')
                conn.commit()
                
                await bot.send_message(user_id, 'The session with you has been successfully created.')
            except Exception as e:
                pass
        
        # Close the session
        open(session_lock_file_path, 'a').close()

        user_steam_accounts_file_path = os.path.join(user_dir_path, 'steam-accounts.txt')
        await message.document.download(destination_file=user_steam_accounts_file_path)
        await bot.send_message(user_id, 'File successfuly downloaded.')
        
        await bot.send_message(user_id, 'Wait a little while. The time depends on the size of your file.')

        # Read data from a file
        with open(user_steam_accounts_file_path, 'r') as f:
            user_steam_accounts = list(filter(bool, f.read().split('\n')))
            f.close()
        
        # Delete file
        os.remove(user_steam_accounts_file_path)

        # Record all accounts in the database in the SteamAccounts table
        try:
            conn = sqlite3.connect(DB_ABSPATH)
            cur = conn.cursor()
            for account in user_steam_accounts:
                login = account.split(':')[0]
                password = account.split(':')[1]
                cur.execute(f'''INSERT INTO SteamAccounts(telegram_id, login, password) VALUES("{user_id}", "{login}", "{password}") ON CONFLICT DO NOTHING''')
            conn.commit()
        except Exception as e:
            pass
        
        #############################################################
        ############### Checking Steam Accounts #####################
        #############################################################

        # Open Session
        os.remove(session_lock_file_path)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)