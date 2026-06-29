from keyboard_backlight_library import KeyboardBacklight

kb = KeyboardBacklight()

# Получаем заряд батареи в процентах (возвращает число от 0 до 100)
battery = kb.get_battery_level()

if battery is not None:
    print(f"Заряд клавиатуры: {battery}%")
    
    # Можно сделать так, чтобы клавиатура горела красным, если заряд ниже 20%
    if battery < 20:
        kb.set_builtin_mode('Static', r=255, g=0, b=0, brightness=5)
else:
    print("Не удалось прочитать заряд (возможно клавиатура подключена по кабелю)")

kb.close()