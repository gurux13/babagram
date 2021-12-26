#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os

from telegram import Update, ForceReply, Voice
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ExtBot

# Enable logging
from hardware import Hardware, is_pi
from image import print_message
from paper_status import PaperStatus
from printer import Printer
import pickle

from private_config import PrivateConfig

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

tg_instance = None


class Telegram:
    def __init__(self, hardware: Hardware, ):
        self.hardware = hardware
        self.bot: ExtBot = None
        self.private_config = PrivateConfig()
        self.on_sos_cancel = None
        self.on_dbg_print = None
        global tg_instance
        if tg_instance is not None:
            raise Exception("Duplicate telegram - not allowed!")
        tg_instance = self

    def set_sos_cancel_callback(self, on_sos_cancel):
        self.on_sos_cancel = on_sos_cancel
    def set_dbgprint_callback(self, on_dbg_print):
        self.on_dbg_print = on_dbg_print
    def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        update.message.reply_markdown_v2(
            fr'Hi {user.mention_markdown_v2()}\!',
            reply_markup=ForceReply(selective=True),
        )

    def is_allowed_or_gtfo(self, update: Update):
        if not update.effective_user.id in self.private_config.allowed_ids:
            update.message.reply_text("Unregistered user " + update.effective_user.id)
            return False
        return True

    def sos_cancel_command(self, update: Update, context: CallbackContext) -> None:
        self.on_sos_cancel(update)

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        if not self.is_allowed_or_gtfo(update):
            return
        update.message.reply_text('Help!')

    def dbg_print_command(self, update: Update, context: CallbackContext) -> None:
        self.on_dbg_print(update)

    def echo(self, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""
        if not self.is_allowed_or_gtfo(update):
            return

        had_name = False
        user_name = update.effective_user.name
        idx = self.private_config.destinations.index(update.effective_user.id)
        if idx is not None:
            user_name = self.private_config.names[idx]
            had_name = True
        if not PaperStatus.instance().is_ok and is_pi:
            update.effective_message.reply_text("Проблема с бумагой - не могу напечатать...")
        else:
            update.message.reply_text("Печатаем...")
            Printer(self.hardware).print_img(print_message(user_name, update.message.text, update.message.date))
            self.hardware.buzz(130, 0, 5, 0)
            update.effective_message.reply_text(
                "Напечатано!" if had_name else "Напечатано, но... Установите имя командой /name !")

    def send_audio(self, filename, destination):
        id = self.private_config.destinations[destination]
        if id == 0:
            return
        with open(filename, 'rb') as f:
            data = f.read()
            self.bot.send_voice(id, data)
    def send_text(self, text, destination):
        id = self.private_config.destinations[destination]
        if id == 0:
            return

        self.bot.send_message(id, text)


    def beep_command(self, update: Update, context: CallbackContext) -> None:
        if not self.is_allowed_or_gtfo(update):
            return
        self.hardware.buzz(128, 140, 4, 1)
        update.effective_message.reply_text("Попищали!")
        # update.message.reply_text("Напечатано!" if had_name else "Напечатано, но... Установите имя командой /name !")

    def main(self) -> None:
        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        updater = Updater(self.private_config.token, use_context=True)

        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher
        self.bot = updater.bot
        try:
            updater.bot.send_message(self.private_config.admin_id, "Система запущена")
        except:
            pass

        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", self.start))
        dispatcher.add_handler(CommandHandler("help", self.help_command))
        dispatcher.add_handler(CommandHandler("beep", self.beep_command))
        dispatcher.add_handler(CommandHandler("stopsos", self.sos_cancel_command))
        dispatcher.add_handler(CommandHandler("dbgprint", self.dbg_print_command))

        # on non command i.e message - echo the message on Telegram
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.echo))

        # Start the Bot
        updater.start_polling()

        self.hardware.led(Hardware.Led.Ok, Hardware.LedMode.On)

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
