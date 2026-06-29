from keyboard_backlight_library import KeyboardBacklight

kb = KeyboardBacklight()

# Выключить подсветку
#kb.set_builtin_mode('LED Off')

# Включить эффект "Дыхание" (Breath) фиолетовым цветом, средняя яркость и скорость
#kb.set_builtin_mode('Breath', r=255, g=0, b=255, brightness=3, speed=3)

# Включить переливание радугой (Colourful)
kb.set_builtin_mode('Breath', brightness=5, speed=2)

# Статичный зеленый цвет
#kb.set_builtin_mode('Static', r=0, g=255, b=0, brightness=5)

kb.close()