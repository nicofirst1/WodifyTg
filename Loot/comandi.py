#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random
import time
from datetime import datetime, timedelta
from threading import Thread

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove)

from Loot.db_call import DB
from Other import utils

COMANDI_PLUS = """\n
/attacchiBoss - Ti permette di visualizzare i punteggi di tutti i membri del team in varie forme\n
/cercaCraft num1 num2 - Ti permette di cercare oggetti in base ai punti craft, rarità e rinascita. Dato num1>num2 cerca oggetti craft con valore compreso tra num1 e num2\n
/compra - ti permette di calcolare facilmente quanti scrigni comprare in base a sconti dell'emporio e il tuo budget\n
/resetBoss - resetta i punteggi associati agli attacchi al Boss di tutti\n
/top - ti permette di visualizzare la classifica dei top player in base a [pc totali, pc settimanali, edosoldi, abilità, rango)\n\n
<b>=====COMANDI DA INOLTRO=====</b>\n\n
"""

videos = {'loot': (
"Video tutorial su come utilizzare i messaggi di inoltro da @craftlootbot", "BAADBAADdgQAAkLEAAFRvQtpL8P36MkC"),
          'rarita': ("Tutorial su come utilizzare i comandi /compra e /rarita", "BAADBAADygIAAtD9GVEWYOqYqzCxvAI")}





# timer class
class Timer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop = False
        self.bot = None
        self.update = None
        self.date_time = None
        self.to_send_id = None

    def set_bot_update(self, bot, update):
        """Setter per bot e update"""
        self.bot = bot
        self.update = update
        self.to_send_id = update.effective_chat.id

    def set_hour(self, date_time):
        """Setta l'ora in cui far partire il timer
         #:param date_time: ora e data della fine del timer
         #:type: datetime"""

        self.date_time = date_time

    def stop_timer(self):
        self.stop = True

    def get_stop_event(self):
        """Ritorna lo stato del thread"""
        return self.stop and self.is_alive()

    def get_remning_time_str(self, string=True):
        """Ritorna la stringa con il tempo rimanente
        @:param string: boolena per ritornare in stringa o datetime
        @:type: bool
        #:return: str or datetime"""
        if not self.date_time:
            self.update.message.reply_text("Non c'è nessun timer impostato")
            return
        remaning_time = self.date_time - datetime.now()

        if string:
            return str(str(remaning_time.time()).split(".")[0])
        else:
            return remaning_time.time()

    def get_remaning_time(self):
        """Notifica l'utente del tempo rimanente"""
        self.update.message.reply_text("Mancano " + self.get_remning_time_str())

    def run(self):
        """Runna il timer"""
        if not self.date_time:
            self.bot.sendMessage(self.to_send_id, "Devi prima usare il comando /pinboss")
            return

        self.stop = False

        # prendi la differenza tra quanto c'è da aspettare e ora
        d, h, m = self.dates_diff(self.date_time)
        if h < 0:
            to_send = "scadrà tra " + str(int(m)) + " minuti"
        else:
            to_send = "scadrà tra " + str(int(h)) + " ore"
        self.bot.sendMessage(self.to_send_id, "Timer avviato!" + to_send)

        # se i minuti da aspettare sono meno di 10 usa quelli come wait time
        wait_time = 600
        if m < 600: wait_time = m

        # aspetta 10 minuti finche non viene stoppato
        while not self.stop:
            # se il tempo è terminato esci dal ciclo
            if datetime.now() == self.date_time: break
            time.sleep(5)

        self.bot.sendMessage(self.to_send_id, "Il timer è scaduto")

    def dates_diff(self, date_time):
        """Get the difference between a datetime and now
        @:param date_time: the date time
        @:type: datetime"""
        diff = datetime.now() - date_time
        days = diff.days
        days_to_hours = days * 24
        diff_btw_two_times = (diff.seconds) / 3600
        overall_hours = days_to_hours + diff_btw_two_times
        overall_minutes = overall_hours * 60

        return days, overall_hours, overall_minutes
