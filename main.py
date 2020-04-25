#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import codecs
import logging
import sys
from subprocess import call

import telegram
from telegram.ext import (
    Updater)

from Loot.bot_classes import *
from Loot.comandi import  videos
from Loot.db_call import DB, developer_dicts
from Other.track_activity import Track, TrackFilter
from Other.utils import (is_numeric, get_pretty_json)

# forzo l'installazione delle dipendenze
# call("pip install -r requirements.txt", shell=True)

# ==================GLOBAL VARIABLES==========================================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get('PORT', '5000'))

# ==================FUNCTIONS==========================================
bot_ids = [333089594, 490902479]



def get_user(user):
    user = {
        'id': user.id,
        'username': getattr(user, 'username', None),
        'first_name': getattr(user, 'first_name', None),
        'last_name': getattr(user, 'last_name', None),
        'language_code': getattr(user, 'language_code', None),
    }
    return user


def get_bot(bot):
    return get_user(bot)



def alarm(bot, job):
    """Function to send the alarm message"""
    bot.send_message(job.context, text='Beep!')





def error(bot, update, error):
    try:
        raise error
    except telegram.error.Unauthorized:
        for val in developer_dicts.values():
            bot.send_message(val, "Unauthorized Error!")
            bot.send_message(val, str(error))

            bot.send_message(val, get_pretty_json(str(update)))
            bot.send_message(val, str(bot))

    except telegram.error.BadRequest:
        if "Message is not modified" in str(error): return
        for val in developer_dicts.values():
            bot.send_message(val, "BadRequest Error!")
            bot.send_message(val, str(error))

            bot.send_message(val, get_pretty_json(str(update)))
            bot.send_message(val, str(bot))
    except telegram.error.TimedOut:
        for val in developer_dicts.values():
            bot.send_message(val, "TimedOut Error!")
            bot.send_message(val, str(error))

            bot.send_message(val, get_pretty_json(str(update)))
            bot.send_message(val, str(bot))
            # handle slow connection problems
    except telegram.error.NetworkError:
        for val in developer_dicts.values():
            bot.send_message(val, "NetworkError Error!")
            bot.send_message(val, str(error))

            bot.send_message(val, get_pretty_json(str(update)))
            bot.send_message(val, str(bot))
    except telegram.error.ChatMigrated as e:
        for val in developer_dicts.values():
            bot.send_message(val, "NetworkError Error!")
            bot.send_message(val, str(error))
            bot.send_message(val, get_pretty_json(str(update)))
            bot.send_message(val, str(bot))
    except telegram.error.TelegramError:
        for val in developer_dicts.values():
            bot.send_message(val, "TelegramError Error!")
            bot.send_message(val, str(error))
            bot.send_message(val, get_pretty_json(str(update)))
            bot.send_message(val, str(bot))
            bot.send_message(val, str(error))
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def log_update(bot, update):
    logger.info(update)

def exc_saver(update, callback_context):
    """
    Saves the output of a job
    :param update:
    :param callback_context:
    :return:
    """
    data = update.callback_query.data.split(" ",1)[1]
    data,rep=data.split(" ")
    bot = callback_context.bot
    user_data = callback_context.user_data

    if data == "done":
        # todo: add save
        bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text=f"You completed <b>{rep} {user_data['name']}</b>",
            message_id=update.effective_message.message_id,
            parse_mode="HTML",

        )
        return ConversationHandler.END

    else:
        bot.edit_message_text(
            chat_id=update.effective_message.chat_id,
            text=f"You skipped <b>{rep} {user_data['name']}</b>",
            message_id=update.effective_message.message_id,
            parse_mode="HTML",

        )



# ==================MAIN==========================================


def main():
    db = DB()  # database

    debug = True
    token = str(1135712682) +":"+ db.get_token(1135712682)['token']
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers
    disp = updater.dispatcher


    # classi per craftlootbot e comandi boss

    Add(updater, db)
    Stop(updater, db)

    disp.add_handler(CallbackQueryHandler(exc_saver, pattern="/exc"))

    #Help(updater, db)

    #Alarm(updater, db)


    # log all errors
    disp.add_error_handler(error)

    # Start the Bot
    if debug:
        updater.start_polling()
    else:
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path="main")
        updater.bot.set_webhook("https://git.heroku.com/wodifybot.git/main.py")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
