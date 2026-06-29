import time
import hid

class KeyboardBacklight:
    # Имя ключей для удобного доступа. Индексы взяты из официального драйвера
    KEY_MAP = {
        'Esc': 1, 'F1': 2, 'F2': 3, 'F3': 4, 'F4': 5, 'F5': 6, 'F6': 7, 
        'F7': 8, 'F8': 9, 'F9': 10, 'F10': 11, 'F11': 12, 'F12': 13,
        'Delete': 119, 'PgUp': 118, 'PgDn': 121,
        '~': 19, '1': 20, '2': 21, '3': 22, '4': 23, '5': 24, '6': 25, 
        '7': 26, '8': 27, '9': 28, '0': 29, '-': 30, '=': 31, 'Backspace': 103,
        'Num': 32, 'Num_/': 33, 'Num_*': 34, 'Num_-': 122, 'Num_+': 123, 'Num_Enter': 106,
        'Num_7': 50, 'Num_8': 51, 'Num_9': 52, 'Num_4': 68, 'Num_5': 69, 'Num_6': 70,
        'Num_1': 86, 'Num_2': 87, 'Num_3': 88, 'Num_0': 104, 'Num_.': 105,
        'Tab': 37, 'Q': 38, 'W': 39, 'E': 40, 'R': 41, 'T': 42, 'Y': 43, 
        'U': 44, 'I': 45, 'O': 46, 'P': 47, '[': 48, ']': 49, '\\': 67,
        'CapsLock': 55, 'A': 56, 'S': 57, 'D': 58, 'F': 59, 'G': 60, 'H': 61, 
        'J': 62, 'K': 63, 'L': 64, ';': 65, '\'': 66, 'Enter': 85,
        'Shift_L': 73, 'Z': 74, 'X': 75, 'C': 76, 'V': 77, 'B': 78, 'N': 79, 
        'M': 80, ',': 81, '.': 82, '/': 83, 'Shift_R': 84,
        'Ctrl_L': 91, 'Win_L': 92, 'Alt_L': 93, 'Space': 94, 
        'Alt_R': 95, 'Fn': 96,
        'Up': 101, 'Left': 99, 'Down': 100, 'Right': 102
    }
    
    # Список всех допустимых индексов (для быстрой проверки)
    VALID_KEYS = list(KEY_MAP.values())
    
    # Встроенные эффекты
    MODES = {
        'Static': 1, 'SingleOn': 2, 'SingleOff': 3, 'Glittering': 4,
        'Falling': 5, 'Colourful': 6, 'Breath': 7, 'Spectrum': 8,
        'Outward': 9, 'Scrolling': 10, 'Rolling': 11, 'Rotating': 12,
        'Explode': 13, 'Launch': 14, 'Ripples': 15, 'Flowing': 16,
        'Pulsating': 17, 'Tilt': 18, 'Shuttle': 19, 'LED Off': 0, 'Off': 0
    }

    def __init__(self, vid=0x05AC, pid=0x024F):
        self.vid = vid
        self.pid = pid
        self.devices = []
        
        for d in hid.enumerate(vid, pid):
            if d.get('usage_page', 0) >= 0xFF00:
                # Открываем только нужные интерфейсы (MI_00 для провода, MI_03 для 2.4G)
                path_str = d['path'].decode('utf-8', errors='ignore').upper()
                if "MI_00" in path_str or "MI_03" in path_str:
                    try:
                        dev = hid.device()
                        dev.open_path(d['path'])
                        dev.set_nonblocking(1)
                        self.devices.append(dev)
                    except:
                        pass
                    
        if not self.devices:
            raise RuntimeError(f"Не удалось найти подходящий HID-интерфейс для клавиатуры {hex(vid)}:{hex(pid)}")
            
    def close(self):
        for dev in self.devices:
            dev.close()
        self.devices.clear()

    def _broadcast(self, payload):
        """Отправляет 32-байтный пакет на все нужные интерфейсы клавиатуры"""
        if len(payload) < 32:
            payload += bytearray(32 - len(payload))
            
        data = bytearray([0x00]) + payload
        for dev in self.devices:
            try:
                dev.write(data)
                time.sleep(0.05) # Небольшая задержка, чтобы ОС успела отправить пакет до закрытия скрипта
            except:
                pass

    def set_global_color(self, r, g, b):
        """Устанавливает статичный цвет для всей клавиатуры."""
        payload = bytearray(32)
        payload[0] = 0x05; payload[1] = 0x10; payload[2] = 0x00; payload[3] = 0x01
        payload[4] = r & 0xFF; payload[5] = g & 0xFF; payload[6] = b & 0xFF
        payload[12] = 0x05; payload[13] = 0x03 # Режим статичного цвета
        payload[17] = 0xAA; payload[18] = 0x55
        payload[31] = sum(payload[:31]) % 256
        self._broadcast(payload)

    def set_builtin_mode(self, mode_id, r=255, g=0, b=0, brightness=5, speed=3):
        """
        Включает встроенный эффект клавиатуры.
        mode_id: от 1 до 19 (встроенные режимы) или 0 (выключить подсветку).
                 Также можно передать строку (например, 'Breath', 'Static', 'LED Off').
        r, g, b: базовый цвет эффекта.
        brightness: яркость (от 0 до 5).
        speed: скорость (от 0 до 5).
        """
        if isinstance(mode_id, str):
            if mode_id not in self.MODES:
                raise ValueError(f"Неизвестный режим: {mode_id}. Доступные: {list(self.MODES.keys())}")
            mode_id = self.MODES[mode_id]
            
        if not (0 <= mode_id <= 19):
            raise ValueError("mode_id должен быть от 0 до 19")
            
        payload = bytearray(32)
        payload[0] = 0x05; payload[1] = 0x10; payload[2] = 0x00
        payload[3] = mode_id & 0xFF
        
        if mode_id == 0:
            # Режим выключения
            pass
        else:
            payload[4] = r & 0xFF; payload[5] = g & 0xFF; payload[6] = b & 0xFF
            payload[12] = brightness & 0xFF
            payload[13] = speed & 0xFF
            
        payload[17] = 0xAA; payload[18] = 0x55
        payload[31] = sum(payload[:31]) % 256
        self._broadcast(payload)

    def set_per_key_colors(self, layout_dict):
        """
        Устанавливает индивидуальные цвета клавиш (Custom Mode).
        layout_dict: словарь {Индекс_или_Название_Клавиши: (R, G, B)}
        
        ВНИМАНИЕ: Запись в EEPROM. Не использовать чаще 1 раза в несколько секунд!
        """
        # Преобразуем названия в индексы, если нужно
        color_map = {}
        for k, color in layout_dict.items():
            if isinstance(k, str) and k in self.KEY_MAP:
                color_map[self.KEY_MAP[k]] = color
            elif isinstance(k, int):
                color_map[k] = color

        packets = []
        
        # 1. Init Packet (05 10 00 80 ...)
        init = bytearray(32)
        init[0] = 0x05; init[1] = 0x10; init[2] = 0x00; init[3] = 0x80
        init[12] = 0x05; init[13] = 0x00
        init[17] = 0xAA; init[18] = 0x55
        init[31] = sum(init[:31]) % 256
        packets.append(init)

        # 2. Data Packets (20 штук по 7 клавиш)
        for packet_idx in range(20):
            p = bytearray(32)
            p[0] = 0x14; p[1] = 0x1C; p[2] = packet_idx
            
            for i in range(7):
                idx = packet_idx * 7 + i
                offset = 3 + i * 4
                
                if idx in self.VALID_KEYS:
                    p[offset] = idx
                    if idx in color_map:
                        r, g, b = color_map[idx]
                        p[offset+1] = r & 0xFF
                        p[offset+2] = g & 0xFF
                        p[offset+3] = b & 0xFF
                else:
                    # Пустой слот
                    p[offset] = 0; p[offset+1] = 0; p[offset+2] = 0; p[offset+3] = 0
                    
            p[31] = sum(p[:31]) % 256
            packets.append(p)

        # 3. Final Packet (14 10 14 ...)
        final = bytearray(32)
        final[0] = 0x14; final[1] = 0x10; final[2] = 0x14
        final[17] = 0xAA; final[18] = 0x55
        final[31] = sum(final[:31]) % 256
        packets.append(final)

        # Отправляем всю последовательность
        for dev in self.devices:
            for p in packets:
                data = bytearray([0x00]) + p
                try:
                    dev.write(data)
                except:
                    pass
                # Задержка 50мс КРИТИЧЕСКИ важна для медленного контроллера клавиатуры!
                time.sleep(0.05)
                
        return True

    def get_battery_level(self):
        """
        Запрашивает уровень заряда батареи у клавиатуры (0-100%).
        Возвращает int (процент) или None, если не удалось прочитать.
        """
        payload = bytearray(32)
        payload[0] = 0x20; payload[1] = 0x01
        payload[31] = sum(payload[:31]) % 256
        data = bytearray([0x00]) + payload
        
        for dev in self.devices:
            try:
                # Отправляем запрос
                dev.write(data)
                
                # Ждем ответ (с таймаутом 200 мс)
                # Очищаем буфер от старых пакетов, пока не найдем нужный
                for _ in range(5):
                    res = dev.read(32, timeout_ms=200)
                    if res and res[0] == 0x20 and res[1] == 0x01:
                        return res[3]
            except:
                pass
                
        return None

if __name__ == "__main__":
    kb = KeyboardBacklight()
    
    print("Устанавливаем статичную кастомную раскладку (Per-Key RGB)...")
    
    # 1. Заливаем всю клавиатуру тусклым синим
    layout = {k: (0, 0, 30) for k in kb.VALID_KEYS}
        
    # 2. Красим WASD в красный
    for key in ['W', 'A', 'S', 'D']:
        layout[key] = (255, 0, 0)
            
    # 3. Красим Стрелки в зеленый
    for key in ['Up', 'Left', 'Down', 'Right']:
        layout[key] = (0, 255, 0)
        
    # Применяем
    kb.set_per_key_colors(layout)
    print("Раскладка применена!")
    kb.close()
