
## NppPyInline: Calculator and Python right inside Notepad++
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Readme.ru](./Readme.ru.md)

**NppPyInline** is a Python runtime environment right inside Notepad++. You write code in the Notepad++ text editor between `_beg_` and `_end_` markers and run it with a single command. Calculation results appear on the same lines or at the end of the block.

This is not a replacement for a full-fledged IDE. It's a tool for quick scenarios where you don't want to switch to a console, open Jupyter Notebook, or write a separate `.py` file.

## When is it useful

- **Calculate something with intermediate variables** — a powerful calculator with memory
- **Quickly test a small piece of code** — without creating a separate file
- **Process data directly in a text file** — results appear right next to the source data
- **Rough out a prototype** — without leaving Notepad++

## What it looks like

**Example 1: Simple calculations**
Finding the hypotenuse of a right triangle and computing the sines of the angles.
```python
_beg_
a = 5
b = 50

# ? - print operator
c = (a**2 + b**2)**0.5 ?.4 50.2494

# out() outputs data as a single block after end
out("Hypotenuse = {:.2f}".format(c))

sin_a = a / c
out("sin_a = {:.5f}".format(sin_a))

sin_b = b / c
out("sin_b = {:.5f}".format(sin_b))
_end_
# > Hypotenuse = 50.25
# > sin_a = 0.09950
# > sin_b = 0.99504

```

## Documentation
A detailed description of all features is available in **[MANUAL.md](MANUAL.md)**

## Project Status
✅ All planned functionality has been implemented.  
🔧 The author fixes bugs but does not add new features.  
🤝 Pull Requests with reasonable enhancements are welcome.

## 📝 License
The project is distributed under the MIT License. See the LICENSE file for details. You are free to use, modify, and distribute this code.