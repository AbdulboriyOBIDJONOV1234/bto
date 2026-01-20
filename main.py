import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand
from aiohttp import web
import yt_dlp

# -----------------------------------------------------------
# TOKEN
# -----------------------------------------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Foydalanuvchi linklarini va tilini saqlash
user_links = {}
user_languages = {}

# -----------------------------------------------------------
# TRANSLATIONS (3 LANGUAGES)
# -----------------------------------------------------------
TRANSLATIONS = {
    'uz': {
        'welcome': (
            "👋 **Salom! Men Universal Video Yuklovchiman.**\n\n"
            "Men quyidagilardan video yuklab beraman:\n"
            "🔹 **YouTube**\n"
            "🔹 **Instagram** (Stories, Reels, Post)\n"
            "🔹 **Facebook**\n"
            "🔹 **Snapchat**\n\n"
            "🚀 *Boshlash uchun link yuboring!*\n\n"
            "🌐 Tilni o'zgartirish: /language\n"
            "ℹ️ Yordam: /help"
        ),
        'help': (
            "📖 **Yordam**\n\n"
            "Bot qanday ishlaydi:\n"
            "1️⃣ Video linkini yuboring (YouTube, Instagram, Facebook, Snapchat)\n"
            "2️⃣ Video yuklanadi va sizga yuboriladi\n"
            "3️⃣ Tayyor!\n\n"
            "🔧 Komandalar:\n"
            "/start - Botni qayta boshlash\n"
            "/language - Tilni o'zgartirish\n"
            "/help - Yordam\n\n"
            "👨‍💻 Muallif: @Abdulboriy7700"
        ),
        'choose_language': "🌐 Tilni tanlang:",
        'language_changed': "✅ Til o'zgartirildi!",
        'invalid_link': "❌ Iltimos, to'g'ri link yuboring.",
        'downloading': "⏳ **📹 Video yuklanmoqda...**\n(Biroz kuting)",
        'error': "❌ Xatolik: {}",
        'file_too_large': "❌ Fayl 50 MB dan katta. Telegramga yuklab bo'lmaydi.",
        'uploading': "📤 Telegramga yuklanmoqda...",
        'upload_error': "Yuborishda xato: {}",
        'file_not_found': "❌ Fayl topilmadi.",
    },
    'ru': {
        'welcome': (
            "👋 **Привет! Я загрузчик видео.**\n\n"
            "Я могу скачать видео с:\n"
            "🔹 **YouTube**\n"
            "🔹 **Instagram** (Stories, Reels, Post)\n"
            "🔹 **Facebook**\n"
            "🔹 **Snapchat**\n\n"
            "🚀 *Отправьте ссылку для начала!*\n\n"
            "🌐 Сменить язык: /language\n"
            "ℹ️ Помощь: /help"
        ),
        'help': (
            "📖 **Помощь**\n\n"
            "Как работает бот:\n"
            "1️⃣ Отправьте ссылку на видео (YouTube, Instagram, Facebook, Snapchat)\n"
            "2️⃣ Видео будет загружено и отправлено вам\n"
            "3️⃣ Готово!\n\n"
            "🔧 Команды:\n"
            "/start - Перезапустить бота\n"
            "/language - Сменить язык\n"
            "/help - Помощь\n\n"
            "👨‍💻 Автор: @Abdulboriy7700"
        ),
        'choose_language': "🌐 Выберите язык:",
        'language_changed': "✅ Язык изменен!",
        'invalid_link': "❌ Пожалуйста, отправьте правильную ссылку.",
        'downloading': "⏳ **📹 Загрузка видео...**\n(Пожалуйста, подождите)",
        'error': "❌ Ошибка: {}",
        'file_too_large': "❌ Файл больше 50 МБ. Невозможно загрузить в Telegram.",
        'uploading': "📤 Загрузка в Telegram...",
        'upload_error': "Ошибка при отправке: {}",
        'file_not_found': "❌ Файл не найден.",
    },
    'en': {
        'welcome': (
            "👋 **Hello! I'm a Video Downloader.**\n\n"
            "I can download videos from:\n"
            "🔹 **YouTube**\n"
            "🔹 **Instagram** (Stories, Reels, Post)\n"
            "🔹 **Facebook**\n"
            "🔹 **Snapchat**\n\n"
            "🚀 *Send a link to get started!*\n\n"
            "🌐 Change language: /language\n"
            "ℹ️ Help: /help"
        ),
        'help': (
            "📖 **Help**\n\n"
            "How the bot works:\n"
            "1️⃣ Send a video link (YouTube, Instagram, Facebook, Snapchat)\n"
            "2️⃣ Video will be downloaded and sent to you\n"
            "3️⃣ Done!\n\n"
            "🔧 Commands:\n"
            "/start - Restart bot\n"
            "/language - Change language\n"
            "/help - Help\n\n"
            "👨‍💻 Creator: @Abdulboriy7700"
        ),
        'choose_language': "🌐 Choose your language:",
        'language_changed': "✅ Language changed!",
        'invalid_link': "❌ Please send a valid link.",
        'downloading': "⏳ **📹 Downloading video...**\n(Please wait)",
        'error': "❌ Error: {}",
        'file_too_large': "❌ File is larger than 50 MB. Cannot upload to Telegram.",
        'uploading': "📤 Uploading to Telegram...",
        'upload_error': "Upload error: {}",
        'file_not_found': "❌ File not found.",
    }
}

def get_text(user_id, key):
    """Foydalanuvchi tilida matnni olish"""
    lang = user_languages.get(user_id, 'uz')
    return TRANSLATIONS[lang].get(key, TRANSLATIONS['uz'][key])

# -----------------------------------------------------------
# VIDEO YUKLASH FUNKSIYASI
# -----------------------------------------------------------
def download_video(url):
    # FFmpeg yo'lini aniqlash (local papkadan)
    if os.name == 'nt':  # Windows tizimi uchun
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_dir = os.path.join(current_dir, "ffmpeg-master-latest-win64-gpl-shared", "ffmpeg-master-latest-win64-gpl-shared", "bin")
    else:
        # Linux/Render uchun (tizimning o'zidan topadi)
        ffmpeg_dir = None

    ydl_opts = {
        'outtmpl': 'media_%(id)s.%(ext)s', 
        'quiet': True,
        'noplaylist': True,
        'format': 'best[ext=mp4]/best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }
    
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if 'entries' in info:
                if len(info['entries']) > 0:
                    info = info['entries'][0]
                else:
                    return None, None, "Media topilmadi."

            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media')
            return filename, title, None
    except Exception as e:
        return None, None, str(e)

# -----------------------------------------------------------
# KOMANDALAR
# -----------------------------------------------------------
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_languages:
        user_languages[user_id] = 'uz'
    
    await message.answer(get_text(user_id, 'welcome'), parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    user_id = message.from_user.id
    await message.answer(get_text(user_id, 'help'), parse_mode="Markdown")

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    user_id = message.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ])
    await message.answer(get_text(user_id, 'choose_language'), reply_markup=keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def language_callback(call: CallbackQuery):
    user_id = call.from_user.id
    lang = call.data.split("_")[1]
    user_languages[user_id] = lang
    
    await call.message.edit_text(get_text(user_id, 'language_changed'))
    await asyncio.sleep(1)
    await call.message.delete()

# -----------------------------------------------------------
# LINK HANDLER (Avtomatik yuklash)
# -----------------------------------------------------------
@dp.message(F.text)
async def link_handler(message: types.Message):
    url = message.text
    user_id = message.from_user.id
    
    if not url.startswith("http"):
        await message.answer(get_text(user_id, 'invalid_link'))
        return

    # Yuklanish jarayonini boshlash
    status_msg = await message.answer(get_text(user_id, 'downloading'))

    loop = asyncio.get_event_loop()
    filename, title, error_msg = await loop.run_in_executor(None, download_video, url)

    if error_msg:
        await status_msg.edit_text(get_text(user_id, 'error').format(str(error_msg)[:100]))
    elif filename and os.path.exists(filename):
        try:
            file_size = os.path.getsize(filename) / (1024 * 1024)
            if file_size > 50:
                await status_msg.edit_text(get_text(user_id, 'file_too_large'))
                os.remove(filename)
                return

            await status_msg.edit_text(get_text(user_id, 'uploading'))
            media_file = FSInputFile(filename)

            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.png', '.webp']:
                await message.answer_photo(media_file, caption=f"📸 {title}\n🤖 @Abdulboriy7700")
            else:
                await message.answer_video(media_file, caption=f"📹 {title}\n🤖 @Abdulboriy7700")

            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(get_text(user_id, 'upload_error').format(e))
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass
    else:
        await status_msg.edit_text(get_text(user_id, 'file_not_found'))

# -----------------------------------------------------------
# ISHGA TUSHIRISH
# -----------------------------------------------------------
async def set_bot_commands():
    """Bot uchun Menu komandalarini o'rnatish"""
    commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish"),
        BotCommand(command="language", description="🌐 Tilni o'zgartirish"),
        BotCommand(command="help", description="ℹ️ Yordam")
    ]
    await bot.set_my_commands(commands)

# -----------------------------------------------------------
# RENDER UCHUN WEB SERVER (Keep-Alive)
# -----------------------------------------------------------
async def health_check(request):
    return web.Response(text="Bot ishlamoqda! 🚀")

async def start_webhook():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    print("Video Downloader Bot ishga tushdi... ✅")
    await set_bot_commands()  # Menuni o'rnatish
    await bot.delete_webhook(drop_pending_updates=True)
    await start_webhook() # Web serverni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())