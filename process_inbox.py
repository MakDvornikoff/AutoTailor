import os
import glob
import subprocess
import sys
from PIL import Image, ExifTags

# Path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INBOX_DIR = os.path.join(BASE_DIR, "inbox")
OUT_DIR = os.path.join(BASE_DIR, "out")
SCRIPT_PATH = os.path.join(BASE_DIR, "process_scan.py")
CONFIG_PATH = os.path.join(BASE_DIR, "config.txt")

def get_exif_rotation(file_path):
    try:
        image = Image.open(file_path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            exif = dict(exif.items())
            val = exif.get(orientation)
            if val == 3:
                return 180
            elif val == 6:
                return 270 # 90 degrees CCW
            elif val == 8:
                return 90  # 90 degrees CW
    except Exception as e:
        pass
    return 0

def read_config_mode():
    default_mode = 'gray'
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write(f"mode={default_mode}\n")
        except:
            pass
        return default_mode
        
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('mode='):
                    mode = line.strip().split('=')[1].lower()
                    if mode in ['color', 'gray', 'bw']:
                        return mode
    except Exception as e:
        print(f"Предупреждение: Не удалось прочитать config.txt: {e}")
    return default_mode

def main():
    print("--- Автоматический обработчик папки Inbox ---")
    if not os.path.exists(INBOX_DIR):
        print(f"Ошибка: Директория {INBOX_DIR} не найдена.")
        return
        
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
        
    # Read output mode from config
    mode = read_config_mode()
    print(f"Текущий режим обработки (из config.txt): {mode.upper()}")
    
    # Get all supported image files
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.tiff', '*.bmp')
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(INBOX_DIR, ext)))
        
    if not files:
        print("В папке Inbox нет новых изображений для обработки.")
        return
        
    print(f"Найдено файлов для обработки: {len(files)}")
    
    for f in files:
        filename = os.path.basename(f)
        print(f"\nОбработка файла: {filename}")
        
        # Read rotation from EXIF to automatically make photos upright
        rot = get_exif_rotation(f)
                
        # Run process_scan.py script
        cmd = [
            sys.executable,
            SCRIPT_PATH,
            f,
            OUT_DIR,
            str(rot),
            mode
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            print(result.stdout)
            if result.returncode != 0:
                print(f"Ошибка при обработке {filename}:")
                print(result.stderr)
        except Exception as e:
            print(f"Не удалось запустить обработку для {filename}: {e}")
            
    print("\nОбработка завершена! Результаты сохранены в папку out.")

if __name__ == "__main__":
    main()
