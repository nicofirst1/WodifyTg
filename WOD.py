from random import randint

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext


def timer_init(name, freq, reps, chat_id):


    def callback_increasing(context: CallbackContext):
        job = context.job

        rnd_rep = randint(reps[0], reps[1])
        to_print = f"Are you ready for <b>{rnd_rep} {name}</b>?"

        inline = InlineKeyboardMarkup([
            [InlineKeyboardButton("Done", callback_data=f"/exc done {rnd_rep}"),
             InlineKeyboardButton("Skip", callback_data=f"/exc skip {rnd_rep}")],
        ])

        context.bot.send_message(chat_id=chat_id, text=to_print,
                                 reply_markup=inline, parse_mode="HTML",)

        rnd_freq = randint(freq[0], freq[1]) * 60

        job.interval += rnd_freq

    return callback_increasing
