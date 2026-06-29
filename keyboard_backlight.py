import hid

class KeyboardBacklight:
    """
    Класс для управления подсветкой клавиатуры через USB HID.
    
    Для использования необходимо знать Vendor ID (VID) и Product ID (PID) клавиатуры.
    Их можно посмотреть в диспетчере устройств или с помощью скрипта.
    """
    def __init__(self, vid, pid):
        self.vid = vid
        self.pid = pid
        self.devices = []
        
        # Находим все интерфейсы устройства с Vendor-Specific Usage Page (обычно >= 0xFF00)
        # У этой клавиатуры, например, есть MI_03 и MI_04. Один для макросов, другой для подсветки.
        for d in hid.enumerate(vid, pid):
            if d.get('usage_page', 0) >= 0xFF00:
                # Фильтруем интерфейсы: официальный драйвер использует MI_00 для USB и MI_03 для 2.4G
                path_str = d['path'].decode('utf-8', errors='ignore').upper()
                if "MI_00" in path_str or "MI_03" in path_str:
                    try:
                        dev = hid.device()
                        dev.open_path(d['path'])
                        dev.set_nonblocking(1)
                        self.devices.append(dev)
                        print(f"Открыт интерфейс: {d['path']}")
                    except Exception as e:
                        print(f"Не удалось открыть {d['path']}: {e}")
                    
        if not self.devices:
            raise RuntimeError(f"Не удалось найти/открыть HID-интерфейсы для устройства {hex(vid)}:{hex(pid)}")
            
    def close(self):
        """Закрыть соединение с устройством."""
        for dev in self.devices:
            try:
                dev.close()
            except:
                pass

    def set_color(self, r, g, b):
        """
        Установить цвет подсветки.
        """
        # Формируем 32-байтный пакет (как в дампе)
        payload = bytearray(32)
        payload[0] = 0x05
        payload[1] = 0x10
        payload[2] = 0x00
        payload[3] = 0x01
        
        payload[4] = r & 0xFF
        payload[5] = g & 0xFF
        payload[6] = b & 0xFF
        
        payload[12] = 0x05
        payload[13] = 0x03
        payload[17] = 0xAA
        payload[18] = 0x55
        
        payload[31] = sum(payload[:31]) % 256
        
        # На Windows hidapi требует +1 байт в начале для Report ID.
        # Если Report ID не используется самим устройством, мы передаем 0x00 в начале.
        data = bytearray([0x00]) + payload
        
        # Отправляем во все открытые вендорские интерфейсы
        # Один из них обязательно тот, который отвечает за подсветку
        for dev in self.devices:
            try:
                # Пробуем отправить 33 байта (с нулевым Report ID)
                dev.write(data)
                # На всякий случай дублируем отправку оригинального 32-байтного
                # если библиотека на другой ОС работает иначе
                dev.write(payload)
            except:
                pass
        
        return True

    VALID_KEYS = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 19, 20, 21, 22, 23, 24, 25, 
        26, 27, 28, 29, 30, 31, 32, 33, 34, 37, 38, 39, 40, 41, 42, 43, 44, 45, 
        46, 47, 48, 49, 50, 51, 52, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 
        66, 67, 68, 69, 70, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 
        86, 87, 88, 91, 92, 93, 94, 95, 96, 99, 100, 101, 102, 103, 104, 105, 
        106, 118, 119, 121, 122, 123
    ]

    def set_per_key_colors(self, key_colors):
        """
        Установить индивидуальный цвет для каждой клавиши.
        """
        # Формируем все пакеты заранее
        packets = []
        
        # 1. Инициализация
        init_payload = bytearray(32)
        init_payload[0] = 0x05
        init_payload[1] = 0x10
        init_payload[2] = 0x00
        init_payload[3] = 0x80
        init_payload[12] = 0x05
        init_payload[13] = 0x00
        init_payload[17] = 0xAA
        init_payload[18] = 0x55
        init_payload[31] = sum(init_payload[:31]) % 256
        packets.append(init_payload)

        # 2. 20 пакетов данных
        for packet_idx in range(20):
            payload = bytearray(32)
            payload[0] = 0x14
            payload[1] = 0x1C
            payload[2] = packet_idx
            
            for i in range(7):
                key_idx = packet_idx * 7 + i
                base_offset = 3 + i * 4
                
                if key_idx not in self.VALID_KEYS:
                    payload[base_offset] = 0
                    payload[base_offset+1] = 0
                    payload[base_offset+2] = 0
                    payload[base_offset+3] = 0
                else:
                    if key_idx in key_colors:
                        r, g, b = key_colors[key_idx]
                        payload[base_offset] = key_idx
                        payload[base_offset+1] = r & 0xFF
                        payload[base_offset+2] = g & 0xFF
                        payload[base_offset+3] = b & 0xFF
                    else:
                        payload[base_offset] = key_idx
                        payload[base_offset+1] = 0
                        payload[base_offset+2] = 0
                        payload[base_offset+3] = 0
                    
            payload[31] = sum(payload[:31]) % 256
            packets.append(payload)

        # 3. Финальный пакет
        final_payload = bytearray(32)
        final_payload[0] = 0x14
        final_payload[1] = 0x10
        final_payload[2] = 0x14
        final_payload[19] = 0xAA
        final_payload[20] = 0x55
        final_payload[31] = sum(final_payload[:31]) % 256
        packets.append(final_payload)
        
        # Отправляем всю последовательность целиком на каждое устройство по очереди,
        # чтобы пакеты не перемешивались (иначе клавиатура сбрасывает транзакцию).
        import time
        for dev in self.devices:
            for p in packets:
                data = bytearray([0x00]) + p
                try:
                    dev.write(data)
                except:
                    pass
                time.sleep(0.02) # Увеличенная задержка (20мс) для предотвращения потери пакетов контроллером
                
        return True

    # Предустановленные цвета из дампа
    def set_red(self): self.set_color(255, 0, 0)
    def set_orange(self): self.set_color(255, 128, 0)
    def set_yellow(self): self.set_color(255, 255, 0)
    def set_green(self): self.set_color(0, 255, 0)
    def set_turquoise(self): self.set_color(0, 255, 255)
    def set_blue(self): self.set_color(0, 0, 255)
    def set_purple(self): self.set_color(255, 0, 255)
    def set_white(self): self.set_color(255, 255, 255)
    def set_off(self): self.set_color(0, 0, 0)

if __name__ == "__main__":
    import time
    
    YOUR_VID = 0x05AC 
    YOUR_PID = 0x024F

    try:
        kb = KeyboardBacklight(YOUR_VID, YOUR_PID)
        
        print("Устанавливаем статичную кастомную раскладку (Per-Key RGB)...")
        print("ВНИМАНИЕ: Не используйте этот метод для частых анимаций (более 1 раза в секунду),")
        print("так как это изнашивает flash-память клавиатуры и может привести к ее зависанию!")
        
        # Создаем красивую статичную раскладку
        my_layout = {}
        
        # Заливаем всю клавиатуру тусклым синим
        for k in kb.VALID_KEYS:
            my_layout[k] = (0, 0, 30)
            
        # Красим WASD (примерные индексы, могут отличаться) в ярко-красный
        for k in [41, 56, 57, 58]: # Пример индексов
            if k in kb.VALID_KEYS:
                my_layout[k] = (255, 0, 0)
                
        # Стрелки (примерные индексы) в зеленый
        for k in [118, 119, 121, 122]:
            if k in kb.VALID_KEYS:
                my_layout[k] = (0, 255, 0)
                
        kb.set_per_key_colors(my_layout)
        
        print("Раскладка успешно применена!")
        
        kb.close()
    except Exception as e:
        print(f"Ошибка: {e}")
