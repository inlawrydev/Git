"""
Roblox Lua Obfuscator — Продвинутый уровень защиты
Методы: XOR-шифрование, Minification, Junk Code, String Splitting
"""

import random
import string
import re
import base64


class AdvancedRobloxObfuscator:
    def __init__(self):
        self.var_counter = 0
        self.func_counter = 0
        self.used_names = set()
        
    def _generate_name(self, prefix='_'):
        """Генерация уникального случайного имени"""
        while True:
            # Используем похожие символы для визуальной путаницы
            chars = 'IlO0' + string.ascii_letters + string.digits
            name = prefix + ''.join(random.choices(chars, k=random.randint(8, 16)))
            if name not in self.used_names:
                self.used_names.add(name)
                return name
    
    def _xor_encrypt(self, text: str, key: int = None) -> tuple:
        """XOR-шифрование строки"""
        if key is None:
            key = random.randint(1, 255)
        encrypted = ''.join(chr(ord(c) ^ key) for c in text)
        # Экранируем для Lua
        escaped = encrypted.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        return escaped, key
    
    def _split_string(self, text: str, parts: int = None) -> list:
        """Разбиение строки на случайные части"""
        if parts is None:
            parts = random.randint(2, 5)
        if len(text) <= parts:
            return [text]
        
        indices = sorted(random.sample(range(1, len(text)), parts - 1))
        result = []
        prev = 0
        for idx in indices:
            result.append(text[prev:idx])
            prev = idx
        result.append(text[prev:])
        return result
    
    def _generate_junk_function(self) -> str:
        """Генерация мусорной функции"""
        name = self._generate_name('f')
        params = ', '.join(self._generate_name('p') for _ in range(random.randint(0, 3)))
        body = '\n'.join([
            f'local {self._generate_name()} = {random.randint(1, 999999)}',
            f'local {self._generate_name()} = function() return {random.randint(1, 999999)} end',
            f'return {random.randint(1, 999999)}'
        ])
        return f'local {name} = function({params})\n{body}\nend\n{name}()'
    
    def _generate_junk_code(self, count: int = 5) -> str:
        """Генерация блока мусорного кода"""
        junk = []
        for _ in range(count):
            junk.append(self._generate_junk_function())
        return '\n'.join(junk)
    
    def _minify(self, code: str) -> str:
        """Minification — удаление пробелов, комментариев, переносов"""
        # Удаляем однострочные комментарии
        code = re.sub(r'--[^\n]*', '', code)
        # Удаляем многострочные комментарии
        code = re.sub(r'--\[\[.*?\]\]', '', code, flags=re.DOTALL)
        # Удаляем лишние пробелы и переносы
        code = re.sub(r'\s+', ' ', code)
        # Удаляем пробелы вокруг операторов (осторожно)
        code = re.sub(r'\s*([=+\-*/<>~,;{}()\[\]])\s*', r'\1', code)
        # Удаляем пробелы в начале и конце
        code = code.strip()
        return code
    
    def _obfuscate_strings(self, code: str) -> str:
        """XOR-шифрование всех строковых литералов"""
        # Находим строки в одинарных и двойных кавычках
        pattern = r'(["\'])(.*?)\1'
        
        def replace_string(match):
            quote = match.group(1)
            original = match.group(2)
            
            if len(original) < 2:
                return match.group(0)
            
            # Разбиваем строку на части
            parts = self._split_string(original)
            
            if len(parts) == 1:
                # Простое XOR-шифрование
                encrypted, key = self._xor_encrypt(original)
                decrypt_func = self._generate_name('d')
                return f'(function(){decrypt_func}=function(s,k)local r=""for i=1,#s do r=r..string.char(bit32.bxor(string.byte(s,i),k))end return r end;return {decrypt_func}("{encrypted}",{key}))()'
            else:
                # Разбиваем на части + XOR для каждой
                obf_parts = []
                for part in parts:
                    if len(part) > 0:
                        encrypted, key = self._xor_encrypt(part)
                        obf_parts.append(f'"{encrypted}"')
                    else:
                        obf_parts.append('""')
                
                # Собираем обратно
                join_func = self._generate_name('j')
                decrypt_func = self._generate_name('x')
                parts_str = ','.join(obf_parts)
                
                return f'(function(){join_func}=function(t)local r=""for i=1,#t do r=r..t[i]end return r end;{decrypt_func}=function(s,k)local r=""for i=1,#s do r=r..string.char(bit32.bxor(string.byte(s,i),k))end return r end;return {join_func}({{{parts_str}}}))()'
        
        return re.sub(pattern, replace_string, code)
    
    def _obfuscate_numbers(self, code: str) -> str:
        """Обфускация чисел"""
        def replace_number(match):
            num = int(match.group(0))
            if num == 0:
                return '(1-1)'
            if num == 1:
                return '(2-1)'
            
            # Представляем как выражение
            methods = [
                lambda n: f'({n//2}+{n-n//2})',
                lambda n: f'({n+1}-1)',
                lambda n: f'({n*2}//2)',
                lambda n: f'({n*3}//3)',
                lambda n: f'(#{{' + ','.join('1' for _ in range(n)) + '}})',
            ]
            return random.choice(methods)(num)
        
        # Заменяем только отдельно стоящие числа
        return re.sub(r'\b\d+\b', replace_number, code)
    
    def _flatten_control_flow(self, code: str) -> str:
        """Control Flow Flattening — превращаем линейный код в state machine"""
        lines = [l.strip() for l in code.split('\n') if l.strip()]
        if len(lines) < 3:
            return code
        
        # Создаём state machine
        states = []
        for i, line in enumerate(lines):
            states.append(f'[{i}] = function() {line} _s = {i+1} end')
        
        states.append(f'[{len(lines)}] = function() _s = nil end')
        
        state_table = ',\n'.join(states)
        runner = f'''
(function()
    local _s = 0
    local _t = {{
        {state_table}
    }}
    while _s do
        _t[_s]()
    end
end)()
'''
        return runner
    
    def _rename_variables(self, code: str) -> str:
        """Переименование всех переменных и функций"""
        # Находим все имена
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        
        # Ключевые слова Lua + Roblox API, которые нельзя переименовывать
        keywords = {
            'local', 'function', 'end', 'if', 'then', 'else', 'elseif',
            'for', 'while', 'do', 'repeat', 'until', 'return', 'break',
            'true', 'false', 'nil', 'not', 'and', 'or', 'in',
            'pairs', 'ipairs', 'next', 'tonumber', 'tostring', 'type',
            'print', 'warn', 'error', 'assert', 'pcall', 'xpcall',
            'require', 'game', 'workspace', 'script', 'math', 'string',
            'table', 'coroutine', 'os', 'debug', 'bit32', 'buffer',
            'task', 'typeof', 'Instance', 'Vector3', 'CFrame', 'Color3',
            'UDim', 'UDim2', 'Enum', 'wait', 'spawn', 'delay',
            'loadstring', 'setfenv', 'getfenv', 'rawget', 'rawset',
            'select', 'unpack', 'pack', 'self', 'super', '_G', '_ENV'
        }
        
        # Собираем переменные для переименования
        mapping = {}
        for word in set(words):
            if word not in keywords and not word.startswith('_') and len(word) > 1:
                mapping[word] = self._generate_name()
        
        # Применяем замены (сначала длинные имена, чтобы не было частичных совпадений)
        for old_name in sorted(mapping.keys(), key=len, reverse=True):
            code = re.sub(r'\b' + re.escape(old_name) + r'\b', mapping[old_name], code)
        
        return code
    
    def obfuscate(self, code: str, level: str = "heavy") -> str:
        """
        Основной метод обфускации
        
        Args:
            code: Исходный Lua-код
            level: Уровень защиты — light | medium | heavy
        
        Returns:
            Обфусцированный код
        """
        if level == "light":
            # Только minification + переименование
            code = self._rename_variables(code)
            code = self._minify(code)
            return code
        
        elif level == "medium":
            # + XOR-шифрование строк
            code = self._rename_variables(code)
            code = self._obfuscate_strings(code)
            code = self._minify(code)
            # Добавляем немного мусора
            junk = self._generate_junk_code(3)
            code = junk + '\n' + code
            return self._minify(code)
        
        else:  # heavy
            # Полная защита
            # 1. Переименование
            code = self._rename_variables(code)
            
            # 2. XOR-шифрование строк
            code = self._obfuscate_strings(code)
            
            # 3. Обфускация чисел
            code = self._obfuscate_numbers(code)
            
            # 4. Мусорный код
            junk_before = self._generate_junk_code(random.randint(5, 10))
            junk_after = self._generate_junk_code(random.randint(3, 7))
            
            # 5. Оборачиваем в анонимную функцию
            wrapper_name = self._generate_name('w')
            code = f'''
(function()
    {junk_before}
    local {wrapper_name} = function()
        {code}
    end
    {wrapper_name}()
    {junk_after}
end)()
'''
            # 6. Minification — всё в одну строку!
            code = self._minify(code)
            
            # 7. Добавляем заголовок
            header = '--[[Obfuscated by IRY HUB OBF]] '
            return header + code


class BytecodeObfuscator:
    """
    Fallback: если LuaJIT доступен — компилируем в байткод
    """
    
    def __init__(self):
        self.advanced = AdvancedRobloxObfuscator()
    
    def obfuscate_bytecode(self, code: str) -> dict:
        import subprocess
        import tempfile
        import os
        
        result = {
            'success': False,
            'loader': None,
            'error': None
        }
        
        try:
            # Предобфускация
            code = self.advanced.obfuscate(code, level="medium")
            
            # Создаём временный файл
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(code)
                lua.write(code)
                lua_file = f.name
            
            bytecode_file = lua_file.replace('.lua', '.luac')
            
            # Компилируем
            try:
                subprocess.run(
                    ['luajit', '-b', lua_file, bytecode_file],
                    check=True, capture_output=True, timeout=10
                )
            except:
                subprocess.run(
                    ['lua5.1', '-o', bytecode_file, lua_file],
                    check=True, capture_output=True, timeout=10
                )
            
            # Читаем байткод
            with open(bytecode_file, 'rb') as f:
                bytecode = f.read()
            
            # XOR-шифруем байткод
            key = bytes([random.randint(1, 255) for _ in range(32)])
            encrypted = bytes(b ^ key[i % 32] for i, b in enumerate(bytecode))
            
            # Генерируем загрузчик
            hex_data = encrypted.hex()
            key_hex = key.hex()
            
            loader = f'--//Obfuscated\nlocal k=("{key_hex}"):gsub("..",function(h)return string.char(tonumber(h,16))end)local d=("{hex_data}"):gsub("..",function(h)return string.char(tonumber(h,16))end)local x=function(d,k)local r=""for i=1,#d do r=r..string.char(bit32.bxor(string.byte(d,i),string.byte(k,(i-1)%#k+1)))end return r end;local b=x(d,k)local f=loadstring(b)if f then f()else local buf=buffer.create(#b)for i=1,#b do buffer.writeu8(buf,i-1,string.byte(b,i))end local l=load(buf)if l then l()end end'
            
            result['success'] = True
            result['loader'] = loader
            
            os.unlink(lua_file)
            os.unlink(bytecode_file)
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
