# Bisection Method Root Finder
### Numerical Analysis — v1.0

A desktop application for finding roots of mathematical functions using two bracketing methods: **Bisection** and **False Position (Regula Falsi)**. The app features a step-by-step Solution Trail that streams the algorithm's reasoning in real time, an interactive graph, and a full iteration table.

---

## Group Members

- John Oniel Thomas Q. Araque
- Niel Allen S. Jauculan
- Tiff Anthony R. Parnala

---

## How to Run the System

### Step 1 — Install Python
Download and install **Python 3.9 or higher** from https://www.python.org/downloads/

Make sure to check **"Add Python to PATH"** during installation.

Verify installation by opening a terminal and running:
```
python --version
```

### Step 2 — Download the Project
Download or clone the project folder. Your folder should contain:
```
bisection_method.py
README.md
TEST_PLAN.md
requirements.txt
```

### Step 3 — Install Dependencies
Open a terminal inside the project folder and run:
```
pip install -r requirements.txt
```

This installs all required libraries automatically.

### Step 4 — Run the Program
```
python bisection_method.py
```

The application window will open immediately.

---

## How to Use

1. **Select a Method** — Choose between Bisection or False Position using the radio buttons at the top of the left panel.
2. **Enter Your Function** — Type a mathematical function using `x` as the variable (e.g. `x**3 - x - 2`).
3. **Set the Interval** — Enter values for `a` (left endpoint) and `b` (right endpoint). `f(a)` and `f(b)` must have opposite signs.
4. **Configure Settings** — Set the tolerance (precision) and max iterations.
5. **Click COMPUTE ROOT** — Or press `Enter`.
6. **View Results** in the three output tabs:
   - **Summary** — Final root, error bound, convergence status
   - **Solution Trail** — Step-by-step reasoning streamed line by line
   - **Iteration Table** — Full table of all iterations
   - **Graph** — Visual plot of the function with root marker

You can also press `Esc` to clear all fields, or click any **Test Case** button to load a pre-built example.

---

## Features

- **Two numerical methods** — Bisection and False Position (Regula Falsi)
- **Method selector** — Radio-button UI to switch methods instantly
- **Solution Trail** — Streams the algorithm's reasoning line-by-line like a live explanation
- **Method identification** — Trail clearly shows which method was used at the top
- **Three stopping rules** — |f(c)| < tolerance, bracket width < tolerance, max iterations cap
- **Interactive graph** — Dark-themed matplotlib plot with convergence bracket shading and root marker
- **Iteration table** — Full table with columns for a, b, midpoint c, f(a), f(b), f(c), width, decision
- **5 built-in test cases** — Load pre-configured examples instantly
- **Input validation** — Clear error messages for invalid function, interval, or settings
- **Keyboard shortcuts** — `Enter` to compute, `Esc` to clear
- **Toast notifications** — Pop-up confirmation when computation finishes
- **White input boxes** — High-contrast input fields with black text for readability
- **3D animated buttons** — Press animation on all buttons

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| Python | 3.9+ | Programming language |
| ttkbootstrap | 1.10+ | Modern themed UI widgets |
| numpy | 1.21+ | Numerical computations and array operations |
| matplotlib | 3.5+ | Interactive graph plotting |
| tkinter | built-in | Base GUI framework |

---

## Requirements File (requirements.txt)

```
ttkbootstrap>=1.10.0
numpy>=1.21.0
matplotlib>=3.5.0
```

---

## Supported Operators and Functions

| Input | Meaning |
|---|---|
| `x**2` | x squared |
| `x**3` | x cubed |
| `*` | multiply |
| `/` | divide |
| `+` `-` | add / subtract |
| `sin(x)` | sine |
| `cos(x)` | cosine |
| `tan(x)` | tangent |
| `exp(x)` | e^x |
| `log(x)` | natural log |
| `log10(x)` | log base 10 |
| `sqrt(x)` | square root |
| `pi` | π ≈ 3.14159 |
| `e` | e ≈ 2.71828 |

---

## Software Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **Screen Resolution**: 1100 × 700 minimum (1400 × 860 recommended)
- **RAM**: 256 MB minimum

---

*Bisection Method Root Finder — Numerical Analysis Project — v1.0*
