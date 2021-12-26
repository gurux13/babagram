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
    def __init__(self, hardware: Hardware):
        self.hardware = hardware
        self.name_map = {}
        self.name_map_fname = os.environ['HOME'] + '/babagram/name_map.pkl'
        self.bot: ExtBot = None
        self.private_config = PrivateConfig()
        try:
            self.load_mapping()
        except Exception as e:
            logger.error(str(e))
            pass
        global tg_instance
        if tg_instance is not None:
            raise Exception("Duplicate telegram - not allowed!")
        tg_instance = self

    def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        update.message.reply_markdown_v2(
            fr'Hi {user.mention_markdown_v2()}\!',
            reply_markup=ForceReply(selective=True),
        )

    def save_mapping(self):
        os.makedirs(os.path.dirname(self.name_map_fname), exist_ok=True)
        with open(self.name_map_fname, 'wb') as f:
            pickle.dump(self.name_map, f)

    def load_mapping(self):
        with open(self.name_map_fname, 'rb') as f:
            self.name_map = pickle.loads(f.read())

    def is_allowed_or_gtfo(self, update: Update):
        if not update.effective_user.id in self.private_config.allowed_ids:
            update.message.reply_text("Unregistered user " + update.effective_user.id)
            return False
        return True

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        if not self.is_allowed_or_gtfo(update):
            return
        update.message.reply_text('Help!')

    def dbg_print_command(self, update: Update, context: CallbackContext) -> None:
        self.

    def name_command(self, update: Update, context: CallbackContext) -> None:
        if not self.is_allowed_or_gtfo(update):
            return

        user = update.effective_user.id
        new_name = update.message.text.replace('/name ', '')
        if len(new_name) > 10:
            update.message.reply_text("Слишком длинное имя!")
            return
        self.name_map[user] = new_name
        update.message.reply_text("Ок, теперь Ваше имя " + new_name)
        self.save_mapping()

    def echo(self, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""
        if not self.is_allowed_or_gtfo(update):
            return
        had_name = False
        user_name = update.effective_user.name
        if update.effective_user.id in self.name_map:
            user_name = self.name_map[update.effective_user.id]
            had_name = True
        if not PaperStatus.instance().is_ok and is_pi:
            update.effective_message.reply_text("Проблема с бумагой - не могу напечатать...")
        else:
            Printer(self.hardware).print_img(print_message(user_name, update.message.text), 6000, 1)
            update.effective_message.reply_text(
                "Напечатано!" if had_name else "Напечатано, но... Установите имя командой /name !")

    def send_audio(self, filename, destination):
        id = self.private_config.destinations[destination]
        with open(filename, 'rb') as f:
            data = f.read()
            self.bot.send_voice(id, data)
    def send_text(self, text, destination):
        id = self.private_config.destinations[destination]
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
        dispatcher.add_handler(CommandHandler("name", self.name_command))
        dispatcher.add_handler(CommandHandler("beep", self.beep_command))

        # on non command i.e message - echo the message on Telegram
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.echo))

        # Start the Bot
        updater.start_polling()

        self.hardware.led(Hardware.Led.Ok, Hardware.LedMode.On)

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
