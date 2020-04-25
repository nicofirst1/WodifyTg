from copy import copy
from random import randint

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, Filters, CommandHandler, \
    CallbackQueryHandler

from Other.utils import catch_exception, text_splitter_bytes
from WOD import timer_init

DEBUG = False


class Add:
    def __init__(self, updater, db):
        self.bot = updater.bot
        self.db = db
        self.updater = updater

        dispatcher = updater.dispatcher

        self.exercise_str = """Name: {}\nFrequency: {}\nRepetitions: {}"""

        self.inline = InlineKeyboardMarkup([[InlineKeyboardButton("Exit", callback_data="/add exit")]])
        dispatcher.add_handler(CallbackQueryHandler(self.exit, pattern="/add"))

        converstion = ConversationHandler(
            [CommandHandler('add', self.add, pass_user_data=True)],
            states={
                "name": [MessageHandler(Filters.text, self.get_name, pass_user_data=True)],
                "freq": [MessageHandler(Filters.text, self.get_freq, pass_user_data=True)],
                "reps": [MessageHandler(Filters.text, self.get_reps, pass_user_data=True)],

            }, fallbacks=[CommandHandler('Fine', self.exit, pass_user_data=True)])

        dispatcher.add_handler(converstion)

    def format_exercise(self, user_data):

        return f"<b>{self.exercise_str.format(user_data['name'], user_data['freq'], user_data['reps'])}</b>\n\n"

    @catch_exception
    def add(self, update, callback_context):

        user_data = callback_context.user_data
        # inizzializza i campi di user data
        user_data['name'] = None
        user_data['freq'] = None
        user_data['reps'] = None

        # aggiungo l'user nel db items se non è presente
        # if not DEBUG: self.db.add_user_to_items(update.message.from_user.id)

        msg = f"{self.format_exercise(user_data)}" \
              f"Please send me the exercise's name.\n" \
              f"You can click on exit to discard the current operation"
        msg_id = callback_context.bot.sendMessage(update.message.chat.id, msg, reply_markup=self.inline,
                                                  parse_mode="HTML")
        user_data['msg'] = msg_id

        return "name"

    @staticmethod
    def convert(text):

        try:
            text = [int(elem) for elem in text.strip().split(",")]
        except Exception:
            return None

        if len(text) != 2:
            return None

        if text[0] >= text[1]:
            return None

        return text

    def get_name(self, update, callback_context):

        user_data = callback_context.user_data
        bot = callback_context.bot

        if update.message.text == "Exit":
            return self.exit(bot, update, user_data)

        user_data['name'] = update.message.text

        msg = f"{self.format_exercise(user_data)}" \
              f"Now send me a frequency interval, use a comma (',') to separate the two numbers\n" \
              f"For example: 4,9 is correct"

        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )

        bot.edit_message_text(
            chat_id=user_data['msg'].chat_id,
            text=msg,
            message_id=user_data['msg'].message_id,
            parse_mode="HTML",
            reply_markup=self.inline,

        )

        return "freq"

    def get_freq(self, update, callback_context):

        user_data = callback_context.user_data
        bot = callback_context.bot

        text = update.message.text

        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )

        if self.convert(text) is None:
            bot.edit_message_text(
                chat_id=user_data['msg'].chat_id,
                text="Wrong formatting, try again\nInsert frequency range",
                message_id=user_data['msg'].message_id,
                parse_mode="HTML",
                reply_markup=self.inline,

            )
            return "freq"

        user_data['freq'] = self.convert(text)

        msg = f"{self.format_exercise(user_data)}" \
              f"Now send me a repetition interval, use a comma (',') to separate the two numbers\n" \
              f"For example: 10,20 is correct"

        bot.edit_message_text(
            chat_id=user_data['msg'].chat_id,
            text=msg,
            message_id=user_data['msg'].message_id,
            parse_mode="HTML",
            reply_markup=self.inline,

        )

        return "reps"

    def get_reps(self, update, callback_context):

        user_data = callback_context.user_data
        bot = callback_context.bot

        text = update.message.text

        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id,
        )

        if self.convert(text) is None:
            bot.edit_message_text(
                chat_id=user_data['msg'].chat_id,
                text="Wrong formatting, try again\nInsert repetition range",
                message_id=user_data['msg'].message_id,
                parse_mode="HTML",
                reply_markup=self.inline,

            )
            return "reps"

        user_data['reps'] = self.convert(text)

        msg = f"{self.format_exercise(user_data)}" \
              f"Now you can either save the exercise [Save], save and run it [Save n Run], or cancel [Exit]"

        inline = InlineKeyboardMarkup([
            [InlineKeyboardButton("Save", callback_data="/add save"),
             InlineKeyboardButton("Save n Run", callback_data="/add saverun")],
            [InlineKeyboardButton("Exit", callback_data="/add exit")]
        ])

        bot.edit_message_text(
            chat_id=user_data['msg'].chat_id,
            text=msg,
            message_id=user_data['msg'].message_id,
            parse_mode="HTML",
            reply_markup=inline,

        )

        return ConversationHandler.END

    @catch_exception
    def exit(self, update, callback_context):
        """Finisce la conversazione azzerando tutto
         msg: è il messaggio inviato all'utente
         return : fine conversazione"""

        data = update.callback_query.data.split(" ")[1]
        bot = callback_context.bot
        user_data = callback_context.user_data

        if data == "exit":
            bot.edit_message_text(
                chat_id=update.effective_message.chat_id,
                text="Operation canceled",
                message_id=update.effective_message.message_id,
                parse_mode="HTML",

            )
            return ConversationHandler.END

        elif "save" in data:
            # todo: add save
            bot.edit_message_text(
                chat_id=update.effective_message.chat_id,
                text="Operation completed",
                message_id=update.effective_message.message_id,
                parse_mode="HTML",

            )

            if "run" in data:
                # todo: run
                cb = timer_init(user_data['name'], user_data['freq'], user_data['reps'],
                                update.effective_message.chat_id)
                rnd_freq = randint(0, user_data['freq'][0]) * 60

                self.updater.job_queue.run_repeating(cb, rnd_freq, context=copy(user_data), name=user_data['name'])
            return ConversationHandler.END


class Stop:
    """
    Stop a job
    """
    def __init__(self, updater, db):
        self.bot = updater.bot
        self.db = db
        self.updater = updater

        dispatcher = updater.dispatcher

        dispatcher.add_handler(CallbackQueryHandler(self.stop, pattern="/stop"))
        dispatcher.add_handler(CommandHandler('stop', self.choose, pass_user_data=True))

    @catch_exception
    def choose(self, update, callback_context):

        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        jobs = callback_context.dispatcher.job_queue.jobs()

        msg = "Which one would you like to stop?"

        inlines = [InlineKeyboardButton(f"{j.name}", callback_data=f"/stop {j.name}") for j in jobs]
        inlines += [InlineKeyboardButton(f"Cancel", callback_data=f"/stop cancel")]

        if len(inlines) > 3:
            inlines = chunks(inlines, 3)
            inlines = list(inlines)
        else:
            inlines = [inlines]

        inline = InlineKeyboardMarkup(inlines)
        callback_context.bot.sendMessage(update.message.chat.id, msg, reply_markup=inline,
                                         parse_mode="HTML")

    @catch_exception
    def stop(self, update, callback_context):
        """Finisce la conversazione azzerando tutto
         msg: è il messaggio inviato all'utente
         return : fine conversazione"""

        data = update.callback_query.data.split(" ", 1)[1]
        bot = callback_context.bot

        if data == "cancel":
            bot.edit_message_text(
                chat_id=update.effective_message.chat_id,
                text="Operation canceled",
                message_id=update.effective_message.message_id,
                parse_mode="HTML",

            )

        else:
            # stop job
            callback_context.job_queue.get_jobs_by_name(data)[0].schedule_removal()
            bot.edit_message_text(
                chat_id=update.effective_message.chat_id,
                text=f"Exercise {data} stopped",
                message_id=update.effective_message.message_id,
                parse_mode="HTML",

            )


class Help:

    def __init__(self, updater, db):
        self.updater = updater
        self.db = db
        self.inline_cat = InlineKeyboardMarkup([
            [InlineKeyboardButton("Admin", callback_data="/help admin"),
             InlineKeyboardButton("User", callback_data="/help user"),
             InlineKeyboardButton("Developer", callback_data="/help developer")],
            [InlineKeyboardButton("Inoltro", callback_data="/help inoltro"),
             InlineKeyboardButton("Crediti", callback_data="/help crediti"),
             InlineKeyboardButton("Esci", callback_data="/help esci")]

        ])
        self.inline_page = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⬅️", callback_data="/help page_indietro"),
                InlineKeyboardButton("➡️", callback_data="/help page_avanti")],
            [InlineKeyboardButton("Torna al help", callback_data="/help page_esci")]

        ])

        disp = updater.dispatcher
        disp.add_handler(CommandHandler("help", self.help_init))

        disp.add_handler(CallbackQueryHandler(self.help_decision, pattern="/help", pass_user_data=True))

    def get_commands_help(self):
        """Prende le funzioni e relative doc dei metodi di Command
        @:return user, admin, developer: liste contenenti nome funzioni e doc"""
        funcs = []
        admin = []
        user = []
        developer = []

        # appende in tutte le liste nomeFunzione - doc
        for elem in funcs:
            if elem[0][0] == "A" and elem[1]:
                admin.append("/" + elem[0][1:] + "  " + elem[1].__doc__ + "\n")
            elif elem[0][0] == "U" and elem[1]:
                user.append("/" + elem[0][1:] + "  " + elem[1].__doc__ + "\n")

            elif elem[0][0] == "D" and elem[1]:
                developer.append("/" + elem[0][1:] + "  " + elem[1].__doc__ + "\n")

        # appende i comandi non prenseti in Command
        admin.append(
            "/resetboss - resetta i punteggi associati agli attacchi Boss di tutti, da usare con cautela poichè una volta cancellati, "
            "i punteggi non sono piu recuperabili")

        user.append("/attacchiBoss - Ti permette di visualizzare i punteggi di tutti i membri del team")
        user.append("/cercaCraft num1 num2 - Ti permette di cercare oggetti in base ai punti craft, rarità e "
                    "rinascita. Dato num1>num2 cerca oggetti craft con valore compreso tra num1 e num2 ")
        user.append("/compra - Ti permette di calcolare facilmente quanti scrigni comprare in base a sconti dell'"
                    "emporio e il tuo budget")
        user.append("/top - Ti permette di visualizzare la classifica dei top player in base a [pc totali, pc "
                    "settimanali, edosoldi, abilità, rango]")
        user.append("/teams - Visualizza i pc dei team presenti nella Hall of Fame e il relativo incremento")
        user.append(
            "/mancanti - Mostra tutti gli oggetti nel tuo zaino (non craftabili) che hanno una quantità inferiore a quella specificata")
        user.append("/diffschede - Visualizza la differenza in pc tra due schede 'Dettaglio Membri' in 'Team'")
        user.append(
            "/timerset hh:mm msg - setta un timer tra <b>hh</b> ore e <b>mm</b> minuti (si possono anche specificare solo le ore) e allo scadere del tempo invia il messaggio <b>msg</b>")
        user.append("/timerunset - Rimuove il timer precedentemente settato")
        user.append("/activity - Mostra varie informazioni del gruppo Fancazzisti")
        user.append(
            "/punteggioact - Visualizza il tuo punteggio, con punteggio maggiore sblocchi diverse funzionalità di activity")
        user.append("/classify - Permette di classificare i vari messaggi")
        user.append("/topunteggio - visualizza i punteggi della classifica di activity")
        user.append("/negozi - genera dei negozi a prezzo base a seconda del vostro zaino")

        return user, admin, developer

    def get_forward_commands(self):
        return """
<b>=====COMANDI DA INOLTRO=====</b>\n
I comandi da inoltro sono molteplici, verranno suddivisi in base al tipo di messaggio inoltrato.

<b>----Loot----</b>
Questo comando viene attivato quando inoltri il messaggio <b>/lista oggetto</b> da @craftlootbot.
Una volta inoltrato ti sarà chiesta quale informazione vuoi visualizzare tra le seguenti:
<b>Negozi</b>
Ti permette di ottenere una comoda stringa di negozi degli oggetti mancanti da poter inoltrare a @lootbotplus
<b>Ricerca</b>
Quando clicchi ricerca verranno automaticamente salvate le rarità che ti mancano per poter utilizzare il comando /compra
Questo comando prevede piu passi:
1) Una volta premuto il bottone ti saranno inviati dei messaggi "/ricerca oggetto1, oggetto2, oggetto3" per ogni oggetto che ti manca
2) Inoltra questi messaggi a @lootplusbot
3) Ri-inoltra i messaggi li @lootplusbot (quelli con i prezzi e i negozi) a @fancabot
4) Clicca stima per ottenere il costo tolate (comprendente acquisto degli oggetti e craft stesso), il tempo stimato per comprare gli oggetti, la top 10 degli oggetti piu costosi (solo se sono presenti 10 elementi o più)
5) Ti verrà chiesto se vuoi visualizzare i negozi, clicca <i>"Si"</i> per ottenere una lista di comandi <pre>@lootplusbot codiceNegozio</pre>, altrimenti <i>"No"</i> per annullare


<b>----Boss----</b>
Comando solo per <b>ADMIN</b>, per l'opzione user visualizzare il help del comando /attacchiboss
Questo comando viene attivato quando inoltri il messaggio <b>Team</b> di @lootgamebot
Potrete scegliere tra tre opzioni:
1) <i>Titan</i> : +1 punto per chi non ha attaccato
2) <i>Phoenix</i> : +2 punti per chi non ha attaccato
2) <i>Visualizza</i> : Permette di vedere le info senza salvare il punteggio
3) <i>Annulla</i> : se vi siete sbagliati
Scelto il tipo di boss verranno salvati i punti dei membri non attaccanti, ovviamente chi ha piu punti si trova in pericolo di kick dal team
<b>NB</b>: Se qualcuno dei membri NON ha inviato il comando /start al bot non saranno salvati i punti del suddetto, ma verrai notificato.
Successivamente potrete scegliere 4 opzioni:
1) <i>Completa</i> : Visualizza gli utenti divisi in due categorie, attaccanti (con danno, punteggio e attacchi), non attaccanti (con punteggio e occupazione corrente (cava, missione))
2) <i>Non Attaccanti</i> : Riceverai un messaggio con gli username di quelli che non hanno attaccato
3) <i>Punteggio</i> : Una lista ordinata di username con relativi punteggi
4) <i>Sveglia</i> : Manda un messaggio per incoraggare chi non ha attaccato a farlo
5) <i>Visualizza</i> : Permentte di vedere le informazioni senza salvare il punteggio
6) <i>Annulla</i> : Per completare la fase di visualizzazione
Per resettare i punteggi usa /resetboss, però fai attenzione poichè l'operazione non è reversibile

<b>----Top----</b>
Questo comando viene attivato inoltrando il messaggio <b>Giocatore</b> da @lootgamebot
Inviando il messaggio ggiornerai il database e potrai visualizzare la tuo posizione in classifica con gli altri membri.
La classifica mostra la data di aggiornamento e i punti realtivi a:
1) Punti craft totali
2) Punti craft settimanali
3) Edosoldi
4) Abilità
5) Rango 
La visualizzazione è anche disponibile tramite il comando /top, senza aggiornamento dei valori

<b>----Pietre del Drago----</b>
Questo comando viene attivato inoltrando il messagio <b>/zaino D</b> da @lootplusbot
Otterrai il valore (in exp drago) di tutte le pietre del drago che sono presenti nel tuo zaino nei seguenti formati:
1) Punti individuali per ogni pietra
2) Punti totali
3) Avanzamento in termini di livello del drago se decidi di nutrirlo con tutte le pietre

<b>----Teams----</b>
Questo comando viene attivato inoltrando il messaggio <b>Team->Hall of Fame</b> da @lootgamebot
Una volta inoltrato il messaggio ti verranno offerte varie scelte di visualizzazione:
1)<b>--Incremento--</b>
(<b>NB</b>: 'Inc' è un acronimo di incremento e fa riferimento alla variazione di pc):
1.1) <i>Inc Orario</i> : Mostra l'incremento orario medio di tutti i team presenti 
1.2) <i>Inc Giornaliero</i> : Mostra l'incremento giornaliero medio di tutti i team presenti 
1.3) <i>Inc Settimanale</i> : Mostra l'incremento settimanale medio di tutti i team presenti 
1.4) <i>Inc Mensile</i> : Mostra l'incremento mensile medio di tutti i team presenti 
1.5) <i>Inc Ultimo Aggiornamento </i> : Mostra l'incremento dall'ultimo aggiornamento 
1.6) <i>Inc Totale </i> : Mostra l'incremento totale dal primo messaggio ricevuto 
1.7) <i>Inc Totale Medio </i> : Mostra l'incremento totale medio dal primo messaggio ricevuto

2) <b>--Grafico--</b>
Invia una foto (in formato png) dell'andamento di tutti i team in termini ti pc totali. I pallini rappresentano un messaggio di inoltro ricevuto,  mentre le line compongono la curva di andamento

3) <b>--Stime--</b>
Le Stime rappresentano la classifica stimata in base all'unità di tempo, ovvero a quanti pc saranno arrivati i teams tra ore, giorni, settimane, mesi...
2.1) <i>Stima Orarie</i> : Mostra i pc stimati tra un ora 
2.2) <i>Stima Giornaliere</i> : Mostra i pc stimati tra un giorno 
2.3) <i>Stima Settimanali</i> : Mostra i pc stimati tra una settimana
2.4) <i>Stima Mensili</i> : Mostra i pc stimati tra un mese

4) <b>--Scalata--</b>
La scalata ti fornisce una sclassifica con i pc necessari per superare i team in testa a Fancazzisti. 
Come per gli altri comandi anche queste si dividono a seconda dell'unità di tempo, la sintassi è:
NomeTeam : pcNecessariPerSuperarlo (pcNecessariIndividuali)
4.1) <i>Scalata Oraria</i> : Mostra i pc necessari per superare il team in un ora
4.2) <i>Scalata Giornaliera</i> : Mostra i pc necessari per superare il team in un giorno
4.3) <i>Scalata Settimanale</i> : Mostra i pc necessari per superare il team in una settimana
4.4) <i>Scalata Mensile</i> : Mostra i pc necessari per superare il team in un mese

5) <b>--Classifica--</b>
Visualizza la classica calssifica della Hall of Fame

6) <b>--Esci--</b> 
Termina la visualizzazione

Per ora sarà possibile accedere a queste informaizoni solo tramite inoltro del messaggio <i>Hall of Fame</i>, poiche ad ogni ricezione vengono aggiungere dati su cui poter effettuare le stime.
Quando avremo raggiunto una sufficente quantita di dati salterà fuori un comando che non necesita di inoltro.
C'è anche da dire che alcune informazioni non sono ancora disponibili (Mensile e Giornaliero) per via della recente nascita del comando... tra un mese avremo a disposizione tutto
Prossimamente aggiungerò anche qualche tecnica di Inteligenza Artificiale al bot per fergli prevedere come sarà la classifica tra un tot di tempo (ore, giorni, settimane...), prorpio per questo vi invito a inoltrare piu messaggi possibili!

<b>----Crafter----</b>
Questo comando viene attivato inoltrando il messaggio <b>/craft->Messaggio</b> da @craftlootbot
Ti verranno inviati una serie di messaggi del tipo:
Crea oggetto1
si
Crea oggetto2
si
....
Da inoltrare a @lootgamebot per craftare velocemente (efficace specialmente con plus)

"""

    def get_credits(self):
        return """<b>=====CREDITI=====</b>\n
Crediti: @brandimax e @Odococo e un ringraziamento speciale a @DiabolicamenteMe per avermi aiutato ❤️.
Se hai idee o suggerimenti scrivici e non tarderemo a risponderti!
Votaci sullo <a href="https://telegram.me/storebot?start=fancazzisti_bot">Storebot</a>!
"""

    def help_init(self, bot, update):
        to_send = """Benvenuto nel FancaBot! Questo bot ha diverse funzionalità per semplificare il gioco @lootgamebot
Seleziona una categoria di comandi per imapararne l'utilizzo. Ricorda che ogni comando ha la seguente sintassi:
nomeComando parametri - spiegazione
Quindi ricorda di aggiungere i parametri giusti!"""
        update.message.reply_text(to_send, reply_markup=self.inline_cat)

    def help_decision(self, bot, update, user_data):
        """Visulauzza i vari help a seconda della scelta dell'user, supporta la creazione automati di piu pagine
        in caso di stringhe troppo lunghe"""
        # prendi la scelta dell'user (guarda CallbackQueryHandler)
        param = update.callback_query.data.split()[1]

        if 'page' not in user_data.keys():
            print("page not found!")
            user_data['page'] = 0

        if 'pages' not in user_data.keys(): user_data['pages'] = []

        user, admin, developer = self.get_commands_help()

        to_send = ""

        if param == "page_avanti":
            user_data['page'] += 1
            to_send = user_data['pages'][user_data['page'] - 1]

        elif param == "page_indietro":
            user_data['page'] -= 1
            to_send = user_data['pages'][user_data['page'] - 1]

        elif param == "page_esci":
            user_data['page'] = 0
            to_send = """Benvenuto nel FancaBot! Questo bot ha diverse funzionalità per semplificare il gioco @lootgamebot
Seleziona una categoria di comandi per imapararne l'utilizzo. Ricorda che ogni comando ha la seguente sintassi:
nomeComando parametri - spiegazione
Quindi ricorda di aggiungere i parametri giusti!"""
            bot.edit_message_text(
                chat_id=update.callback_query.message.chat_id,
                text=to_send,
                message_id=update.callback_query.message.message_id,
                reply_markup=self.inline_cat,
                parse_mode="HTML"

            )
            return

        if param == "esci":
            # elimina messaggio di scelta
            bot.delete_message(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id
            )
            bot.sendMessage(update.callback_query.message.chat.id, "Spero di esserti stato utile!")
            return
        elif param == "admin":

            to_send += "<b>=====COMANDI ADMIN=====</b>\n\n"
            # scrive tutti i comandi
            for elem in admin:
                to_send += elem + "\n\n"
            # dividi il messaggio a seconda della lunghezza in bytes
            to_send = text_splitter_bytes(to_send, splitter="\n\n")
            # se ci sono piu elementi manda solo il pirmo, vedi todo
            if len(to_send) > 1:
                user_data['pages'] = to_send

                if user_data['page'] == 0:
                    user_data['page'] = 1
                    to_send = to_send[0]
            # altrimenti usa il primo elemento
            else:
                to_send = to_send[0]


        elif param == "user":
            to_send += "<b>=====COMANDI USER=====</b>\n\n"

            for elem in user:
                to_send += elem + "\n\n"
            # dividi il messaggio a seconda della lunghezza in bytes
            to_send = text_splitter_bytes(to_send, splitter="\n\n")
            # se ci sono piu elementi manda solo il pirmo, vedi todo
            if len(to_send) > 1:
                user_data['pages'] = to_send

                if user_data['page'] == 0:
                    user_data['page'] = 1
                    to_send = to_send[0]
            # altrimenti usa il primo elemento
            else:
                to_send = to_send[0]


        elif param == "developer":
            to_send += "<b>=====COMANDI DEVELOPER=====</b>\n\n"

            for elem in developer:
                to_send += elem + "\n\n"
            # dividi il messaggio a seconda della lunghezza in bytes
            to_send = text_splitter_bytes(to_send, splitter="\n\n")
            # se ci sono piu elementi manda solo il pirmo, vedi todo
            if len(to_send) > 1:
                user_data['pages'] = to_send

                if user_data['page'] == 0:
                    user_data['page'] = 1
                    to_send = to_send[0]
            # altrimenti usa il primo elemento
            else:
                to_send = to_send[0]

        elif param == "inoltro":
            to_send += self.get_forward_commands()
            # print(to_send)
            # dividi il messaggio a seconda della lunghezza in bytes
            to_send = text_splitter_bytes(to_send, splitter="\n\n")
            # se ci sono piu elementi manda solo il pirmo, vedi todo
            if len(to_send) > 1:
                user_data['pages'] = to_send

                if user_data['page'] == 0:
                    user_data['page'] = 1
                    to_send = to_send[0]

            # altrimenti usa il primo elemento
            else:
                to_send = to_send[0]


        elif param == "crediti":
            to_send += self.get_credits()

        if user_data['page'] == 0:
            # modifica il messaggio con il to_send
            bot.edit_message_text(
                chat_id=update.callback_query.message.chat_id,
                text=to_send,
                message_id=update.callback_query.message.message_id,
                reply_markup=self.inline_cat,
                parse_mode="HTML"

            )
        else:
            # ultima pagina
            if user_data['page'] == len(user_data['pages']):
                bot.edit_message_text(
                    chat_id=update.callback_query.message.chat_id,
                    text=to_send,
                    message_id=update.callback_query.message.message_id,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️", callback_data="/help page_indietro")],
                        [InlineKeyboardButton("Torna al help", callback_data="/help page_esci")]]),
                    parse_mode="HTML"

                )
            # prima pagina
            elif user_data['page'] == 1:
                bot.edit_message_text(
                    chat_id=update.callback_query.message.chat_id,
                    text=to_send,
                    message_id=update.callback_query.message.message_id,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➡️", callback_data="/help page_avanti")],
                        [InlineKeyboardButton("Torna al help", callback_data="/help page_esci")]

                    ]),
                    parse_mode="HTML"

                )
            # pagine in mezzo
            else:
                bot.edit_message_text(
                    chat_id=update.callback_query.message.chat_id,
                    text=to_send,
                    message_id=update.callback_query.message.message_id,
                    reply_markup=self.inline_page,
                    parse_mode="HTML"

                )
