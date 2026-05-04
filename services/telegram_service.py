import telebot
import os
from flask import url_for

# Initialize bot with token from environment
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN) if TOKEN else None

class TelegramService:
    @staticmethod
    def send_notification(chat_id, message):
        """Send a message to a specific telegram chat"""
        if not bot or not chat_id:
            return False
        try:
            bot.send_message(chat_id, message, parse_mode='HTML')
            return True
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    @staticmethod
    def notify_ticket_called(ticket):
        """Notify client that their ticket is called"""
        if not ticket.telegram_chat_id:
            return
            
        message = (
            f"🔔 <b>Ваша очередь подошла!</b>\n\n"
            f"🎫 Талон: <b>{ticket.ticket_number}</b>\n"
            f"📍 Пожалуйста, пройдите к: <b>{ticket.window.name if ticket.window_id else 'окну обслуживания'}</b>\n\n"
            f"Ждем вас!"
        )
        TelegramService.send_notification(ticket.telegram_chat_id, message)

    @staticmethod
    def notify_ticket_cancelled(ticket):
        """Notify client that their ticket is cancelled"""
        if not ticket.telegram_chat_id:
            return
            
        message = (
            f"❌ <b>Ваш талон {ticket.ticket_number} был отменен.</b>\n"
            f"Если это ошибка, пожалуйста, обратитесь к администратору."
        )
        TelegramService.send_notification(ticket.telegram_chat_id, message)

# Simple bot polling logic (usually runs in a separate thread)
def start_bot_polling():
    if not bot:
        print("[!] Telegram Bot Token not found. Bot disabled.")
        return

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        text = (
            "👋 <b>Добро пожаловать в QueueSmart!</b>\n\n"
            "Я помогу вам отслеживать вашу очередь. "
            "Чтобы привязать талон, нажмите кнопку 'Уведомить в Telegram' на сайте."
        )
        bot.reply_to(message, text, parse_mode='HTML')

    @bot.message_handler(commands=['status'])
    def check_status(message):
        bot.reply_to(message, "Введите ваш номер талона (например, A-001):")

    print("[OK] Telegram Bot logic initialized. Starting polling...")
    bot.infinity_polling()
