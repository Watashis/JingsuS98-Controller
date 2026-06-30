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

    # Стандартные USB HID Keyboard/Keypad Usage ID (Usage Page 0x07).
    # Используются ТОЛЬКО для поля "что выводить" в remap_key() — это другая
    # система индексации, не путать с KEY_MAP (физическое положение клавиши).
    # Покрыты самые частые клавиши; полная таблица — USB HID Usage Tables.
    HID_USAGE = {
        'A': 4, 'B': 5, 'C': 6, 'D': 7, 'E': 8, 'F': 9, 'G': 10, 'H': 11,
        'I': 12, 'J': 13, 'K': 14, 'L': 15, 'M': 16, 'N': 17, 'O': 18,
        'P': 19, 'Q': 20, 'R': 21, 'S': 22, 'T': 23, 'U': 24, 'V': 25,
        'W': 26, 'X': 27, 'Y': 28, 'Z': 29,
        '1': 30, '2': 31, '3': 32, '4': 33, '5': 34,
        '6': 35, '7': 36, '8': 37, '9': 38, '0': 39,
        'Enter': 40, 'Esc': 41, 'Backspace': 42, 'Tab': 43, 'Space': 44,
        '-': 45, '=': 46, '[': 47, ']': 48, '\\': 49, ';': 51, '\'': 52,
        '`': 53, ',': 54, '.': 55, '/': 56, 'CapsLock': 57,
        'F1': 58, 'F2': 59, 'F3': 60, 'F4': 61, 'F5': 62, 'F6': 63,
        'F7': 64, 'F8': 65, 'F9': 66, 'F10': 67, 'F11': 68, 'F12': 69,
        'PrintScreen': 70, 'Pause': 72, 'Insert': 73, 'Home': 74,
        'PgUp': 75, 'Delete': 76, 'End': 77, 'PgDn': 78,
        'Right': 79, 'Left': 80, 'Down': 81, 'Up': 82, 'NumLock': 83,
        'Ctrl_L': 224, 'Shift_L': 225, 'Alt_L': 226, 'Win_L': 227,
        'Ctrl_R': 228, 'Shift_R': 229, 'Alt_R': 230, 'Win_R': 231,
    }
    
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

    # Биты стандартного USB HID modifier byte (Usage Page 0x07, modifier byte
    # из boot keyboard report). Используются в remap_key(modifiers=...).
    MODIFIER_BITS = {
        'Ctrl_L': 0x01, 'Shift_L': 0x02, 'Alt_L': 0x04, 'Win_L': 0x08,
        'Ctrl_R': 0x10, 'Shift_R': 0x20, 'Alt_R': 0x40, 'Win_R': 0x80,
        # Алиасы без _L (обычно подразумевают левую клавишу)
        'Ctrl': 0x01, 'Shift': 0x02, 'Alt': 0x04, 'Win': 0x08,
    }

    def remap_key(self, physical_key, output_key, fn_layer=0, modifiers=0):
        """
        Переназначает физическую клавишу на новое действие (простой keycode,
        с опциональными модификаторами — Ctrl/Shift/Alt/Win — то есть
        полноценное сочетание клавиш). macro_type=2 в терминах официального
        софта. Подтверждено реверсом дампов layout.json и layout_fn.json
        (см. CLAUDE.md, 2026-06-30).

        physical_key: имя клавиши из KEY_MAP (например 'W') или её индекс.
        output_key:   имя клавиши из HID_USAGE (например 'B') или её
                      числовой USB HID usage code напрямую.
        fn_layer:     0 = слой Top, 1 = слой Fn.
                      ВАЖНО: слой кодируется КОМАНДНЫМ БАЙТОМ (0x03 для Top,
                      0x0D для Fn), а не отдельным полем в payload — это
                      разные команды, не флаг.
        modifiers:    битовая маска MODIFIER_BITS (например Ctrl_L=0x01),
                      либо список имён (например ['Ctrl_L']) для сочетаний
                      типа Ctrl+S. 0 = без модификаторов.
        """
        if isinstance(physical_key, str):
            if physical_key not in self.KEY_MAP:
                raise ValueError(f"Неизвестная физическая клавиша: {physical_key}")
            phys_idx = self.KEY_MAP[physical_key]
        else:
            phys_idx = physical_key

        if isinstance(output_key, str):
            if output_key not in self.HID_USAGE:
                raise ValueError(f"Неизвестный выходной код клавиши: {output_key}")
            hid_code = self.HID_USAGE[output_key]
        else:
            hid_code = output_key

        if isinstance(modifiers, (list, tuple, set)):
            mod_mask = 0
            for m in modifiers:
                if m not in self.MODIFIER_BITS:
                    raise ValueError(f"Неизвестный модификатор: {m}")
                mod_mask |= self.MODIFIER_BITS[m]
        else:
            mod_mask = modifiers

        cmd = 0x0D if fn_layer else 0x03

        payload = bytearray(32)
        payload[0] = cmd; payload[1] = 0x04
        payload[2] = phys_idx & 0xFF
        payload[3] = 0x02  # macro_type = простой keycode (опц. с модификаторами)
        payload[4] = mod_mask & 0xFF
        payload[5] = hid_code & 0xFF
        payload[31] = sum(payload[:31]) % 256
        self._broadcast(payload)

    def clear_remap(self, physical_key, fn_layer=0):
        """
        Сбрасывает ремап клавиши на стандартное поведение.

        Подтверждено реверсом дампа layout_remove.json (2026-06-30):
        официальный софт сам "очищает" ремап точно так же — identity-ремап
        (клавиша назначается сама на себя) через тот же протокол
        remap_key(). Отдельной команды "удалить запись" не существует.
        Работает только для клавиш, чьё имя совпадает в обеих таблицах
        (KEY_MAP и HID_USAGE) — то есть для букв, цифр и части служебных
        клавиш. Для остальных кидает ValueError.
        """
        if physical_key not in self.HID_USAGE:
            raise ValueError(
                f"Не знаю код по умолчанию для '{physical_key}' "
                f"(нет в HID_USAGE) — нечем восстановить identity-ремап."
            )
        self.remap_key(physical_key, physical_key, fn_layer=fn_layer, modifiers=0)

    def set_full_keymap(self, layout_dict, fn_layer=0):
        """
        Заливает ПОЛНУЮ раскладку слоя одной bulk-последовательностью —
        ровно так, как это делает официальный софт при загрузке профиля.
        Расшифровано из дампа layout.json (см. CLAUDE.md, 2026-06-30,
        раздел "Массовая выгрузка раскладки").

        layout_dict: словарь {физическая_клавиша: действие}, где
            физическая_клавиша — имя из KEY_MAP или индекс;
            действие — одно из:
              * имя из HID_USAGE / число (простой keycode),
              * кортеж (output_key, modifiers) для сочетаний, где modifiers —
                маска или список имён из MODIFIER_BITS,
              * None / отсутствие клавиши в словаре — оставить дефолт (то
                есть стандартное поведение этой клавиши).
        fn_layer: 0 = Top (cmd 0x10), 1 = Fn (cmd 0x12).

        Клавиши, которых нет в словаре, заливаются как нули = дефолт. То
        есть это ПОЛНАЯ замена раскладки слоя, а не точечная правка.

        ⚠️ РЕВЕРС ПОДТВЕРЖДЁН ДЕКОДОМ, НО САМА ОТПРАВКА ЕЩЁ НЕ ПРОВЕРЕНА НА
        ЖЕЛЕЗЕ (в отличие от remap_key). Пишет в энергонезависимую память —
        не гонять в цикле.
        """
        cmd = 0x12 if fn_layer else 0x10

        # Нормализуем вход: phys_idx -> (macro_type, modifier, hid_code, extra)
        slots = {}
        for k, action in layout_dict.items():
            if isinstance(k, str):
                if k not in self.KEY_MAP:
                    raise ValueError(f"Неизвестная физическая клавиша: {k}")
                phys_idx = self.KEY_MAP[k]
            else:
                phys_idx = k

            if action is None:
                continue

            modifiers = 0
            if isinstance(action, tuple):
                output_key, modifiers = action
            else:
                output_key = action

            if isinstance(output_key, str):
                if output_key not in self.HID_USAGE:
                    raise ValueError(f"Неизвестный выходной код: {output_key}")
                hid_code = self.HID_USAGE[output_key]
            else:
                hid_code = output_key

            if isinstance(modifiers, (list, tuple, set)):
                mod_mask = 0
                for m in modifiers:
                    mod_mask |= self.MODIFIER_BITS[m]
            else:
                mod_mask = modifiers

            slots[phys_idx] = (0x02, mod_mask & 0xFF, hid_code & 0xFF, 0x00)

        packets = []
        # 20 data-пакетов по 7 клавиш (адресация key# = pidx*7 + i, как у RGB)
        for pidx in range(20):
            p = bytearray(32)
            p[0] = cmd; p[1] = 0x1C; p[2] = pidx
            for i in range(7):
                keynum = pidx * 7 + i
                off = 3 + i * 4
                if keynum in slots:
                    mt, mod, code, extra = slots[keynum]
                    p[off] = mt; p[off+1] = mod; p[off+2] = code; p[off+3] = extra
                # иначе слот остаётся нулевым = дефолт
            p[31] = sum(p[:31]) % 256
            packets.append(p)

        # Финальный/commit-пакет: <cmd> 10 14 .. AA 55 00 <cmd> 10 14 ..
        final = bytearray(32)
        final[0] = cmd; final[1] = 0x10; final[2] = 0x14
        final[17] = 0xAA; final[18] = 0x55
        final[20] = cmd; final[21] = 0x10; final[22] = 0x14
        final[31] = sum(final[:31]) % 256
        packets.append(final)

        for dev in self.devices:
            for p in packets:
                data = bytearray([0x00]) + p
                try:
                    dev.write(data)
                except:
                    pass
                time.sleep(0.025)  # темп близкий к официальному софту (~25мс)

    def clear_layer(self, fn_layer=0):
        """
        Сбрасывает ВЕСЬ слой в дефолт одной bulk-выгрузкой пустой раскладки —
        именно так официальный софт "очищает" при загрузке пустого профиля
        (подтверждено дампами layout_clear.json / layout_empty.json).
        В отличие от identity-ремапа в clear_all_remaps(), этот метод
        сбрасывает ЛЮБЫЕ клавиши (не только буквы/цифры), и делает это одной
        атомарной последовательностью.
        """
        self.set_full_keymap({}, fn_layer=fn_layer)

    def clear_all_remaps(self, fn_layer=0, delay=0.2):
        """
        Сбрасывает на стандартное поведение все клавиши, для которых
        известен код по умолчанию (пересечение KEY_MAP и HID_USAGE — буквы,
        цифры, часть служебных). Identity-ремап — тот же механизм, которым
        пользуется официальный софт для ОДНОЙ клавиши (см. clear_remap()).

        ПРИМЕЧАНИЕ: для полного сброса слоя предпочтительнее clear_layer() —
        он использует bulk-выгрузку (как делает официальный софт при
        загрузке пустого профиля) и сбрасывает ВСЕ клавиши, а не только те,
        для которых известен HID-код. Этот метод оставлен как запасной
        вариант поклавишного сброса.

        ВНИМАНИЕ: каждая клавиша — отдельная запись (вероятно в EEPROM).
        Не вызывайте эту функцию часто/в цикле — между записями выдерживается
        пауза `delay` сек, но злоупотреблять всё равно не стоит (см.
        предупреждение про износ EEPROM у set_per_key_colors()).
        """
        common_keys = [k for k in self.KEY_MAP if k in self.HID_USAGE]
        for key in common_keys:
            self.remap_key(key, key, fn_layer=fn_layer, modifiers=0)
            time.sleep(delay)
        return common_keys

    def send_music_frame(self, bands, active=2):
        """
        Отправляет один кадр "живой" музыкальной подсветки (live, без записи
        в EEPROM): командный байт 0x0B, 19 значений амплитуды по полосам.
        Подтверждено реверсом дампов music.json/music_2.json (см. CLAUDE.md).

        ПРИМЕЧАНИЕ: это лишь ФИД АМПЛИТУДЫ для встроенного в прошивку
        визуализатора — сама анимация (что и где загорается) зашита в чип.
        Произвольно "рисовать" кадры через этот канал нельзя, прошивка сама
        решает, как отобразить переданные уровни.

        bands: список/кортеж из 19 чисел (0-6) — амплитуда по полосам/колонкам.
        active: 0 = тишина, 1 = переход (fade), 2 = звук активен.
        """
        if len(bands) != 19:
            raise ValueError("bands должен содержать ровно 19 значений (0-6)")

        payload = bytearray(32)
        payload[0] = 0x0B; payload[1] = 0x1C; payload[2] = 0x00
        payload[3] = 0x04; payload[4] = 0x0B; payload[5] = 0x64
        payload[6] = active & 0xFF
        for i, v in enumerate(bands):
            payload[7 + i] = v & 0xFF
        payload[31] = sum(payload[:31]) % 256
        self._broadcast(payload)

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
