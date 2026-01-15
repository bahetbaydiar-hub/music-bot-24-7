import os
import asyncio
import aiohttp
import yt_dlp
import ffmpeg
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================== НАСТРОЙКА ==================
TOKEN = os.getenv("TELEGRAM_TOKEN") or "YOUR_BOT_TOKEN"
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Папка для временных файлов
TEMP_DIR = Path("temp_downloads")
TEMP_DIR.mkdir(exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================== ИНИЦИАЛИЗАЦИЯ ==================
storage = MemoryStorage()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# Статистика
stats = {
    "total_downloads": 0,
    "failed_downloads": 0,
    "users": {},
    "start_time": datetime.now().isoformat()
}

# ================== РЕАЛЬНОЕ СКАЧИВАНИЕ ==================
class YouTubeDownloader:
    """Класс для реального скачивания музыки с YouTube"""
    
    @staticmethod
    async def search_youtube(query: str, limit: int = 10):
        """Поиск видео на YouTube"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'skip_download': True,
                'default_search': 'ytsearch',
                'format': 'bestaudio/best',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                
                if not result or 'entries' not in result:
                    return []
                
                videos = []
                for entry in result['entries'][:limit]:
                    if entry:
                        videos.append({
                            'id': entry.get('id'),
                            'title': entry.get('title', 'Без названия'),
                            'duration': entry.get('duration_string', '0:00'),
                            'thumbnail': entry.get('thumbnail'),
                            'url': entry.get('url'),
                            'channel': entry.get('channel', 'Неизвестно'),
                            'views': entry.get('view_count', 0)
                        })
                return videos
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    @staticmethod
    async def download_audio(video_id: str, quality: str = "192"):
        """Скачивание аудио в MP3"""
        temp_file = None
        try:
            # Создаем временную папку
            temp_dir = tempfile.mkdtemp(prefix="music_bot_", dir=TEMP_DIR)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'quiet': False,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'noplaylist': True,
                'geo_bypass': True,
                'ignoreerrors': True,
                'logtostderr': False,
                'verbose': False,
                'no_color': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            }
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # Меняем расширение на .mp3
                base, _ = os.path.splitext(downloaded_file)
                mp3_file = base + '.mp3'
                
                if os.path.exists(mp3_file):
                    # Читаем файл
                    with open(mp3_file, 'rb') as f:
                        audio_data = f.read()
                    
                    temp_file = {
                        'data': audio_data,
                        'filename': os.path.basename(mp3_file),
                        'title': info.get('title', 'audio'),
                        'artist': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'temp_dir': temp_dir
                    }
                    return temp_file
                    
            return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            if temp_file and 'temp_dir' in temp_file:
                shutil.rmtree(temp_file['temp_dir'], ignore_errors=True)
            return None
    
    @staticmethod
    async def get_direct_link(video_id: str):
        """Получение прямой ссылки на аудио (альтернативный метод)"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'url' in info:
                    return info['url']
                    
            return None
        except Exception as e:
            logger.error(f"Direct link error: {e}")
            return None

# ================== КОМАНДЫ БОТА ==================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🎵 <b>Музыкальный бот для скачивания</b>\n\n"
        "🔍 <b>Как использовать:</b>\n"
        "1. Напиши название песни или исполнителя\n"
        "2. Выбери трек из списка\n"
        "3. Нажми 'Скачать MP3'\n\n"
        "⚡ <b>Команды:</b>\n"
        "/search - поиск музыки\n"
        "/quality - настройка качества\n"
        "/help - помощь\n\n"
        "<i>Бот скачивает музыку с YouTube</i>"
    )

@dp.message(Command("quality"))
async def quality_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 Высокое (320kbps)", callback_data="quality_320")],
        [InlineKeyboardButton(text="🎶 Среднее (192kbps)", callback_data="quality_192")],
        [InlineKeyboardButton(text="📱 Низкое (128kbps)", callback_data="quality_128")],
    ])
    
    await message.answer(
        "⚙️ <b>Настройка качества аудио:</b>\n\n"
        "• <b>320kbps</b> - лучшее качество, больший размер\n"
        "• <b>192kbps</b> - оптимальное качество/размер (по умолчанию)\n"
        "• <b>128kbps</b> - меньше размер, качество похуже\n\n"
        "Выберите качество:",
        reply_markup=keyboard
    )

# ================== ПОИСК ==================
@dp.message(Command("search"))
async def search_cmd(message: types.Message, state: FSMContext):
    await message.answer("🔍 <b>Введите название песни или исполнителя:</b>")
    await state.set_state("waiting_query")

@dp.message(F.text, F.text.len() > 1)
async def handle_search(message: types.Message, state: FSMContext = None):
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Введите минимум 2 символа")
        return
    
    # Отправляем сообщение о поиске
    msg = await message.answer(f"🔍 <b>Ищем:</b> <code>{query}</code>")
    
    try:
        # Ищем видео
        videos = await YouTubeDownloader.search_youtube(query, limit=10)
        
        if not videos:
            await msg.edit_text(f"❌ По запросу <code>{query}</code> ничего не найдено")
            return
        
        # Сохраняем в FSM context
        if state:
            await state.update_data(videos=videos, query=query)
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for i, video in enumerate(videos[:8]):  # Показываем первые 8
            title = video['title'][:40] + "..." if len(video['title']) > 40 else video['title']
            duration = video['duration'] if video['duration'] != '0:00' else "N/A"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{i+1}. {title} ({duration})",
                    callback_data=f"select_{video['id']}"
                )
            ])
        
        # Добавляем кнопки управления
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search"),
            InlineKeyboardButton(text="📋 Еще результаты", callback_data="more_results")
        ])
        
        await msg.edit_text(
            f"✅ <b>Найдено {len(videos)} результатов:</b>\n"
            f"Запрос: <code>{query}</code>\n\n"
            f"<i>Выберите трек для скачивания:</i>",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await msg.edit_text("❌ Ошибка при поиске. Попробуйте другой запрос.")

# ================== ВЫБОР ТРЕКА ==================
@dp.callback_query(F.data.startswith("select_"))
async def handle_selection(callback: types.CallbackQuery, state: FSMContext):
    video_id = callback.data.replace("select_", "")
    
    # Получаем данные из состояния
    data = await state.get_data()
    videos = data.get('videos', [])
    
    # Находим выбранный трек
    selected_video = next((v for v in videos if v['id'] == video_id), None)
    
    if not selected_video:
        await callback.answer("❌ Трек не найден")
        return
    
    # Клавиатура с опциями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬇️ Скачать MP3", callback_data=f"download_{video_id}"),
            InlineKeyboardButton(text="🎬 Смотреть", url=f"https://youtu.be/{video_id}")
        ],
        [
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search"),
            InlineKeyboardButton(text="⚙️ Качество", callback_data="change_quality")
        ]
    ])
    
    # Информация о треке
    duration = selected_video.get('duration', 'N/A')
    channel = selected_video.get('channel', 'Неизвестно')
    
    await callback.message.edit_text(
        f"🎵 <b>Выбран трек:</b>\n\n"
        f"📌 <b>{selected_video['title']}</b>\n"
        f"⏱ Длительность: {duration}\n"
        f"👤 Канал: {channel}\n\n"
        f"<i>Выберите действие:</i>",
        reply_markup=keyboard
    )
    await callback.answer()

# ================== СКАЧИВАНИЕ ==================
@dp.callback_query(F.data.startswith("download_"))
async def handle_download(callback: types.CallbackQuery, state: FSMContext):
    video_id = callback.data.replace("download_", "")
    
    # Получаем качество из состояния
    data = await state.get_data()
    quality = data.get('quality', '192')
    
    await callback.answer("⏳ Начинаем скачивание...")
    
    # Сообщение о скачивании
    msg = await callback.message.answer(
        "⬇️ <b>Скачиваю трек...</b>\n"
        "⏳ Это может занять несколько секунд"
    )
    
    try:
        # Скачиваем аудио
        audio_file = await YouTubeDownloader.download_audio(video_id, quality)
        
        if not audio_file or 'data' not in audio_file:
            await msg.edit_text("❌ Не удалось скачать трек")
            return
        
        # Обновляем статистику
        stats["total_downloads"] += 1
        user_id = callback.from_user.id
        if user_id not in stats["users"]:
            stats["users"][user_id] = {"downloads": 0, "username": callback.from_user.username}
        stats["users"][user_id]["downloads"] += 1
        
        # Отправляем файл
        duration = audio_file.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration > 0 else "N/A"
        
        await bot.send_audio(
            chat_id=callback.from_user.id,
            audio=types.BufferedInputFile(
                audio_file['data'],
                filename=audio_file['filename'][:64]  # Ограничение длины имени
            ),
            caption=(
                f"🎵 <b>{audio_file['title'][:50]}</b>\n"
                f"👤 {audio_file['artist'][:30]}\n"
                f"⏱ {duration_str}\n"
                f"🎧 Качество: {quality}kbps\n\n"
                f"<i>Скачано через Music Bot</i>"
            ),
            title=audio_file['title'][:30],
            performer=audio_file['artist'][:30],
            duration=int(duration) if duration > 0 else None
        )
        
        # Обновляем сообщение
        await msg.edit_text(f"✅ <b>Готово!</b> Трек отправлен в чат")
        
        # Очищаем временные файлы
        if 'temp_dir' in audio_file:
            shutil.rmtree(audio_file['temp_dir'], ignore_errors=True)
        
        logger.info(f"Download successful: user={user_id}, track={video_id}")
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        stats["failed_downloads"] += 1
        await msg.edit_text(
            f"❌ <b>Ошибка скачивания:</b>\n"
            f"<code>{str(e)[:100]}</code>\n\n"
            f"Попробуйте другой трек или качество"
        )
        
        # Очищаем временные файлы при ошибке
        try:
            temp_files = list(TEMP_DIR.glob("*"))
            for temp in temp_files:
                if temp.is_dir():
                    shutil.rmtree(temp, ignore_errors=True)
        except:
            pass

# ================== ДОПОЛНИТЕЛЬНЫЕ КНОПКИ ==================
@dp.callback_query(F.data == "new_search")
async def new_search_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔍 <b>Новый поиск</b>\n\n"
        "Введите название песни или исполнителя:"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("quality_"))
async def quality_handler(callback: types.CallbackQuery, state: FSMContext):
    quality = callback.data.replace("quality_", "")
    
    quality_names = {
        "320": "Высокое (320kbps)",
        "192": "Среднее (192kbps)",
        "128": "Низкое (128kbps)"
    }
    
    await state.update_data(quality=quality)
    await callback.answer(f"✅ Установлено качество: {quality_names.get(quality, quality)}kbps")

@dp.callback_query(F.data == "change_quality")
async def change_quality_handler(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 320kbps", callback_data="quality_320")],
        [InlineKeyboardButton(text="🎶 192kbps", callback_data="quality_192")],
        [InlineKeyboardButton(text="📱 128kbps", callback_data="quality_128")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_track")],
    ])
    
    await callback.message.edit_text(
        "⚙️ <b>Выберите качество аудио:</b>\n\n"
        "Битрейт влияет на качество и размер файла",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_track")
async def back_handler(callback: types.CallbackQuery):
    await callback.answer("Возвращаемся...")
    # Здесь нужно вернуться к предыдущему сообщению
    # В реальном боте нужно сохранять состояние

# ================== ОЧИСТКА ТЕМП ФАЙЛОВ ==================
async def cleanup_temp_files():
    """Очистка временных файлов каждые 10 минут"""
    while True:
        try:
            now = datetime.now()
            temp_items = list(TEMP_DIR.glob("*"))
            
            for item in temp_items:
                if item.is_dir():
                    # Удаляем папки старше 1 часа
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if (now - mtime).seconds > 3600:
                        shutil.rmtree(item, ignore_errors=True)
                elif item.is_file():
                    # Удаляем файлы старше 1 часа
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if (now - mtime).seconds > 3600:
                        item.unlink(missing_ok=True)
            
            logger.info(f"Cleanup: удалено {len(temp_items)} временных файлов")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        await asyncio.sleep(600)  # 10 минут

# ================== ЗАПУСК ==================
async def main():
    logger.info("=" * 50)
    logger.info("🎵 MUSIC DOWNLOAD BOT")
    logger.info(f"📁 Temp dir: {TEMP_DIR.absolute()}")
    logger.info("✅ Starting bot...")
    logger.info("=" * 50)
    
    # Запускаем очистку временных файлов
    asyncio.create_task(cleanup_temp_files())
    
    # Удаляем старые вебхуки
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
