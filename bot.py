import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import yt_dlp
import aiofiles
import re

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    logger.error("❌ Токен не найден! Добавь TELEGRAM_TOKEN в Secrets")
    exit(1)

# Инициализация бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Класс для работы с YouTube
class MusicBot:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch5:',
        }
    
    def clean_title(self, title):
        """Очищает название от мусора"""
        if not title:
            return "Без названия"
        title = re.sub(r'\[.*?\]|\(.*?\)', '', title)
        title = ' '.join(title.split())
        return title[:50]
    
    async def search_music(self, query):
        """Ищет музыку на YouTube"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                
                tracks = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if not entry:
                            continue
                        
                        duration = entry.get('duration', 0)
                        if duration:
                            dur_str = f"{duration//60}:{duration%60:02d}"
                        else:
                            dur_str = "?:??"
                        
                        tracks.append({
                            'id': entry.get('id'),
                            'title': self.clean_title(entry.get('title')),
                            'duration': dur_str,
                            'url': f"https://youtu.be/{entry.get('id')}",
                        })
                
                return tracks[:5]  # Только 5 результатов
                
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []
    
    async def download_music(self, video_id, title):
        """Скачивает музыку (демо-функция)"""
        # В реальном боте здесь будет скачивание
        # Пока возвращаем демо-сообщение
        return None

# Создаем экземпляр
music_bot = MusicBot()

# Команды бота
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "🎵 <b>Музыкальный бот 24/7</b>\n\n"
        "Работает на <b>GitHub Actions</b>!\n\n"
        "Просто напиши название песни...\n\n"
        "<code>/help</code> - помощь\n"
        "<code>/status</code> - статус",
    )

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "🎯 <b>Как пользоваться:</b>\n\n"
        "1. Напиши название песни\n"
        "2. Бот найдет треки\n"
        "3. Выбери из списка\n"
        "4. Скоро будет скачивание!\n\n"
        "<i>Примеры:</i>\n"
        "• <code>Billie Eilish</code>\n"
        "• <code>Shape of You</code>\n"
        "• <code>реп 2024</code>"
    )

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    await message.answer("✅ Бот работает! Хостинг: GitHub Actions")

@dp.message()
async def search_handler(message: types.Message):
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Введите более длинный запрос")
        return
    
    status = await message.answer(f"🔍 <b>Ищу:</b> <code>{query}</code>")
    
    tracks = await music_bot.search_music(query)
    
    if not tracks:
        await status.edit_text(f"❌ По запросу <code>{query}</code> ничего не найдено")
        return
    
    # Формируем ответ
    response = f"✅ <b>Найдено {len(tracks)} треков:</b>\n\n"
    for i, track in enumerate(tracks, 1):
        response += f"{i}. <b>{track['title']}</b> ({track['duration']})\n"
    
    response += "\n⚡ <i>Скачивание скоро будет добавлено!</i>"
    
    await status.edit_text(response)

# Запуск бота
async def main():
    logger.info("=" * 50)
    logger.info("🚀 МУЗЫКАЛЬНЫЙ БОТ ЗАПУЩЕН")
    logger.info(f"✅ Токен: {'Установлен' if TOKEN else 'НЕТ!'}")
    logger.info("📍 Хостинг: GitHub Actions")
    logger.info("⏰ 24/7 работа")
    logger.info("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
