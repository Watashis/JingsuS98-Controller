from keyboard_backlight_library import KeyboardBacklight

kb = KeyboardBacklight()

#kb.set_full_keymap({'W':'B', 'V':('S',['Ctrl_L'])})     # W→B и V→Ctrl+S разом  
kb.clear_layer(0)          # сброс всего Top                                
kb.close()