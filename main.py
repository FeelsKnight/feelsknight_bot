from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functions import *
import logging
from keys import bot_token


def main():
    updater = Updater(bot_token)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('certify', certify_handler))
    dp.add_handler(CommandHandler('roll', roll))
    dp.add_handler(MessageHandler((Filters.photo | Filters.document) & Filters.text, certify_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
