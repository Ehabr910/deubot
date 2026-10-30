from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import load_data, save_data

# استبدل الأرقام أدناه بمعرفات القنوات الخاصة بك
USERS_INFO_CHANNEL_ID = -1003805398009 
PRIVATE_CHANNEL_ID = -1004392734704

REGISTRATION_STATE = {}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    uid = str(user.id)
    data = load_data()

    if uid in data["banned"]:
        update.message.reply_text("❌ أنت محظور من استخدام البوت.")
        return

    if uid in data["users"]:
        show_tree_menu(update, context, "root")
        return

    if uid in data["pending_users"]:
        update.message.reply_text("⏳ طلبك قيد المراجعة من قبل الإدارة. يرجى الانتظار حتى تحصل على كود التفعيل.")
        return

    update.message.reply_text(
        "👋 أهلاً بك في البوت التعليمي.\n"
        "للاستفادة من محتويات البوت، يرجى تزويدنا بالمعلومات التالية:\n"
        "1️⃣ ما هو اسمك الثلاثي؟\n"
        "2️⃣ ما هو اختصاصك أو مستواك الدراسي؟\n\n"
        "أرسل إجابتك في رسالة واحدة وسنقوم بتحويلها للإدارة."
    )
    REGISTRATION_STATE[int(uid)] = True

def handle_user_text(update: Update, context: CallbackContext):
    user = update.effective_user
    uid = str(user.id)
    data = load_data()

    if uid in data["banned"]:
        return

    # التحقق من كود التفعيل (8 خانات)
    text = update.message.text.strip()
    if len(text) == 8 and text in data["codes"]:
        data["users"][uid] = {
            "id": user.id,
            "name": user.full_name,
            "username": user.username
        }
        del data["codes"][text]
        if uid in data["pending_users"]:
            del data["pending_users"][uid]
        save_data(data)
        
        update.message.reply_text("✅ تم تفعيل حسابك بنجاح! يمكنك الآن استخدام البوت.")
        show_tree_menu(update, context, "root")
        return

    # تسجيل بيانات الطالب الجديدة وإرسالها لقناة الإدارة
    if REGISTRATION_STATE.get(user.id):
        user_info = (
            f"👤 طلب تسحيل جديد:\n"
            f"• الاسم الكامل: {user.full_name}\n"
            f"• المعرف (ID): `{user.id}`\n"
            f"• اليوزرنيم: @{user.username if user.username else 'لا يوجد'}\n"
            f"• معلومات الطالب:\n{text}"
        )
        try:
            context.bot.send_message(chat_id=USERS_INFO_CHANNEL_ID, text=user_info, parse_mode="Markdown")
            data["pending_users"][uid] = {"name": user.full_name, "info": text}
            save_data(data)
            
            REGISTRATION_STATE.pop(user.id)
            update.message.reply_text("✅ تم إرسال معلوماتك بنجاح إلى الإدارة للمراجعة. سيتم تزويدك بالكود قريباً.")
        except Exception as e:
            update.message.reply_text("❌ حدث خطأ أثناء إرسال بياناتك، يرجى المحاولة لاحقاً.")
        return

    if uid not in data["users"]:
        update.message.reply_text("⚠️ يجب عليك إدخال كود التفعيل المكون من 8 خانات للاستمرار. إذا لم تكن تمتلكه، تواصل مع الإدارة عبر أمر /start.")

def show_tree_menu(update_or_query, context, node_id):
    data = load_data()
    tree = data["tree"]
    
    if node_id not in tree:
        return

    node = tree[node_id]
    keyboard = []

    for child_id in node.get("children", []):
        child_node = tree.get(child_id)
        if child_node:
            keyboard.append([InlineKeyboardButton(child_node["text"], callback_data=f"node_{child_id}")])

    if node["parent_id"]:
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"node_{node['parent_id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"📂 {node['text']}\nاختر من القائمة أدناه:"

    if isinstance(update_or_query, Update):
        update_or_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        try:
            update_or_query.edit_message_text(text, reply_markup=reply_markup)
        except:
            pass

def button_navigation_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = str(query.from_user.id)
    data = load_data()

    if uid in data["banned"]:
        query.answer("❌ أنت محظور.", show_alert=True)
        return

    query.answer()
    data_callback = query.data

    if data_callback.startswith("node_"):
        node_id = data_callback.split("_", 1)[1]
        tree = data["tree"]
        if node_id in tree:
            node = tree[node_id]
            if node["type"] == "folder":
                keyboard = []
                for child_id in node.get("children", []):
                    child_node = tree.get(child_id)
                    if child_node:
                        keyboard.append([InlineKeyboardButton(child_node["text"], callback_data=f"node_{child_id}")])
                if node["parent_id"]:
                    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"node_{node['parent_id']}")])
                
                try:
                    query.edit_message_text(f"📂 {node['text']}\nاختر القسم المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard))
                except:
                    pass
            elif node["type"] == "file":
                serial_num = node.get("serial_num")
                if serial_num and serial_num in data["serials"]:
                    channel_msg_id = data["serials"][serial_num]
                    try:
                        context.bot.copy_message(
                            chat_id=query.from_user.id,
                            from_chat_id=PRIVATE_CHANNEL_ID,
                            message_id=channel_msg_id
                        )
                        query.answer("📥 تم إرسال الملف بنجاح!", show_alert=False)
                    except Exception as e:
                        query.answer("⚠️ حدث خطأ أثناء إرسال الملف.", show_alert=True)
                else:
                    query.answer("❌ الملف غير متوفر حالياً.", show_alert=True)