"""
Roblox Lua Obfuscator — Bytecode Level
Использует luajit для компиляции в байткод + дополнительная защита
"""

import subprocess
import tempfile
import os
import random
import string

class RobloxObfuscator:
    def __init__(self):
        self.bytecode_magic = b'\x1bLua'
        self.jit_magic = b'\x1bLJ\x02'
        
    def _generate_random_string(self, length=16):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def _add_junk_comments(self, code: str) -> str:
        junk = []
        for _ in range(random.randint(5, 15)):
            comment = '-- ' + self._generate_random_string(random.randint(20, 50))
            junk.append(comment)
        lines = code.split('\n')
        for j in junk:
            pos = random.randint(0, len(lines))
            lines.insert(pos, j)
        return '\n'.join(lines)
    
    def obfuscate_bytecode(self, code: str) -> dict:
        result = {
            'success': False,
            'bytecode': None,
            'loader': None,
            'error': None
        }
        
        try:
            preprocessed = self._add_junk_comments(code)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
                f.write(preprocessed)
                lua_file = f.name
            
            bytecode_file = lua_file.replace('.lua', '.luac')
            
            try:
                subprocess.run(
                    ['luajit', '-b', lua_file, bytecode_file],
                    check=True,
                    capture_output=True,
                    timeout=10
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                subprocess.run(
                    ['lua5.1', '-o', bytecode_file, lua_file],
                    check=True,
                    capture_output=True,
                    timeout=10
                )
            
            with open(bytecode_file, 'rb') as f:
                bytecode = f.read()
            
            protected_bytecode = self._protect_bytecode(bytecode)
            loader = self._generate_loader(protected_bytecode)
            
            result['success'] = True
            result['bytecode'] = protected_bytecode.hex()
            result['loader'] = loader
            
            os.unlink(lua_file)
            os.unlink(bytecode_file)
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def _protect_bytecode(self, bytecode: bytes) -> bytes:
        key = bytes([random.randint(1, 255) for _ in range(16)])
        encrypted = bytes(b ^ key[i % 16] for i, b in enumerate(bytecode))
        return key + encrypted
    
    def _generate_loader(self, protected_bytecode: bytes) -> str:
        hex_data = protected_bytecode.hex()
        
        loader = f'''--// Obfuscated by RobloxObfuscator Bot
--// Bytecode Level Protection

local function decrypt_bytecode(hex_str)
    local data = ""
    for i = 1, #hex_str, 2 do
        data = data .. string.char(tonumber(hex_str:sub(i, i+1), 16))
    end
    return data
end

local function xor_decrypt(data, key)
    local result = ""
    for i = 1, #data do
        result = result .. string.char(bit32.bxor(
            string.byte(data, i),
            string.byte(key, (i-1) % #key + 1)
        ))
    end
    return result
end

local encrypted = decrypt_bytecode("{hex_data}")
local key = encrypted:sub(1, 16)
local bytecode = xor_decrypt(encrypted:sub(17), key)

local success, err = pcall(function()
    local func = loadstring(bytecode)
    if func then
        func()
    else
        local buffer = buffer.create(#bytecode)
        for i = 1, #bytecode do
            buffer.writeu8(buffer, i-1, string.byte(bytecode, i))
        end
        local loaded = load(buffer)
        if loaded then loaded() end
    end
end)

if not success then
    warn("[Obfuscator] Execution error: " .. tostring(err))
end
'''
        return loader


class SimpleObfuscator:
    def __init__(self):
        self.var_counter = 0
        
    def _random_name(self):
        self.var_counter += 1
        chars = 'IlO0'
        return '_' + ''.join(random.choices(chars, k=8)) + str(self.var_counter)
    
    def obfuscate(self, code: str) -> str:
        import re
        
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        keywords = {'local', 'function', 'end', 'if', 'then', 'else', 
                   'elseif', 'for', 'while', 'do', 'return', 'true', 
                   'false', 'nil', 'not', 'and', 'or', 'in', 'repeat',
                   'until', 'break', 'continue', 'pairs', 'ipairs',
                   'print', 'warn', 'error', 'pcall', 'xpcall',
                   'require', 'game', 'workspace', 'script', 'math',
                   'string', 'table', 'coroutine', 'os', 'debug',
                   'bit32', 'buffer', 'task', 'typeof', 'Instance',
                   'Vector3', 'CFrame', 'Color3', 'UDim', 'UDim2'}
        
        mapping = {}
        for word in set(words):
            if word not in keywords and not word.startswith('_'):
                mapping[word] = self._random_name()
        
        def replace_word(match):
            word = match.group(0)
            return mapping.get(word, word)
        
        obfuscated = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', replace_word, code)
        junk = self._generate_junk()
        
        return f'--// Obfuscated\n{junk}\n{obfuscated}'
    
    def _generate_junk(self) -> str:
        junk_code = []
        for _ in range(random.randint(3, 8)):
            name = self._random_name()
            junk_code.append(f'local {name} = function() return {random.randint(1,9999)} end')
            junk_code.append(f'{name}()')
        return '\n'.join(junk_code)
