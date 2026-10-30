import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import load_data, save_data, generate_activation_code

# قائمة معرفات الأدمنز (يمكنك إضافة أكثر من أدمن هنا مفصولين بفواصل)
ADMIN_IDS = [5037555049]  

ADMIN_STATE = {}

def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ أنت لست الأدمن المصرح له!")
        return

    keyboard = [
        [InlineKeyboardButton("➕ إضافة زر / ملف جديد للشجرة", callback_data="admin_add_button")],
        [InlineKeyboardButton("🔑 توليد كود تفعيل لطالب", callback_data="admin_gen_code")],
        [InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("ℹ️ إحصائيات البوت", callback_data="admin_info")]
    ]
    update.message.reply_text("⚙️ لوحة تحكم الأدمن الشاملة:", reply_markup=InlineKeyboardMarkup(keyboard))

def admin_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    uid = query.from_user.id
    if uid not in ADMIN_IDS:
        query.answer("❌ غير مسموح!", show_alert=True)
        return

    query.answer()
    data_callback = query.data
    data = load_data()

    if data_callback == "admin_gen_code":
        code = generate_activation_code()
        data["codes"][code] = "active"
        save_data(data)
        
        keyboard = [[InlineKeyboardButton("⬅️ رجوع لوحة التحكم", callback_data="back_admin")]]
        query.edit_message_text(
            f"🔑 تم توليد كود تفعيل جديد بنجاح:\n\n`{code}`\n\n"
            f"أعط هذا الكود للطالب ليقوم بإرساله للبوت فيتم تفعيل حسابه.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data_callback == "admin_users":
        text = "👥 المستخدمون المفعلون:\n"
        for u in data["users"].values():
            text += f"- {u['name']} (ID: `{u['id']}`)\n"
        if not data["users"]:
            text += "لا يوجد مستخدمون مفعلون بعد."
        
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_admin")]]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data_callback == "admin_info":
        text = (
            f"ℹ️ إحصائيات البوت:\n"
            f"• عدد المستخدمين المفعلين: {len(data['users'])}\n"
            f"• الطلبات المعلقة: {len(data['pending_users'])}\n"
            f"• الأزرار في الشجرة: {len(data['tree'])}\n"
            f"• السيريلات المخزنة: {len(data['serials'])}"
        )
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_admin")]]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data_callback == "back_admin":
        keyboard = [
            [InlineKeyboardButton("➕ إضافة زر / ملف جديد للشجرة", callback_data="admin_add_button")],
            [InlineKeyboardButton("🔑 توليد كود تفعيل لطالب", callback_data="admin_gen_code")],
            [InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("ℹ️ إحصائيات البوت", callback_data="admin_info")]
        ]
        query.edit_message_text("⚙️ لوحة تحكم الأدمن الشاملة:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data_callback == "admin_add_button":
        tree = data["tree"]
        keyboard = []
        for node_id, node_info in tree.items():
            if node_info["type"] == "folder":
                keyboard.append([InlineKeyboardButton(f"📁 وضع في: {node_info['text']}", callback_data=f"addto_{node_id}")])
        keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_admin")])
        query.edit_message_text("📂 اختر المجلد الأب الذي تريد إضافة الزر الجديد بداخله:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data_callback.startswith("addto_"):
        parent_id = data_callback.split("_", 1)[1]
        ADMIN_STATE[uid] = {"action": "waiting_button_details", "parent_id": parent_id}
        query.edit_message_text(
            "✍️ أرسل الآن تفاصيل الزر الجديد بالصيغة التالية في رسالة واحدة:\n\n"
            "`اسم الزر | نوع الزر (folder أو file) | الرقم التسلسلي (إذا كان file وإلا اكتب none)`\n\n"
            "مثال لمجلد فرعي:\n`الفصل الثالث | folder | none`\n\n"
            "مثال لملف نهائي:\n`محاضرة النحو | file | 105`",
            parse_mode="Markdown"
        )

def handle_admin_text_inputs(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    text = update.message.text.strip()
    state = ADMIN_STATE.get(uid)

    if state and state.get("action") == "waiting_button_details":
        try:
            parts = [p.strip() for p in text.split("|")]
            button_name = parts[0]
            button_type = parts[1]
            serial_num = parts[2] if len(parts) > 2 else "none"

            data = load_data()
            parent_id = state["parent_id"]

            new_node_id = f"node_{random.randint(1000, 99999)}"
            new_node = {
                "text": button_name,
                "parent_id": parent_id,
                "type": button_type
            }

            if button_type == "folder":
                new_node["children"] = []
            elif button_type == "file":
                new_node["serial_num"] = serial_num if serial_num != "none" else None

            data["tree"][new_node_id] = new_node
            if parent_id in data["tree"]:
                data["tree"][parent_id]["children"].append(new_node_id)

            save_data(data)
            ADMIN_STATE.pop(uid)

            update.message.reply_text(f"✅ تمت إضافة الزر '{button_name}' بنجاح إلى الهيكل الشجري!")
        except Exception as e:
            update.message.reply_text("❌ حدث خطأ في صيغة المدخلات. تأكد من استخدام الفاصلة العمودية `|` بالشكل الصحيح.")