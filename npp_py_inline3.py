# npp_py_inline3.py
import re
import math
import os
import sys
import operator 
import types

# =====================================================================
# 1. ИНТЕРФЕЙСНЫЕ ФУНКЦИИ И СПРАВКА
# =====================================================================
def open_tab(title, content, is_manual=False, file_path=None):
    target_buffer = None
    for buffer_id in notepad.getFiles():
        if title in buffer_id[0]:
            target_buffer = buffer_id[0]
            break
    if target_buffer:
        notepad.activateFile(target_buffer)
        if not is_manual: editor.setText(content)
    else:
        if is_manual and file_path and os.path.exists(file_path):
            notepad.open(file_path)
        else:
            notepad.new()
            editor.setText(content)
    editor.gotoPos(0)

def show_smart_help(query, calc_scope, mode='_help_'):
    import types
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    if mode == '_man_':
        path = os.path.join(script_dir, "npp_py_inline")
        if not os.path.exists(path):
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("=== МОЙ ИНЖЕНЕРНЫЙ СПРАВОЧНИК ===\n")
            except OSError as e:
                # Fallback: открытие буфера без привязки к диску при ошибке прав
                err_content = f"=== МОЙ ИНЖЕНЕРНЫЙ СПРАВОЧНИК ===\n# [ВНИМАНИЕ: Ошибка I/O, файл не сохранен на диск: {e}]\n"
                open_tab("npp_py_inline.txt", err_content, is_manual=False)
                return
        open_tab("npp_py_inline.txt", "", is_manual=True, file_path=path)
        return

    # --- НОВЫЙ БЛОК: РАЗРЕШЕНИЕ ПУТИ (sys.exit -> getattr) ---
    target = None
    parts = query.split('.')
    if parts[0] in calc_scope:
        target = calc_scope[parts[0]]
        for part in parts[1:]:
            try:
                target = getattr(target, part)
            except AttributeError:
                target = None
                break
    # -------------------------------------------------------

    if isinstance(target, types.ModuleType):
        content = [f"=== МОДУЛЬ: {query} ==="]
        for name in sorted(dir(target)):
            if not name.startswith("_"):
                try:
                    obj = getattr(target, name)
                    # Добавляем str(), чтобы обезопасить себя от дескрипторов
                    raw_doc = obj.__doc__ if obj.__doc__ is not None else "Нет описания"
                    doc = str(raw_doc).strip().split('\n')[0]
                    content.append(f"{name:20} | {doc}")
                except Exception:
                    # На случай, если getattr тоже выдаст ошибку на системном объекте
                    content.append(f"{name:20} | <ошибка доступа>")
        open_tab("SmartRef.txt", "\n".join(content))
        
    elif target is not None:
        # Теперь это сработает для sys.exit или math.cos
        doc = target.__doc__ or "Описание отсутствует."
        open_tab("SmartRef.txt", f"=== СПРАВКА: {query} ===\n\n{doc}")

    else:
        # Если ничего не нашли или query == 'all'
        content = ["=== ДОСТУПНЫЕ ФУНКЦИИ (Global/Math) ==="]
        for name in sorted(calc_scope.keys()):
            obj = calc_scope[name]
            if callable(obj) and not name.startswith("_"):
                doc = (obj.__doc__ or "No desc").split('\n')[0]
                content.append(f"{name:15} - {doc}")
        open_tab("SmartRef.txt", "\n".join(content))
        
# =====================================================================
# 2. ЯДРО ВЫЧИСЛЕНИЙ (MathEngine)
# =====================================================================
class MathEngine:
    """Изолирует математику, состояние переменных и буфер вывода таблиц."""
    def __init__(self):
        self.out_buffer = []
        self.scope = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}
        self.scope.update({
            "_digits_": 6, "_bitwise_": 0, "_clean_": 0, "_debug_": 0, 
            "operator": operator,  "out": self.out_text, "row": self.build_row,
            "__builtins__": __builtins__
        })

    def build_row(self, *args, w=15):
        """
        Печатает аргументы в виде ровных колонок.
        w - ширина колонки (число для всех одинаково, либо список чисел для каждой колонки)
        """
        # Если w - одно число, делаем из него список для всех аргументов
        if isinstance(w, int):
            widths = [w] * len(args)
        else:
            # Если передали список ширин, дополняем его дефолтными 15, если аргументов больше
            widths = list(w) + [15] * max(0, len(args) - len(w))
            
        # Склеиваем строку, выравнивая каждый аргумент по левому краю (<) на заданную ширину
        line = "".join(f"{str(arg):<{width}}" for arg, width in zip(args, widths))
        self.out_buffer.append(line)

        
    def out_text(self, *args):
        self.out_buffer.append(" ".join(map(str, args)))

    def evaluate(self, raw_formula):
        """Пытается вычислить выражение, обрабатывая возвратный парсинг (multiple =)."""
        test_expr = raw_formula
        if self.scope.get("_bitwise_", 0) == 1:
            for word, op in [('xor', '^'), ('and', '&'), ('or', '|')]:
                test_expr = re.sub(r'\b' + word + r'\b', op, test_expr, flags=re.IGNORECASE)
                
        try:
            return eval(test_expr, self.scope, self.scope), raw_formula
        except SyntaxError:
            matches = list(re.finditer(r'(?<![!<>=])=(?!=)', raw_formula))
            for m in reversed(matches):
                sub_expr = raw_formula[:m.start()].strip()
                try:
                    return eval(sub_expr, self.scope, self.scope), sub_expr
                except SyntaxError:
                    continue
            raise SyntaxError("Invalid syntax")

    def execute_assignment(self, var_part, result):
        """Безопасно сохраняет результат в память калькулятора."""
        self.scope["__sc_res__"] = result
        exec(f"{var_part} = __sc_res__", self.scope, self.scope)

    def execute_raw(self, raw_formula):
        """Выполняет код, который не возвращает результат (например, импорты)."""
        exec(raw_formula, self.scope, self.scope)


# =====================================================================
# 3. ПАРСЕР ТЕКСТА (CodeParser)
# =====================================================================
class CodeParser:
    """Отвечает исключительно за разбор строки на компоненты."""
    @staticmethod
    def parse(full_raw_line):
        line_to_process = full_raw_line.strip()
        if not line_to_process: return None

        # Отделяем комментарии
        if "#" in full_raw_line:
            code_part, comment_str = full_raw_line.split("#", 1)
            comment_str = " #" + comment_str
        else:
            code_part, comment_str = full_raw_line, ""

        code_part = re.sub(r'\s*!! ERROR:.*', '', code_part).strip()
        if not code_part: return None

        # Ищем инспектор (?)
        insp_match = re.search(r'\?([a-zA-Z]*(?:\.\d+)?)', code_part)
        is_inspector = bool(insp_match)
        flag_str = insp_match.group(1).lower() if insp_match else ""
        core_line = code_part[:insp_match.start()].strip() if insp_match else code_part

        if not core_line: return None

        # Ищем присваивание (=)
        match = re.search(r'(?<![!<>=])=(?!=)', core_line)
        var_part = ""
        raw_formula = core_line

        if match:
            left_candidate = core_line[:match.start()].strip()
            try:
                compile(f"{left_candidate} = None", "<string>", "exec")
                var_part = left_candidate
                raw_formula = core_line[match.end():].strip()
            except SyntaxError:
                pass

        # Проверка на системные команды (help/man)
        cmd_parts = raw_formula.split()
        cmd = cmd_parts[0].lower() if cmd_parts else ""

        return {
            "code_part": code_part, "comment_str": comment_str,
            "is_inspector": is_inspector, "flag_str": flag_str,
            "core_line": core_line, "var_part": var_part, 
            "raw_formula": raw_formula, "cmd": cmd, "cmd_parts": cmd_parts
        }


# =====================================================================
# 4. ФОРМАТТЕР ВЫВОДА (ResultFormatter)
# =====================================================================
class ResultFormatter:
    """Отвечает за сборку финальной строки после вычислений."""
    @staticmethod
    def format(parsed, result, actual_formula, engine):
        flag_str = parsed["flag_str"]
        format_type = 'd'
        precision = int(engine.scope.get("_digits_", 6))
        clean_mode = engine.scope.get("_clean_", 0) == 1
        debug_mode = engine.scope.get("_debug_", 0) == 1
    
        if '.' in flag_str:
            m = re.search(r'\.(\d+)', flag_str)
            if m: precision = int(m.group(1))
        if 'h' in flag_str: format_type = 'h'
        elif 'b' in flag_str: format_type = 'b'

        # Форматирование значения
        if result is None: 
            res_str = ""
        elif isinstance(result, bool): 
            res_str = "True" if result else "False"
        elif format_type == 'h' and isinstance(result, int): 
            res_str = hex(result)
        elif format_type == 'b' and isinstance(result, int): 
            res_str = bin(result)
        elif isinstance(result, (int, float)):
            
            # === НАЧАЛО ИЗМЕНЕНИЙ ===
            # Проблема: float из целого числа выводится с .000000 (например, 5987654321.000000)
            # Решение: проверяем, является ли число целым (без значимой дробной части)
            
            def is_effectively_integer(value):
                """Проверяет, является ли число целым с учетом погрешности float"""
                if isinstance(value, int):
                    return True
                if isinstance(value, float):
                    # Используем round для учета погрешностей вычислений
                    # 1e-12 - допустимая погрешность для double
                    return abs(value - round(value)) < 1e-12
                return False
            
            # Если результат - целое число (int или float с .0), выводим без дробной части
            if is_effectively_integer(result):
                # Преобразуем в int через round для отсечения погрешности
                # round(5987654321.0) -> 5987654321
                res_str = str(int(round(result)))
            else:
                # Настоящий float с дробной частью - используем стандартное форматирование
                res_str = f"{result:.{precision}f}"
            # === КОНЕЦ ИЗМЕНЕНИЙ ===
            
        else: 
            res_str = str(result)

        # Сборка базового выражения
        base_expr = f"{parsed['var_part']} = {actual_formula}" if parsed['var_part'] else actual_formula

        # Применение режимов Clean и Debug
        if clean_mode:
            if parsed['is_inspector']: 
                return f"{base_expr} ?{flag_str}".strip()
            if parsed['var_part'].lower() == "_clean_": 
                return "_clean_ = 0"
            return base_expr
        else:
            if parsed['is_inspector']:
                return f"{base_expr} ?{flag_str} {res_str}".strip() if res_str else f"{base_expr} ?{flag_str}".strip()
            if debug_mode and res_str and str(result) != actual_formula.strip():
                return f"{base_expr} = {res_str}"
            return base_expr
            
# =====================================================================
# 5. ГЛАВНЫЙ ЦИКЛ (Notepad++ DOM)
# =====================================================================
def smart_calc_main():
    engine = MathEngine()
        
    cur_pos = editor.getCurrentPos()
    cur_line = editor.lineFromPosition(cur_pos)
    start_line, end_line = -1, -1
        
    # Поиск границ блока
    for l in range(cur_line, -1, -1):
        if re.search(r'\b_end_\b', editor.getLine(l).lower()) and l != cur_line: break 
        if re.search(r'\b_beg_\b', editor.getLine(l).lower()):
            start_line = l + 1
            break
            
    for l in range(cur_line, editor.getLineCount()):
        if re.search(r'\b_beg_\b', editor.getLine(l).lower()) and l != cur_line: break 
        if re.search(r'\b_end_\b', editor.getLine(l).lower()):
            end_line = l
            break

    if start_line == -1 or end_line == -1: return 

    # Проверка режима clean (pre-flight)
    for i in range(start_line, end_line):
        if i < editor.getLineCount() and "_clean_ = 1" in editor.getLine(i).lower().split('#')[0]:
            engine.scope["_clean_"] = 1
            break

    editor.beginUndoAction()
    try:
        in_multi_comment = False
        
        for i in range(start_line, end_line):
            if i >= editor.getLineCount(): break 
            
            full_raw_line = editor.getLine(i).rstrip('\r\n')
            
            # Обработка многострочных комментариев
            if '"""' in full_raw_line:
                if full_raw_line.count('"""') < 2: in_multi_comment = not in_multi_comment
                continue
            if in_multi_comment: continue

            parsed = CodeParser.parse(full_raw_line)
            if not parsed: continue

            # Системные команды
            if parsed["cmd"] in ['_help_', '_man_']:
                query = parsed["cmd_parts"][1].lower() if len(parsed["cmd_parts"]) > 1 else 'all'
                show_smart_help(query, engine.scope, mode=parsed["cmd"])
                continue 

            # Основной вычислительный процесс
            try:
                result, actual_formula = engine.evaluate(parsed["raw_formula"])
                
                if parsed["var_part"]:
                    engine.execute_assignment(parsed["var_part"], result)

                new_code = ResultFormatter.format(parsed, result, actual_formula, engine)
                
                editor.setSel(editor.positionFromLine(i), editor.getLineEndPosition(i))
                editor.replaceSel(new_code + parsed["comment_str"])

            except Exception as e:
                # Fallback для конструкций вроде import, print, list.append
                if not parsed["var_part"] and not parsed["is_inspector"]:
                     try:
                         engine.execute_raw(parsed["raw_formula"])
                         editor.setSel(editor.positionFromLine(i), editor.getLineEndPosition(i))
                         editor.replaceSel(parsed["core_line"] + parsed["comment_str"])
                         continue
                     except Exception as fallback_err: 
                         # Перезаписываем первоначальный SyntaxError реальной ошибкой выполнения
                         e = fallback_err 
                
                editor.setSel(editor.positionFromLine(i), editor.getLineEndPosition(i))
                editor.replaceSel(parsed["code_part"] + f" !! ERROR: {str(e)}" + parsed["comment_str"]) 
 
        # Smart Output: Вывод таблиц
        last_out_line = end_line
        while last_out_line + 1 < editor.getLineCount() and editor.getLine(last_out_line + 1).startswith("# >"):
            last_out_line += 1
            
        if not engine.scope.get("_clean_") == 1:
            for l in range(last_out_line, end_line, -1):
                editor.setTarget(editor.positionFromLine(l), editor.positionFromLine(l + 1))
                editor.replaceTarget("")
                
        if engine.out_buffer and not engine.scope.get("_clean_") == 1:
            if end_line >= editor.getLineCount() - 1: editor.appendText("\n")
            out_text = "".join([f"# > {line}\n" for line in "\n".join(engine.out_buffer).split('\n')])
            editor.insertText(editor.positionFromLine(end_line + 1), out_text)

    finally:
        editor.endUndoAction()

smart_calc_main()