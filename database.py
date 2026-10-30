import os
import json
import random
import string

DATA_FILE = "bot_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "tree": {
                "root": {
                    "text": "القائمة الرئيسية",
                    "parent_id": None,
                    "type": "folder",
                    "children": ["year_1", "year_2", "year_3"]
                },
                "year_1": {
                    "text": "📘 السنة الأولى",
                    "parent_id": "root",
                    "type": "folder",
                    "children": []
                },
                "year_2": {
                    "text": "📗 السنة الثانية",
                    "parent_id": "root",
                    "type": "folder",
                    "children": []
                },
                "year_3": {
                    "text": "📙 السنة الثالثة",
                    "parent_id": "root",
                    "type": "folder",
                    "children": []
                }
            },
            "serials": {},         # ربط الرقم التسلسلي بمعرّف الرسالة في القناة الخاصة {"serial_num": channel_msg_id}
            "users": {},           # المستخدمون المفعلون {user_id: {"name": ..., "username": ...}}
            "pending_users": {},   # طلبات قيد المراجعة {user_id: {"name": ..., "info": ...}}
            "codes": {},           # الأكواد النشطة للتفعيل
            "banned": {}           # المستخدمون المحظورون
        }
        save_data(default_data)
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_activation_code():
    """توليد كود فريد من 8 خانات (حروف وأرقام)"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=8))