
## NppPyInline: Python Inline Execution Environment for Notepad++
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**NppPyInline** is an embeddable tool that transforms the Notepad++ text editor into an inline calculation environment. It allows you to execute Python code directly inside the Scintilla text buffer with instant output and updating of results on the same lines or in a specifically designated area.

You write code directly in the text, run the script, and get the calculation result. If you fix an error or change the initial data — restart the script, and the results are updated. Unlike a standard console, the code is typed once, saved in a file, and you can work with it for as long as needed.

---

## 🚀 Quick Start (How it works)

Each calculation block is enclosed by the keywords `_beg_` and `_end_`. The result can be output directly on the line using the `?` operator or grouped at the end using `out()`.

**Example 1: Simple calculations**
Finding the hypotenuse of a right triangle and calculating the sines of the angles.
```python
_beg_
a = 5
b = 50

# ?.4 - print operator (rounding to 4 decimal places)
c = (a**2 + b**2)**0.5 ?.4 50.2494

# out() outputs data as a single block after end
# out(f"Hypotenuse = {c:.2f}")         # Only for Python 3
out("Hypotenuse = {:.2f}".format(c))

sin_a = a / c
# out(f"sin_a = {sin_a:.5f}")          # Only for Python 3
out("sin_a = {:.5f}".format(sin_a))

sin_b = b / c
# out(f"sin_b = {sin_b:.5f}")          # Only for Python 3
out("sin_b = {:.5f}".format(sin_b))
_end_
# > Hypotenuse = 50.25
# > sin_a = 0.09950
# > sin_b = 0.99504

```

**Example 2: Working with collections and modules**
Element-wise multiplication of randomly generated lists.

```python
_beg_
import random

my_tuple = tuple(random.randint(1, 10) for _ in range(10))
my_list = [random.randint(1, 10) for _ in range(10)]
result = [my_tuple[i] * my_list[i] for i in range(10)]

# Defining a single-line function
def get_stats(data): return min(data), max(data), sum(data) / float(len(data))

result_min, result_max, result_mean = get_stats(result)
out("RESULT: min={}, max={}, mean={:.2f}".format(result_min, result_max, result_mean))
_end_
# > RESULT: min=4, max=72, mean=41.40

```

> 💡 **More examples:** Over 60 examples of using various aspects of the environment are collected in the files `examples2.md` (for Python 2) and `examples3.md` (for Python 3). Most examples are identical for both versions.

---
## 📥 Installation and Launch

**System requirements:**
* **Notepad++** editor (tested on version 8.9.3 64-bit).
* **PythonScript** plugin. NppPyInline is versatile and supports both plugin versions (Python 3.14+) and (Python 2.7+) - as two separate scripts.

**Installation steps:**

1. Install the Python Script plugin via the Notepad++ plugin manager: Plugins → Plugins Admin... Find PythonScript in the list and install it.
2. Upon first use, the PythonScript plugin does not always automatically create the necessary `scripts` folder. Therefore, do the following:
* For a standard Notepad++ installation: scripts should be placed in `%APPDATA%\Notepad++\plugins\config\PythonScript\scripts`
* For a Portable Notepad++ version: scripts should be placed in `(notepad++.exe folder)\plugins\config\PythonScript\scripts`
* If the `PythonScript\scripts` folder doesn't exist — create it manually. Place the script file (e.g., `npp_py_inline2.py`) into the `scripts` directory.
3. Go to the main menu: Plugins → Python Script → Configuration... Add your downloaded script from the User Scripts section to the Menu items section. Restart Notepad++.
4. Assign a shortcut key to run the script. To do this, go to the main menu: Settings → Shortcut Mapper... → Plugin commands. Usually, you will find your script closer to the end of the table. Set a convenient key combination for it.

**How to find your Python version in Notepad++?** In the main menu, select **Plugins** -> **Python Script** -> **Show Console**. The exact interpreter version (e.g., *Python 3.14.3* or *Python 2.7.18*) will be indicated in the very first line of the console that opens at the bottom.

**How to use:**
1. Write code between `_beg_` and `_end_` in any text file.
2. Place the cursor on any line inside this block.
3. Execute the script.

---

## ⚙️ Technical Description and Architecture

**NppPyInline** operates on top of the Scintilla text buffer (in Notepad++) and uses built-in Python functions (`eval` and `exec`). Math, variables, and data types work exactly the same as in standard Python.

However, **NppPyInline is not a full-fledged Python interpreter**. Its architecture is based on **strict line-by-line execution**. The main loop takes one line, passes it to the parser, then to the evaluator and formatter. This results in strict environment limitations.

### 🚫 Limitations (What you cannot do)

1. **No multi-line control structures:** Classic `if/elif/else`, `for`, `while` spanning multiple lines are not supported.
2. **No multi-line function/class declarations:** Block `def` and `class` statements are not allowed.
3. **No standard I/O:** The `print()` and `input()` functions are disabled, as the environment has no console — the text itself is the interface.

*Valid alternatives:*

* Instead of a block `if`, use a ternary operator or a single-line statement: `if x > 0: y = 10`.
* Instead of block `def`, use `lambda` or single-line functions: `def func(x,y): return (x**2 + y**2)`.

### 🛡️ Code Block Isolation

Code blocks enclosed between `_beg_` and `_end_` are **completely independent**. With each new run of a block, its environment (variable state) is created from scratch, and upon completion of execution — destroyed. Data from one block is inaccessible in another.

---

## 🛠 Output Tools

### Operator (`?`)

Prints the calculation result directly on the code line. It has modification flags:

* `?` — basic output: `x = 10 / 3 ? 3.333333333`
* `?.N` — rounding to N decimal places: `pi_val = math.pi ?.2 3.14`
* `?h` — HEX format output: `mask = 255 ?h 0xff`
* `?b` — binary format output: `flags = 5 ?b 0b101`

### Block Output (`out` and `row`)

Generates output at the very end of the block (after `_end_`).

* `out(*args)` — analogue of `print()`. Concatenates arguments with a space.
* `row(title, *rows)` — generates a neat ASCII table. Takes a title and iterables (minimum 2 elements).

When the script is run again, old results are automatically deleted, and new ones are written in their place. Syntax or runtime errors are printed directly on the problematic line and are also deleted after correction.

---

## 🎛 System Variables (Modes)

You can control NppPyInline's behavior by declaring special variables inside the `_beg_ ... _end_` block. Modes apply **only locally** within a specific block.

* `_digits_ = N` — sets the global number of decimal places for the current calculation block (default is 10).
* `_clean_ = 1` — forcibly deletes all previously printed results of the current block. (Error messages remain until they are resolved).
* `_debug_ = 1` — enables debugging mode. The results of all operations are printed forcibly, even if the `?` operator is not set.
* `_bitwise_ = 1` — **Warning: alters standard Python syntax!** Logical operators `and` and `or` are replaced by bitwise `&` and `|`. The keyword `xor` also becomes available. The mode is enabled locally only by explicit user request.

---

## 📚 Built-in Help System

The `_math_` library is loaded into the environment automatically.

* Calling `_help_` (or `_help_ all`) will open a new tab in Notepad++ with a list of all functions in the `math` library.
* Calling `_help_ <function_name>` (e.g., `_help_ sin`) will extract `__doc__` and output detailed documentation for the specific object.
* The keyword `_man_` on an empty line will automatically open or create the `npp_py_inline.txt` file in an adjacent tab — this is your personal cheat sheet for notes.

---

## 📝 License

The project is distributed under the MIT License. See the [LICENSE](./LICENSE) file for details. You are free to use, modify, and distribute this code.

---

## 🔗 Useful Links

- [Script for Python 3](npp_py_inline3.py)
- [Script for Python 2](npp_py_inline2.py)
- [Examples for Python 3](examples3.md)
- [Examples for Python 2](examples2.md)
- [Demonstration](npp_py_inline.gif)
- [Russian version of README](README.ru.md)
