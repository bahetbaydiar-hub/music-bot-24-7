import os
import zipfile
import requests
import subprocess
import sys

def download_ffmpeg():
    """Скачиваем и устанавливаем FFmpeg"""
    
    print("📥 Скачиваю FFmpeg...")
    
    # URL для скачивания (проверенный, 80 МБ)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    # Папка для установки
    install_dir = "C:\\ffmpeg"
    os.makedirs(install_dir, exist_ok=True)
    
    # Путь к архиву
    zip_path = os.path.join(install_dir, "ffmpeg.zip")
    
    try:
        # Скачиваем
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(zip_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Прогресс
                    percent = (downloaded / total_size) * 100 if total_size > 0 else 0
                    print(f"\rПрогресс: {percent:.1f}% ({downloaded/1024/1024:.1f} MB)", end="")
        
        print("\n✅ Скачано!")
        
        # Распаковываем
        print("📦 Распаковываю...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        
        # Находим папку bin
        for item in os.listdir(install_dir):
            item_path = os.path.join(install_dir, item)
            if os.path.isdir(item_path):
                bin_path = os.path.join(item_path, "bin")
                if os.path.exists(bin_path):
                    print(f"🎯 Найдена папка с бинарниками: {bin_path}")
                    
                    # Добавляем в PATH (для текущей сессии)
                    os.environ['PATH'] = bin_path + ';' + os.environ['PATH']
                    
                    # Проверяем
                    try:
                        result = subprocess.run(
                            ['ffmpeg', '-version'],
                            capture_output=True,
                            text=True,
                            cwd=bin_path
                        )
                        if result.returncode == 0:
                            print("✅ FFmpeg работает!")
                            print(f"\n📋 Инструкция:")
                            print(f"1. FFmpeg установлен в: {bin_path}")
                            print(f"2. Чтобы добавить в PATH навсегда:")
                            print(f"   - Win + X → Система")
                            print(f"   - Дополнительные параметры")
                            print(f"   - Переменные среды → Path")
                            print(f"   - Добавьте: {bin_path}")
                            return True
                    except:
                        pass
        
        print("⚠️ Автоматическая установка не удалась, но файлы скачаны.")
        print(f"📁 Перейдите в: {install_dir}")
        print("🔍 Найдите папку с названием 'ffmpeg-...'")
        print("📂 В ней будет папка 'bin' с ffmpeg.exe")
        
        return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("УСТАНОВКА FFMPEG ДЛЯ МУЗЫКАЛЬНОГО БОТА")
    print("=" * 50)
    
    if download_ffmpeg():
        print("\n🎉 Установка завершена успешно!")
        print("Перезапустите терминал и проверьте: ffmpeg -version")
    else:
        print("\n⚠️ Установите FFmpeg вручную:")
        print("1. Скачайте: https://tmpfiles.org/dl/311142/ffmpeg-essential.zip")
        print("2. Распакуйте в C:\\ffmpeg")
        print("3. Добавьте C:\\ffmpeg\\bin в PATH")
    
    input("\nНажмите Enter для выхода...")
