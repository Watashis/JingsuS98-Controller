"""
Проверка гипотезы "live music" (см. CLAUDE.md, дамп music_2.json).
Гоняет бегущую волну по 19 "полосам" — если гипотеза верна, по клавиатуре
должна побежать волна яркости слева направо (или как-то по колонкам).

ВАЖНО: перед запуском в официальном софте выключи музыкальный режим (или
закрой софт), иначе он будет конкурировать с этим скриптом за подсветку.
"""
import time
from keyboard_backlight_library import KeyboardBacklight

kb = KeyboardBacklight()

print("Шлём бегущую волну по 19 полосам в течение 6 секунд...")
print("Смотри на клавиатуру: должна быть видна волна/паттерн смены яркости/цвета.")

t0 = time.time()
try:
    while time.time() - t0 < 6:
        phase = (time.time() - t0) * 4  # скорость волны
        bands = []
        for i in range(19):
            import math
            v = int((math.sin(phase + i * 0.5) + 1) / 2 * 6)  # 0..6
            bands.append(v)
        kb.send_music_frame(bands, active=2)
        time.sleep(0.03)
finally:
    kb.send_music_frame([0] * 19, active=0)
    kb.close()

print("Готово. Опиши, что увидел на клавиатуре (ничего? волна? мигание? не та зона?).")
