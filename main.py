import os
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from handlers_user import start, handle_user_text, button_navigation_handler
from handlers_admin import admin_panel, admin_callback_handler, handle_admin_text_inputs, ADMIN_IDS
from database import load_data

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في متغيرات البيئة!")

def main():
    load_data()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))

    dp.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_|^back_|^addto_"))
    dp.add_handler(CallbackQueryHandler(button_navigation_handler))

    # توجيه الرسائل النصية تلقائياً للأدمن أو المستخدم بناءً على القائمة
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: (
        handle_admin_text_inputs(update, context) if update.effective_user.id in ADMIN_IDS else handle_user_text(update, context)
    )))

    print("🤖 البوت يعمل الآن بنجاح...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()