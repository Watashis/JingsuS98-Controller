from keyboard_backlight_library import KeyboardBacklight

kb = KeyboardBacklight()

# Создаем свою раскладку
my_layout = {
    # Можно использовать имена
    'Space': (255, 0, 255),  # Пробел фиолетовым
    'Enter': (0, 255, 0),    # Enter зеленым
    'Esc': (255, 0, 0),      # Esc красным
    
    # Можно заливать целые зоны
    'W': (255, 100, 0),
    'A': (255, 100, 0),
    'S': (255, 100, 0),
    'D': (255, 100, 0)
}

# Отправляем на клавиатуру (помним про правило "не чаще 1 раза в пару секунд"!)
kb.set_per_key_colors(my_layout)

kb.close()