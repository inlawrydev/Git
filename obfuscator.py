
import random
import string
import re


class AdvancedRobloxObfuscator:

    _long_bracket = re.compile(r'\[(=*)\[')

    KEYWORDS = {
        'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for',
        'function', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat',
        'return', 'then', 'true', 'until', 'while', 'continue', 'self',
        'export', 'type', 'typeof', '_G', '_VERSION', '_ENV'
    }

    GLOBALS = {
        'game', 'workspace', 'Workspace', 'script', 'shared', 'plugin',
        'math', 'string', 'table', 'coroutine', 'os', 'debug', 'task',
        'bit', 'bit32', 'buffer', 'utf8', 'utf16', 'vector',
        'Vector2', 'Vector3', 'CFrame', 'Color3', 'BrickColor', 'UDim', 'UDim2',
        'Ray', 'Region3', 'Rect', 'TweenInfo', 'NumberRange', 'NumberSequence',
        'NumberSequenceKeypoint', 'ColorSequence', 'ColorSequenceKeypoint',
        'PhysicalProperties', 'RaycastParams', 'OverlapParams', 'Font',
        'Enum', 'Instance', 'Random', 'DateTime', 'Faces', 'Axes',
        'next', 'ipairs', 'pairs', 'print', 'warn', 'error', 'assert',
        'pcall', 'xpcall', 'select', 'tonumber', 'tostring', 'type',
        'typeof', 'unpack', 'rawget', 'rawset', 'rawequal', 'rawlen',
        'setmetatable', 'getmetatable', 'getfenv', 'setfenv',
        'loadstring', 'load', 'require', 'collectgarbage', 'gcinfo',
        'newproxy', 'wait', 'spawn', 'delay', 'defer', 'tick', 'time',
        'elapsedTime', 'settings', 'UserSettings', 'version',
        'syn', 'synapse', 'request', 'http_request', 'http',
        'WebSocket', 'websocket', 'identifyexecutor', 'getexecutorname',
        'getgenv', 'getsenv', 'getrenv', 'getreg', 'getgc', 'getgcobjects',
        'getconnections', 'getloadedmodule', 'getcallingscript', 'gethui',
        'getinstances', 'getnilinstances', 'getthreadcontext', 'setthreadcontext',
        'getidentity', 'setidentity', 'queue_on_teleport',
        'setclipboard', 'setrbxclipboard', 'toclipboard',
        'writefile', 'readfile', 'appendfile', 'loadfile', 'isfile',
        'isfolder', 'makefolder', 'delfolder', 'delfile', 'listfiles',
        'hookfunction', 'replaceclosure', 'hookmetamethod', 'hookglobalfunction',
        'isfunctionhooked', 'isexecutorclosure', 'is_synapse_function', 'isluau',
        'getrawmetatable', 'setreadonly', 'isreadonly', 'checkcaller',
        'newcclosure', 'clonefunction', 'islclosure', 'iscclosure',
        'firesignal', 'firetouchinterest', 'fireclickdetector',
        'fireproximityprompt', 'setfpscap', 'getfpscap',
        'keypress', 'keyrelease', 'mouse1press', 'mouse1release',
        'mouse2press', 'mouse2release', 'mousemoveabs', 'mouserelmove',
        'isrbxactive', 'setrenderproperty', 'getrenderproperty', 'cloneref',
        'messagebox', 'printconsole', 'downloadfile',
        'Drawing', 'drawing',
        'getupvalue', 'setupvalue', 'getupvalues',
        'getconstant', 'setconstant', 'getconstants',
    }

    def __init__(self):
        self.used_names = set()
        self.reserved = set()


    def _generate_name(self, prefix='_'):
        chars = 'IlO0' + string.ascii_letters + string.digits
        while True:
            name = prefix + ''.join(random.choices(chars, k=random.randint(8, 16)))
            if name not in self.used_names and name not in self.reserved:
                self.used_names.add(name)
                return name


    def _mask_strings(self, code: str):
        strings = []
        tag = '__IRYS' + ''.join(random.choices(string.ascii_uppercase, k=6)) + '_'
        while tag in code:
            tag = '__IRYS' + ''.join(random.choices(string.ascii_uppercase, k=6)) + '_'

        result = []
        i = 0
        n = len(code)

        while i < n:
            c = code[i]

            if c == '-' and i + 1 < n and code[i + 1] == '-':
                m = self._long_bracket.match(code, i + 2)
                if m:
                    closer = ']' + m.group(1) + ']'
                    end = code.find(closer, m.end())
                    result.append(' ')
                    i = n if end == -1 else end + len(closer)
                else:
                    end = code.find('\n', i)
                    result.append(' ')
                    i = n if end == -1 else end
                continue

            if c == '"' or c == "'":
                j = i + 1
                while j < n:
                    if code[j] == '\\':
                        j += 2
                        continue
                    if code[j] == c:
                        break
                    j += 1
                if j < n and code[j] == c:
                    raw = code[i:j + 1]
                    strings.append(raw)
                    result.append(f'{tag}{len(strings) - 1}{tag}')
                    i = j + 1
                else:
                    result.append(code[i:])
                    i = n
                continue

            if c == '[':
                m = self._long_bracket.match(code, i)
                if m:
                    closer = ']' + m.group(1) + ']'
                    end = code.find(closer, m.end())
                    if end != -1:
                        raw = code[i:end + len(closer)]
                        strings.append(raw)
                        result.append(f'{tag}{len(strings) - 1}{tag}')
                        i = end + len(closer)
                        continue
                result.append(c)
                i += 1
                continue

            result.append(c)
            i += 1

        return ''.join(result), strings, tag

    def _unmask(self, code: str, strings: list, tag: str) -> str:
        pattern = re.compile(re.escape(tag) + r'(\d+)' + re.escape(tag))
        return pattern.sub(lambda m: strings[int(m.group(1))], code)


    def _lua_unescape(self, s: str) -> bytes:
        out = bytearray()
        i = 0
        n = len(s)
        simple = {'n': 10, 't': 9, 'r': 13, 'a': 7, 'b': 8, 'f': 12, 'v': 11,
                  '\\': 92, '"': 34, "'": 39, '\n': 10, '\r': 13}
        while i < n:
            c = s[i]
            if c == '\\' and i + 1 < n:
                nxt = s[i + 1]
                if nxt in simple:
                    out.append(simple[nxt]); i += 2
                elif nxt == 'z':
                    i += 2
                    while i < n and s[i] in ' \t\r\n':
                        i += 1
                elif nxt == 'x':
                    j = i + 2
                    h = ''
                    while j < n and len(h) < 2 and s[j] in '0123456789abcdefABCDEF':
                        h += s[j]; j += 1
                    if h:
                        out.append(int(h, 16)); i = j
                    else:
                        out.append(ord('x')); i += 2
                elif nxt == 'u':
                    m = re.match(r'\\u\{([0-9a-fA-F]+)\}', s[i:])
                    if m:
                        out.extend(chr(int(m.group(1), 16)).encode('utf-8'))
                        i += m.end()
                    else:
                        out.append(ord('u')); i += 2
                elif nxt.isdigit():
                    j = i + 1
                    d = ''
                    while j < n and len(d) < 3 and s[j].isdigit():
                        d += s[j]; j += 1
                    out.append(int(d) & 0xFF)
                    i = j
                else:
                    out.extend(nxt.encode('utf-8')); i += 2
            else:
                out.extend(c.encode('utf-8'))
                i += 1
        return bytes(out)

    def _lua_escape_bytes(self, data: bytes) -> str:
        parts = []
        for b in data:
            if b == 92:
                parts.append('\\\\')
            elif b == 34:
                parts.append('\\"')
            elif 32 <= b <= 126:
                parts.append(chr(b))
            else:
                parts.append('\\%d' % b)
        return ''.join(parts)


    def _best_xor(self, data: bytes):
        best_enc, best_key, best_cost = None, None, None
        for _ in range(10):
            k = random.randint(1, 255)
            enc = bytes(b ^ k for b in data)
            cost = 0
            for b in enc:
                if b < 32 or b > 126 or b == 34 or b == 92:
                    cost += 1
            if best_cost is None or cost < best_cost:
                best_enc, best_key, best_cost = enc, k, cost
                if cost == 0:
                    break
        return best_enc, best_key

    def _make_string_expr(self, data: bytes, dec: str) -> str:
        parts_count = random.randint(1, 3)
        if len(data) < parts_count:
            parts_count = 1
        if parts_count == 1:
            pieces = [data]
        else:
            cuts = sorted(random.sample(range(1, len(data)), parts_count - 1))
            pieces = []
            prev = 0
            for cut in cuts:
                pieces.append(data[prev:cut])
                prev = cut
            pieces.append(data[prev:])

        exprs = []
        for piece in pieces:
            if not piece:
                continue
            enc, key = self._best_xor(piece)
            exprs.append('%s("%s",%d)' % (dec, self._lua_escape_bytes(enc), key))

        if not exprs:
            return ''
        if len(exprs) == 1:
            return '(' + exprs[0] + ')'
        return '(' + '..'.join(exprs) + ')'

    def _obfuscate_strings(self, masked: str, strings: list, tag: str):
        dec = self._generate_name('v')
        pattern = re.compile(re.escape(tag) + r'(\d+)' + re.escape(tag))

        def repl(m):
            raw = m.group(0)
            try:
                raw = strings[int(m.group(1))]
                if raw.startswith('"') or raw.startswith("'"):
                    data = self._lua_unescape(raw[1:-1])
                else:
                    m2 = self._long_bracket.match(raw)
                    if not m2:
                        return raw
                    lvl = len(m2.group(1))
                    inner = raw[2 + lvl:len(raw) - (2 + lvl)]
                    if inner.startswith('\r\n'):
                        inner = inner[2:]
                    elif inner.startswith('\n'):
                        inner = inner[1:]
                    data = inner.encode('utf-8')
                if len(data) < 2:
                    return raw
                expr = self._make_string_expr(data, dec)
                return expr if expr else raw
            except Exception:
                return raw

        return pattern.sub(repl, masked), dec


    def _rename_variables(self, masked: str) -> str:
        protected = set(self.KEYWORDS) | set(self.GLOBALS)

        for m in re.finditer(r'[.:]\s*([A-Za-z_]\w*)', masked):
            protected.add(m.group(1))

        for m in re.finditer(r'[{,]\s*([A-Za-z_]\w*)\s*=(?!=)', masked):
            protected.add(m.group(1))

        stmt = re.compile(
            r'(?:(?<=[;\n)])|(?<=\bthen\b)|(?<=\bdo\b)|(?<=\belse\b)'
            r'|(?<=\bend\b)|(?<=\brepeat\b)|^)[ \t]*([A-Za-z_]\w*)[ \t]*=(?!=)',
            re.M
        )
        for m in stmt.finditer(masked):
            protected.add(m.group(1))

        for m in re.finditer(r'(?m)^[ \t]*([A-Za-z_]\w*)\s*\.', masked):
            protected.add(m.group(1))

        for m in re.finditer(r'(?<!local )\bfunction\s+([A-Za-z_]\w*)\s*\(', masked):
            protected.add(m.group(1))

        mapping = {}
        for word in set(re.findall(r'\b[A-Za-z_]\w*\b', masked)):
            if word in protected or word.startswith('_'):
                continue
            mapping[word] = self._generate_name()

        names = sorted(mapping.keys(), key=len, reverse=True)
        for cs in range(0, len(names), 400):
            chunk = names[cs:cs + 400]
            pattern = re.compile(r'\b(' + '|'.join(re.escape(x) for x in chunk) + r')\b')
            masked = pattern.sub(lambda m: mapping[m.group(1)], masked)
        return masked


    def _number_expr(self, n: int) -> str:
        if n == 0:
            return random.choice(['(0*7)', '(5-5)', '(3-3)'])
        if n == 1:
            return random.choice(['(2-1)', '(1*1)', '(6-5)'])
        choices = []
        a = random.randint(0, n)
        choices.append('(%d+%d)' % (a, n - a))
        k = random.randint(1, 999)
        choices.append('(%d-%d)' % (n + k, k))
        if n <= 12:
            choices.append('(#{' + ','.join(['1'] * n) + '})')
        if n % 2 == 0:
            choices.append('(%d*2)' % (n // 2))
        if n % 3 == 0 and n > 2:
            choices.append('(%d*3)' % (n // 3))
        return random.choice(choices)

    def _obfuscate_numbers(self, code: str) -> str:
        masked, strings, tag = self._mask_strings(code)
        pattern = re.compile(r'(?<![\w.\\])\d+(?![\w.])')

        def repl(m):
            try:
                return self._number_expr(int(m.group(0)))
            except Exception:
                return m.group(0)

        masked = pattern.sub(repl, masked)
        return self._unmask(masked, strings, tag)


    def _generate_junk_function(self) -> str:
        name = self._generate_name('f')
        params = ', '.join(self._generate_name('p') for _ in range(random.randint(0, 3)))
        variant = random.randint(0, 3)

        if variant == 0:
            v1 = self._generate_name()
            v2 = self._generate_name()
            body = (
                f'local {v1}={random.randint(1, 999999)}\n'
                f'local {v2}=function()return {random.randint(1, 999999)}end\n'
                f'return {v1}+{v2}()'
            )
        elif variant == 1:
            t = self._generate_name('t')
            items = ','.join(str(random.randint(1, 999)) for _ in range(random.randint(2, 6)))
            body = f'local {t}={{{items}}}\nreturn #{t}+{random.randint(1, 99)}'
        elif variant == 2:
            a = self._generate_name()
            b = self._generate_name()
            body = (
                f'local {a}={random.randint(1, 999)}\n'
                f'local {b}={random.randint(1, 999)}\n'
                f'return ({a}*{b})%{random.randint(2, 97)}'
            )
        else:
            v = self._generate_name()
            body = f'local {v}=math.floor(math.random()*{random.randint(10, 9999)})\nreturn {v}'

        return f'local {name}=function({params})\n{body}\nend\n{name}()'

    def _generate_junk_code(self, count: int = 5) -> str:
        return '\n'.join(self._generate_junk_function() for _ in range(count))


    def _minify(self, code: str) -> str:
        masked, strings, tag = self._mask_strings(code)
        masked = re.sub(r'[ \t]+', ' ', masked)
        masked = re.sub(r'\s*\n\s*', ' ', masked)
        masked = re.sub(r' ?([=+*/<>~,;{}()\[\]]) ?', r'\1', masked)
        masked = masked.strip()
        return self._unmask(masked, strings, tag)


    def obfuscate(self, code: str) -> str:
        if not code or not code.strip():
            return '--[[ IRY HUB OBF ]]'

        self.used_names = set()
        self.reserved = set(re.findall(r'[A-Za-z_]\w*', code))

        masked, strings, tag = self._mask_strings(code)


        try:
            masked, dec = self._obfuscate_strings(masked, strings, tag)
        except Exception:
            masked = self._unmask(masked, strings, tag)
            dec = self._generate_name('v')

        decoder = (
            'local bx=function(a,b)local r,p=0,1 while a>0 or b>0 do '
            'local x=a%%2 local y=b%%2 if x~=y then r=r+p end '
            'a=(a-x)/2 b=(b-y)/2 p=p*2 end return r end '
            'local %s=function(s,k)local t={}for i=1,#s do '
            't[i]=string.char(bx(string.byte(s,i),k))end '
            'return table.concat(t)end' % dec
        )
        full = decoder + '\n' + masked

        try:
            full = self._minify(full)
        except Exception:
            full = re.sub(r'\s*\n\s*', ' ', full).strip()

        return '--[[ IRY HUB OBF | DS https://discord.gg/N3KCdD7Yn ]] ' + full
