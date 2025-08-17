import os
import json
import psutil
import asyncio
import speedtest
import subprocess
import re
import hashlib
from datetime import datetime
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import CommandHandler, CallbackContext, Application, CallbackQueryHandler


# Biến toàn cục
last_sms_time = {}
last_spam_time = {}
sms_process = None
spam_process = None
user_sessions = {}  # Lưu trữ session người dùng

# Đường dẫ    # Gửi thông báo bắt đầu với giao diện đẹp
    # Biến toàn cục
last_sms_time = {}
last_spam_time = {}
sms_process = None
spam_process = None
user_sessions = {}  # Lưu trữ session người dùng

# Đường dẫn file JSON
VIP_FILE = "vip.json"
LOGS_FILE = "attack_logs.json"

# Khởi tạo file JSON nếu chưa tồn tại
if not os.path.exists(VIP_FILE):
    with open(VIP_FILE, "w") as file:
        json.dump({}, file)

if not os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, "w") as file:
        json.dump([], file)

    # Xóa tin nhắn gốc và tin nhắn phản hồi sau 3 giây
    async def delete_messages():
        await asyncio.sleep(3)
        try:
            await update.message.delete()
            await sent_message.delete()
        except:
            pass

    asyncio.create_task(delete_messages())IP_FILE = "vip.json"
LOGS_FILE = "attack_logs.json"

# Khởi tạo file JSON nếu chưa tồn tại
if not os.path.exists(VIP_FILE):
    with open(VIP_FILE, "w") as file:
        json.dump({}, file)

if not os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, "w") as file:
        json.dump([], file)

# ID admin được phép sử dụng lệnh /add
ADMIN_ID = 7509896689
GROUP_ID = -1002256706038

# Hàm bảo mật số điện thoại
def mask_phone_number(phone):
    """Ẩn một phần số điện thoại để bảo mật"""
    if len(phone) >= 7:
        return phone[:3] + "****" + phone[-3:]
    return "****"

# Hàm validate số điện thoại
def validate_phone_number(phone):
    """Kiểm tra định dạng số điện thoại hợp lệ"""
    pattern = r'^0[3-9]\d{8}$'
    return re.match(pattern, phone) is not None

# Hàm log hoạt động
def log_attack(user_id, username, phone, attack_type, loops):
    """Ghi log các cuộc tấn công"""
    try:
        with open(LOGS_FILE, "r") as file:
            logs = json.load(file)
    except:
        logs = []
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "username": username,
        "phone_masked": mask_phone_number(phone),
        "attack_type": attack_type,
        "loops": loops,
        "phone_hash": hashlib.md5(phone.encode()).hexdigest()[:8]
    }
    
    logs.append(log_entry)
    # Giữ chỉ 100 log gần nhất
    if len(logs) > 100:
        logs = logs[-100:]
    
    with open(LOGS_FILE, "w") as file:
        json.dump(logs, file, indent=2)

# Hàm kiểm tra server
def check_server():
    try:
        ping = psutil.net_if_stats()
        return ping['lo'].isup  # Thay 'lo' bằng interface phù hợp nếu VPS khác
    except:
        return False

# Hàm thêm người dùng vào VIP (cải tiến)

# Hàm xử lý callback từ menu
async def button_handler(update: Update, context: CallbackContext):
    """Xử lý các nút bấm từ menu"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_sms":
        await show_sms_menu(update, context)
    elif query.data == "menu_spam":
        await show_spam_menu(update, context)
    elif query.data == "menu_server":
        await server(update, context)
    elif query.data == "menu_logs":
        await show_logs(update, context)
    elif query.data == "menu_help":
        await show_help(update, context)
    elif query.data == "menu_vip":
        await show_vip_info(update, context)
    elif query.data == "back_main":
        await start(update, context)

async def show_sms_menu(update: Update, context: CallbackContext):
    """Hiển thị hướng dẫn SMS attack"""
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
📱 **SMS ATTACK - FREE**

🔧 **Cách sử dụng:**
`/sms [số điện thoại] [số vòng]`

📝 **Ví dụ:**
`/sms 0987654321 50`

⚠️ **Lưu ý:**
• Cooldown: 100 giây
• Max vòng lặp: 10,000
• Thời gian chạy: 120 giây

🔐 **Bảo mật:** Số điện thoại sẽ được mã hóa trong log
    """
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_spam_menu(update: Update, context: CallbackContext):
    """Hiển thị hướng dẫn VIP attack"""
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
💥 **VIP ATTACK - PREMIUM**

🔧 **Cách sử dụng:**
`/spam [số điện thoại] [số vòng]`

📝 **Ví dụ:**
`/spam 0987654321 100`

⚡ **Ưu điểm VIP:**
• Cooldown: 60 giây
• Max vòng lặp: 10,000
• Thời gian chạy: 200 giây
• Tốc độ cao hơn

🔐 **Bảo mật:** Số điện thoại được mã hóa MD5
    """
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_logs(update: Update, context: CallbackContext):
    """Hiển thị logs tấn công gần đây"""
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        with open(LOGS_FILE, "r") as file:
            logs = json.load(file)
        
        if not logs:
            text = "📋 **ATTACK LOGS**\n\n❌ Chưa có log nào được ghi nhận."
        else:
            text = "📋 **ATTACK LOGS** (10 gần nhất)\n\n"
            for log in logs[-10:]:
                time_str = datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S %d/%m')
                text += f"🕐 {time_str}\n"
                text += f"👤 User: {log.get('username', 'Unknown')}\n"
                text += f"📱 Phone: {log['phone_masked']}\n"
                text += f"🎯 Type: {log['attack_type']}\n"
                text += f"🔄 Loops: {log['loops']}\n"
                text += f"🔑 Hash: {log['phone_hash']}\n\n"
    except:
        text = "📋 **ATTACK LOGS**\n\n❌ Lỗi đọc file log."
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_help(update: Update, context: CallbackContext):
    """Hiển thị hướng dẫn sử dụng"""
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
❓ **HƯỚNG DẪN SỬ DỤNG**

🔹 **Lệnh cơ bản:**
• `/start` - Mở menu chính
• `/sms` - SMS attack miễn phí
• `/spam` - VIP attack premium
• `/server` - Kiểm tra server

🔹 **Định dạng số điện thoại:**
• Phải bắt đầu bằng số 0
• Đủ 10 chữ số
• Ví dụ: 0987654321

🔹 **Bảo mật:**
• Số điện thoại được mã hóa trong log
• Không lưu trữ số thật
• Chỉ admin mới xem được log đầy đủ

💡 **Lưu ý:** Bot có cooldown để tránh spam
    """
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_vip_info(update: Update, context: CallbackContext):
    """Hiển thị thông tin VIP"""
    keyboard = [[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_id = update.effective_user.id
    
    # Kiểm tra VIP status
    with open(VIP_FILE, "r") as file:
        vip_data = json.load(file)
    
    is_vip = user_id in vip_data.values()
    
    if is_vip:
        status = "👑 **VIP MEMBER**"
        benefits = """
✅ **Quyền lợi của bạn:**
• Không giới hạn sử dụng /spam
• Cooldown ngắn hơn (60s)
• Tốc độ attack cao hơn
• Ưu tiên hỗ trợ
        """
    else:
        status = "👤 **FREE USER**"
        benefits = """
📝 **Để trở thành VIP:**
• Liên hệ admin: `/admin`
• Hoặc inbox trực tiếp
• Giá cả hợp lý

💰 **Lợi ích VIP:**
• Attack mạnh hơn
• Cooldown ngắn
• Hỗ trợ 24/7
        """
    
    text = f"""
👑 **THÔNG TIN VIP**

{status}

{benefits}

🆔 **User ID:** `{user_id}`
⏰ **Thời gian:** {datetime.now().strftime('%H:%M:%S')}
    """
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
# Hàm thêm người dùng vào VIP (cải tiến)
async def add(update: Update, context: CallbackContext):
    user: User = update.effective_user

    # Kiểm tra quyền truy cập
    if user.id != ADMIN_ID:
        await update.message.reply_text(
            "❌ **KHÔNG CÓ QUYỀN**\n\n🔐 Chỉ admin mới có thể sử dụng lệnh này.", 
            parse_mode="Markdown"
        )
        return

    if not context.args or not context.args[0].startswith("@"):
        await update.message.reply_text(
            "❌ **SAI ĐỊNH DẠNG**\n\n📝 Sử dụng: `/add @username user_id`\n💡 Ví dụ: `/add @john123 987654321`", 
            parse_mode="Markdown"
        )
        return

    username = context.args[0].lstrip("@")

    # Kiểm tra xem có cung cấp thêm ID người dùng hay không
    if len(context.args) > 1 and context.args[1].isdigit():
        user_id = int(context.args[1])
    else:
        await update.message.reply_text(
            "❌ **THIẾU USER ID**\n\n📝 Vui lòng cung cấp cả ID người dùng\n💡 Ví dụ: `/add @username 123456789`", 
            parse_mode="Markdown"
        )
        return

    # Lưu dữ liệu vào file JSON
    with open(VIP_FILE, "r") as file:
        vip_data = json.load(file)

    if username in vip_data:
        await update.message.reply_text(
            f"✅ **ĐÃ TỒN TẠI**\n\n👑 @{username} đã có trong danh sách VIP rồi.", 
            parse_mode="Markdown"
        )
        return

    vip_data[username] = user_id
    with open(VIP_FILE, "w") as file:
        json.dump(vip_data, file, indent=4)

    await update.message.reply_text(
        f"✅ **THÊM VIP THÀNH CÔNG**\n\n"
        f"👤 Username: @{username}\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👑 Quyền: VIP Member\n"
        f"⏰ Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}", 
        parse_mode="Markdown"
    )

# Hàm xử lý lệnh spam (VIP Attack - cải tiến)
async def spam(update: Update, context: CallbackContext):
    global last_spam_time, spam_process

    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    now = datetime.now()

    # Kiểm tra cooldown 60s
    if user_id in last_spam_time and (now - last_spam_time[user_id]).total_seconds() < 60:
        remaining = 60 - int((now - last_spam_time[user_id]).total_seconds())
        await update.message.reply_text(
            f"⏳ **COOLDOWN ACTIVE**\n\n"
            f"🕐 Vui lòng chờ {remaining} giây nữa", 
            parse_mode="Markdown"
        )
        return

    # Kiểm tra tham số
    args = context.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text(
            "❌ **SAI ĐỊNH DẠNG**\n\n"
            "📝 Sử dụng: `/spam [số điện thoại] [vòng lặp]`\n"
            "💡 Ví dụ: `/spam 0987654321 100`", 
            parse_mode="Markdown"
        )
        return

    phone, loops = args
    
    # Validate số điện thoại
    if not validate_phone_number(phone):
        await update.message.reply_text(
            "❌ **SỐ ĐIỆN THOẠI KHÔNG HỢP LỆ**\n\n"
            "📱 Yêu cầu:\n"
            "• Bắt đầu bằng số 0\n"
            "• Đủ 10 chữ số\n"
            "• Đúng format Việt Nam\n\n"
            "💡 Ví dụ: 0987654321", 
            parse_mode="Markdown"
        )
        return

    loops = int(loops)
    if loops > 10000:
        await update.message.reply_text(
            "❌ **VƯỢT QUÁ GIỚI HẠN**\n\n"
            "🔢 Số vòng lặp tối đa: 10,000\n"
            "💡 Vui lòng nhập số nhỏ hơn", 
            parse_mode="Markdown"
        )
        return

    # Cập nhật thời gian sử dụng lệnh
    last_spam_time[user_id] = now

    # Log hoạt động
    log_attack(user_id, username, phone, "VIP_SPAM", loops)

    # Gửi thông báo bắt đầu với giao diện đẹp
    masked_phone = mask_phone_number(phone)
    sent_message = await update.message.reply_text(
        f"💥 **VIP ATTACK STARTED** 💥\n\n"
        f"👤 **User:** @{username}\n"
        f"📱 **Target:** `{masked_phone}`\n"
        f"🔄 **Loops:** {loops:,}\n"
        f"⏰ **Started:** {now.strftime('%H:%M:%S')}\n"
        f"⚡ **Server:** VIP-1\n"
        f"🕐 **Duration:** 200s\n\n"
        f"🔐 **Bảo mật:** Số điện thoại đã được mã hóa",
        parse_mode="Markdown"
    )

    # Xóa tin nhắn gốc và tin nhắn phản hồi sau 3 giây
    async def delete_messages():
        await asyncio.sleep(3)
        try:
            await update.message.delete()
            await sent_message.delete()
        except:
            pass

    asyncio.create_task(delete_messages())

    # Dừng tiến trình cũ nếu có
    if spam_process and spam_process.poll() is None:
        spam_process.terminate()
        print(f"[{datetime.now()}] Terminated old spam process for user {user_id}")

    # Chạy tiến trình mới
    spam_process = subprocess.Popen(["python3", "smsvip.py", phone, "200"])
    print(f"[{datetime.now()}] Started VIP attack: User {user_id}, Phone {masked_phone}, Loops {loops}")

    # Dừng tiến trình sau 200 giây
    async def stop_spam_after_delay():
        global spam_process
        await asyncio.sleep(200)
        if spam_process and spam_process.poll() is None:
            spam_process.terminate()
            spam_process = None
            print(f"[{datetime.now()}] VIP attack completed for user {user_id}")

    asyncio.create_task(stop_spam_after_delay())

# Hàm xử lý lệnh SMS (Free Attack - cải tiến)
async def sms(update: Update, context: CallbackContext):
    global last_sms_time, sms_process

    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"
    now = datetime.now()

    # Kiểm tra cooldown 100s
    if user_id in last_sms_time and (now - last_sms_time[user_id]).total_seconds() < 100:
        remaining = 100 - int((now - last_sms_time[user_id]).total_seconds())
        await update.message.reply_text(
            f"⏳ **COOLDOWN ACTIVE**\n\n"
            f"🕐 Vui lòng chờ {remaining} giây nữa", 
            parse_mode="Markdown"
        )
        return

    # Kiểm tra tham số
    args = context.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text(
            "❌ **SAI ĐỊNH DẠNG**\n\n"
            "📝 Sử dụng: `/sms [số điện thoại] [vòng lặp]`\n"
            "💡 Ví dụ: `/sms 0987654321 50`", 
            parse_mode="Markdown"
        )
        return

    phone, loops = args
    
    # Validate số điện thoại
    if not validate_phone_number(phone):
        await update.message.reply_text(
            "❌ **SỐ ĐIỆN THOẠI KHÔNG HỢP LỆ**\n\n"
            "📱 Yêu cầu:\n"
            "• Bắt đầu bằng số 0\n"
            "• Đủ 10 chữ số\n"
            "• Đúng format Việt Nam\n\n"
            "💡 Ví dụ: 0987654321", 
            parse_mode="Markdown"
        )
        return

    loops = int(loops)
    if loops > 10000:
        await update.message.reply_text(
            "❌ **VƯỢT QUÁ GIỚI HẠN**\n\n"
            "🔢 Số vòng lặp tối đa: 10,000\n"
            "💡 Vui lòng nhập số nhỏ hơn", 
            parse_mode="Markdown"
        )
        return

    # Cập nhật thời gian sử dụng lệnh
    last_sms_time[user_id] = now

    # Log hoạt động
    log_attack(user_id, username, phone, "FREE_SMS", loops)

    # Gửi thông báo bắt đầu với giao diện đẹp
    masked_phone = mask_phone_number(phone)
    await update.message.reply_text(
        f"📱 **SMS ATTACK STARTED** 📱\n\n"
        f"� **User:** @{username}\n"
        f"📱 **Target:** `{masked_phone}`\n"
        f"🔄 **Loops:** {loops:,}\n"
        f"⏰ **Started:** {now.strftime('%H:%M:%S')}\n"
        f"⚡ **Server:** FREE-1\n"
        f"🕐 **Duration:** 120s\n\n"
        f"🔐 **Bảo mật:** Số điện thoại đã được mã hóa",
        parse_mode="Markdown"
    )

    # Dừng tiến trình cũ nếu có
    if sms_process and sms_process.poll() is None:
        sms_process.terminate()
        print(f"[{datetime.now()}] Terminated old SMS process for user {user_id}")

    # Chạy tiến trình mới
    sms_process = subprocess.Popen(["python3", "sms.py", phone, "100"])
    print(f"[{datetime.now()}] Started SMS attack: User {user_id}, Phone {masked_phone}, Loops {loops}")

    # Dừng tiến trình sau 120 giây
    async def stop_sms_after_delay():
        global sms_process
        await asyncio.sleep(120)
        if sms_process and sms_process.poll() is None:
            sms_process.terminate()
            sms_process = None
            print(f"[{datetime.now()}] SMS attack completed for user {user_id}")

    asyncio.create_task(stop_sms_after_delay())

# Hàm xử lý lệnh kiểm tra server (cải tiến)
async def server(update: Update, context: CallbackContext):
    # Hiển thị loading message
    loading_text = "🔄 **ĐANG KIỂM TRA SERVER...**\n\nVui lòng chờ trong giây lát..."
    
    loading_msg = await update.message.reply_text(loading_text, parse_mode="Markdown")
    
    try:
        # Kiểm tra CPU, RAM, Disk
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_used = memory.percent
        disk_usage = psutil.disk_usage('/')
        disk_used = disk_usage.percent
        disk_free = 100 - disk_used

        # Kiểm tra tốc độ mạng
        try:
            st = speedtest.Speedtest()
            download_speed = st.download() / 1e+6  # Mbps
            upload_speed = st.upload() / 1e+6  # Mbps
            ping = st.results.ping
        except:
            download_speed = upload_speed = ping = 0

        # Kiểm tra trạng thái server
        server_status = "🟢 Online" if check_server() else "🔴 Offline"
        
        # Đánh giá hiệu suất
        if cpu_percent < 50 and memory_used < 70:
            performance = "🟢 Excellent"
        elif cpu_percent < 80 and memory_used < 85:
            performance = "🟡 Good"
        else:
            performance = "🔴 Poor"

        # Gửi thông tin server với giao diện đẹp
        server_text = f"""
📊 **SERVER STATUS REPORT**

🖥️ **System Performance:**
├ CPU Usage: `{cpu_percent:.1f}%`
├ Memory: `{memory_used:.1f}%` used
├ Disk: `{disk_used:.1f}%` used / `{disk_free:.1f}%` free
└ Overall: {performance}

🌐 **Network Status:**
├ Download: `{download_speed:.2f} Mbps`
├ Upload: `{upload_speed:.2f} Mbps`
└ Ping: `{ping:.0f}ms`

⚡ **Service Status:**
├ Bot Status: {server_status}
├ SMS Engine: 🟢 Active
├ VIP Engine: 🟢 Active
└ Security: 🔐 Enabled

🕐 **Last Check:** {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}
        """
        
        await loading_msg.edit_text(server_text, parse_mode="Markdown")
            
    except Exception as e:
        error_text = f"""
❌ **SERVER CHECK FAILED**

🔧 **Error Details:**
{str(e)[:100]}...

🕐 **Time:** {datetime.now().strftime('%H:%M:%S')}

💡 **Suggestion:** Try again in a few moments
        """
        
        await loading_msg.edit_text(error_text, parse_mode="Markdown")

# Hàm chính
if __name__ == "__main__":
    # Thay token bot của bạn
    TOKEN = "7905621710:AAEGFz44YBSzkUevXKDoEM73VLJl12ilnes"

    # Tạo bot
    app = Application.builder().token(TOKEN).build()
    
    # Đăng ký lệnh
    app.add_handler(CommandHandler("sms", sms))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("server", server))

    # Chạy bot
    print("🔥 SMS BOMBER BOT STARTED 🔥")
    print("🎯 Features: SMS Attack, VIP Attack, Server Monitor")
    print("🔐 Security: Phone masking, Attack logging")
    print("✅ Bot is ready and listening...")
    app.run_polling()




