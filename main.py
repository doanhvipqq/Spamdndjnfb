import os
import json
import psutil
import asyncio
import speedtest
import subprocess
from datetime import datetime
from telegram import Update, User
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import CommandHandler, CallbackContext, Application


# Biến toàn cục
last_sms_time = {}
last_spam_time = {}
sms_process = None
spam_process = None

# Đường dẫn file JSON
VIP_FILE = "vip.json"

# Khởi tạo file JSON nếu chưa tồn tại
if not os.path.exists(VIP_FILE):
    with open(VIP_FILE, "w") as file:
        json.dump({}, file)

# ID admin được phép sử dụng lệnh /add
ADMIN_ID = 7605936504
GROUP_ID = -1002408191237

# Hàm kiểm tra server
def check_server():
    try:
        ping = psutil.net_if_stats()
        return ping['lo'].isup  # Thay 'lo' bằng interface phù hợp nếu VPS khác
    except:
        return False

# Hàm thêm người dùng vào VIP
async def add(update: Update, context: CallbackContext):
    user: User = update.effective_user

    # Kiểm tra quyền truy cập
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args or not context.args[0].startswith("@"):
        await update.message.reply_text("❌ Vui lòng tag người dùng với định dạng: /add @username.")
        return

    username = context.args[0].lstrip("@")

    # Kiểm tra xem có cung cấp thêm ID người dùng hay không
    if len(context.args) > 1 and context.args[1].isdigit():
        user_id = int(context.args[1])
    else:
        await update.message.reply_text("❌ Vui lòng cung cấp cả ID người dùng sau username. Ví dụ: /add @username 123456789.")
        return

    # Lưu dữ liệu vào file JSON
    with open(VIP_FILE, "r") as file:
        vip_data = json.load(file)

    if username in vip_data:
        await update.message.reply_text(f"✅ Người dùng @{username} đã có trong danh sách VIP.")
        return

    vip_data[username] = user_id
    with open(VIP_FILE, "w") as file:
        json.dump(vip_data, file, indent=4)

    await update.message.reply_text(f"✅ Đã thêm @{username} (ID: {user_id}) vào danh sách VIP.")

# Hàm xử lý lệnh spam (Spam Vip)
async def spam(update: Update, context: CallbackContext):
    global last_spam_time, spam_process

    user_id = update.effective_user.id
    now = datetime.now()

    # Kiểm tra quyền VIP
    with open(VIP_FILE, "r") as file:
        vip_data = json.load(file)
    if user_id not in vip_data.values():
        await update.message.reply_text("❌ Bạn không có quyền vì chưa mua VIP. Hãy ib `/admin` để mua VIP.")
        return

    # Kiểm tra cooldown 60s
    if user_id in last_spam_time and (now - last_spam_time[user_id]).total_seconds() < 60:
        await update.message.reply_text("❌ Bạn cần chờ 60 giây trước khi sử dụng lệnh này lại.")
        return

    # Kiểm tra tham số
    args = context.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text("❌ Sử dụng đúng cách: /spam [10 số] [vòng lặp].")
        return

    phone, loops = args
    if len(phone) != 10 or not phone.startswith("0"):
        await update.message.reply_text("❌ Số điện thoại phải bắt đầu bằng 0 và có đủ 10 chữ số.")
        return

    loops = int(loops)
    if loops > 10000:
        await update.message.reply_text("❌ Vòng lặp không được vượt quá 10.000.")
        return

    # Cập nhật thời gian sử dụng lệnh
    last_spam_time[user_id] = now

    # Gửi thông báo bắt đầu
    await update.message.reply_text(
        f"**Spam Server 1**\n📱 **Mục tiêu:** {phone}\n🍃 **Vòng lặp:** {loops}",
        parse_mode="Markdown"
    )

    # Dừng tiến trình cũ nếu có
    if spam_process and spam_process.poll() is None:
        spam_process.terminate()
        print("Tiến trình spam cũ đã bị dừng.")

    # Chạy tiến trình mới
    spam_process = subprocess.Popen(["python3", "smsvip.py", phone, "200"])

    # Dừng tiến trình sau 200 giây
    async def stop_spam_after_delay():
        global spam_process
        await asyncio.sleep(200)
        if spam_process and spam_process.poll() is None:
            spam_process.terminate()
            spam_process = None
            print("Spam process stopped after 200 seconds.")

    asyncio.create_task(stop_spam_after_delay())

# Hàm xử lý lệnh SMS (Spam thường)
async def sms(update: Update, context: CallbackContext):
    global last_sms_time, sms_process

    user_id = update.effective_user.id
    now = datetime.now()

    # Kiểm tra cooldown 100s
    if user_id in last_sms_time and (now - last_sms_time[user_id]).total_seconds() < 100:
        await update.message.reply_text("❌ Bạn cần chờ thêm để sử dụng lại lệnh.")
        return

    # Kiểm tra tham số
    args = context.args
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        await update.message.reply_text("❌ Sử dụng đúng cách: /sms [số điện thoại] [vòng lặp].")
        return

    phone, loops = args
    if len(phone) != 10 or not phone.startswith("0"):
        await update.message.reply_text("❌ Số điện thoại phải bắt đầu bằng 0 và có đủ 10 chữ số.")
        return

    loops = int(loops)
    if loops > 10000:
        await update.message.reply_text("❌ Vòng lặp không được vượt quá 10.000.")
        return

    # Cập nhật thời gian sử dụng lệnh
    last_sms_time[user_id] = now

    # Gửi thông báo bắt đầu
    await update.message.reply_text(
        f"⚡*Bắt đầu tấn công SEVER1*\n"
        f"📱*Số điện thoại:* {phone}\n"
        f"🌩️*Vòng lặp:* {loops}",
        parse_mode="Markdown"
    )

    # Dừng tiến trình cũ nếu có
    if sms_process and sms_process.poll() is None:
        sms_process.terminate()
        print("Tiến trình SMS cũ đã bị dừng.")

    # Chạy tiến trình mới
    sms_process = subprocess.Popen(["python3", "sms.py", phone, "100"])

    # Dừng tiến trình sau 120 giây
    async def stop_sms_after_delay():
        global sms_process
        await asyncio.sleep(120)
        if sms_process and sms_process.poll() is None:
            sms_process.terminate()
            sms_process = None
            print("SMS process stopped after 120 seconds.")

    asyncio.create_task(stop_sms_after_delay())

# Hàm xử lý lệnh kiểm tra server
async def server(update: Update, context: CallbackContext):
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
    except:
        download_speed = upload_speed = 0

    # Kiểm tra trạng thái server
    server_status = "🟢" if check_server() else "🔴"

    # Gửi thông tin server
    await update.message.reply_text(
        f"*Status Server 1!*\n"
        f"CPU: *{cpu_percent}%*\n"
        f"Internet: Download *{download_speed:.2f} Mbps*, Upload *{upload_speed:.2f} Mbps*\n"
        f"Memory: *{memory_used}%*\n"
        f"Disk: *{disk_free}%* trống / *{disk_used}%* đã dùng\n"
        f"Server status: {server_status}",
        parse_mode="Markdown"
    )

# Hàm chính
if __name__ == "__main__":
    # Thay token bot của bạn
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Tạo bot
    app = Application.builder().token(TOKEN).build()
    # Đăng ký lệnh
    app.add_handler(CommandHandler("sms", sms))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("server", server))

    # Chạy bot
    print("Bot đã sẵn sàng!")
    app.run_polling()




