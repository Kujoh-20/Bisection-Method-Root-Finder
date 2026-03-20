import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.toast import ToastNotification
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


# ── Colours ──────────────────────────────────
BG        = "#12121e"
CARD_BG   = "#1c1c2e"
INPUT_BG  = "#ffffff"
INPUT_FG  = "#000000"
INPUT_TOP = "#d0d8e8"
INPUT_BOT = "#a0b0c8"
ACCENT1   = "#4fc3f7"
ACCENT2   = "#ffd54f"
ACCENT3   = "#69f0ae"
TEXT_FG   = "#e8eaf6"
MUTED     = "#7986cb"

# 3-D button palette
BTN_GREEN_TOP = "#2ecc71"
BTN_GREEN_MID = "#27ae60"
BTN_GREEN_BOT = "#1a7a43"
BTN_RED_TOP   = "#e74c3c"
BTN_RED_MID   = "#c0392b"
BTN_RED_BOT   = "#922b21"
BTN_EX_TOP    = "#3d3d6b"
BTN_EX_MID    = "#2e2e55"
BTN_EX_BOT    = "#1a1a38"

# ── Safe evaluator ───────────────────────────
SAFE_NS = {
    "x": None, "np": np,
    "sin": np.sin,  "cos": np.cos,  "tan": np.tan,
    "exp": np.exp,  "log": np.log,  "log10": np.log10,
    "sqrt": np.sqrt,"abs": np.abs,  "pi": np.pi, "e": np.e,
}
def make_f(expr):
    def f(x):
        ns = SAFE_NS.copy(); ns["x"] = x
        return eval(expr, {"__builtins__": {}}, ns)
    return f

# ── Bisection ────────────────────────────────
def bisection(f, a, b, tol, max_iter):
    history, brackets = [], []
    ca, cb = a, b
    stop_reason = "max_iter"   # default: ran out of iterations
    for i in range(1, max_iter + 1):
        fa, fb = float(f(ca)), float(f(cb))
        c  = (ca + cb) / 2.0
        fc = float(f(c))
        w  = cb - ca
        dec = "Left  [a->c]" if fa * fc < 0 else "Right [c->b]"
        brackets.append((ca, cb))
        history.append((i, ca, cb, fa, fb, c, fc, w, dec))
        if abs(fc) < tol:
            stop_reason = "f(c)_tol"   # |f(c)| < tolerance
            break
        if w / 2 < tol:
            stop_reason = "bracket_tol"  # bracket width < tolerance
            break
        if fa * fc < 0:
            cb = c
        else:
            ca = c
    return c, history, brackets, stop_reason

# ── Graph ────────────────────────────────────
def plot_graph(expr, root_val, brackets):
    for w in graph_frame.winfo_children():
        w.destroy()
    f = make_f(expr)
    span = max(10.0, abs(root_val) * 2.5)
    x = np.linspace(root_val - span/2, root_val + span/2, 900)
    try:
        raw = f(x)
        y = np.where(np.isfinite(raw), raw, np.nan)
    except Exception:
        y = np.full_like(x, np.nan)

    fig = Figure(figsize=(5, 4), dpi=100, facecolor=BG)
    ax  = fig.add_subplot(111, facecolor=BG)
    for sp in ax.spines.values():
        sp.set_edgecolor("#2a2a4a")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_xlabel("x",    color=MUTED, fontsize=10)
    ax.set_ylabel("f(x)", color=MUTED, fontsize=10)
    ax.set_title(f"f(x) = {expr}", color=TEXT_FG, fontsize=11, pad=8)
    ax.grid(True, alpha=0.12, color="#444488")
    ax.axhline(0, color="#444466", linewidth=0.8)
    ax.axvline(0, color="#444466", linewidth=0.8)
    ax.plot(x, y, color=ACCENT1, linewidth=2.2, label="f(x)", zorder=3)
    for i, (ia, ib) in enumerate(brackets[-8:]):
        ax.axvspan(ia, ib, alpha=0.03 + i*0.012, color=ACCENT2, zorder=1)
    try:
        ry = float(f(root_val))
    except Exception:
        ry = 0.0
    ax.axvline(root_val, color="#ef5350", linestyle="--", linewidth=1.5,
               label=f"Root = {root_val:.8f}", zorder=4)
    ax.plot(root_val, ry, "o", color="#ef5350", markersize=10,
            markeredgecolor="#fff", markeredgewidth=1.5, zorder=5)
    ax.legend(facecolor=CARD_BG, edgecolor="#2a2a4a",
              labelcolor=TEXT_FG, fontsize=9, loc="best")
    fig.tight_layout(pad=1.0)
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    tb = NavigationToolbar2Tk(canvas, graph_frame, pack_toolbar=False)
    tb.update()
    tb.pack(side=BOTTOM, fill=X)
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

# ── Solution Trail ────────────────────────────
TRAIL_HEADER  = "#4fc3f7"
TRAIL_LABEL   = "#c792ea"
TRAIL_VALUE   = "#ffffff"
TRAIL_EXPLAIN = "#ffe082"
TRAIL_GOOD    = "#69f0ae"
TRAIL_WARN    = "#ff7043"
TRAIL_DIM     = "#546e7a"

def build_trail_segments(f_expr, a, b, tol, max_iter, history, root_val, stop_reason="f(c)_tol"):
    f = make_f(f_expr)
    fa0, fb0 = float(f(a)), float(f(b))
    segs = []

    def h(t):    segs.append((t + "\n", "header"))
    def lv(label, val):
        segs.append((f"  {label}", "label"))
        segs.append((f"  {val}\n", "value"))
    def p(t):    segs.append(("  " + t + "\n", "explain"))
    def good(t): segs.append(("  " + t + "\n", "good"))
    def warn(t): segs.append(("  " + t + "\n", "warn"))
    def sep():   segs.append(("  " + "-" * 52 + "\n", "dim"))
    def blank(): segs.append(("\n", "explain"))

    h("=" * 56)
    h("  SOLUTION TRAIL  -  BISECTION METHOD")
    h("=" * 56)
    blank()

    h("  PROBLEM SETUP")
    sep()
    lv("Function  :", f"f(x) = {f_expr}")
    lv("Interval  :", f"a = {a},   b = {b}")
    lv("Tolerance :", str(tol))
    lv("Max Iters :", str(max_iter))
    blank()

    h("  STOPPING / COMPLETION RULES")
    sep()
    p("The bisection loop will stop as soon as ANY of these rules fires:")
    blank()
    lv("  Rule 1 — Tolerance on f(c) :",
       f"|f(c)| < {tol}  (midpoint value is close enough to zero)")
    p("    If the function value at the midpoint is smaller than the")
    p("    tolerance, the root is found with sufficient precision.")
    blank()
    lv("  Rule 2 — Tolerance on bracket :",
       f"(b-a)/2 < {tol}  (bracket is too narrow to matter)")
    p("    If the half-width of the current bracket falls below the")
    p("    tolerance, we cannot narrow it further meaningfully.")
    blank()
    lv("  Rule 3 — Max iterations :",
       f"i > {max_iter}  (safety cap to prevent infinite loops)")
    p("    If neither tolerance rule fires within the allowed number")
    p("    of iterations, the loop stops and we report the best")
    p("    midpoint found so far.")
    blank()
    # ── Which rule actually fired? ──
    if stop_reason == "f(c)_tol":
        good("  ACTIVE THIS RUN  ->  Rule 1  (|f(c)| < tolerance)")
    elif stop_reason == "bracket_tol":
        good("  ACTIVE THIS RUN  ->  Rule 2  (bracket width < tolerance)")
    else:
        warn(f"  ACTIVE THIS RUN  ->  Rule 3  (hit max iterations = {max_iter})")
    blank()

    h("  STEP 0 - VALIDITY CHECK  (Intermediate Value Theorem)")
    sep()
    p("Before we can bisect, we must confirm f(a) and f(b)")
    p("have OPPOSITE signs. If one is negative and one positive,")
    p("the function must cross zero somewhere between them.")
    blank()
    lv(f"f(a) = f({a})  =", f"{fa0:.8f}  ({'negative' if fa0 < 0 else 'positive'})")
    lv(f"f(b) = f({b})  =", f"{fb0:.8f}  ({'negative' if fb0 < 0 else 'positive'})")
    lv("f(a) x f(b)   =", f"{fa0 * fb0:.6f}")
    blank()
    if fa0 * fb0 < 0:
        good("OK  Opposite signs confirmed - safe to proceed!")
    else:
        warn("X  Same sign - bisection cannot be applied here.")
    blank()

    h("  ITERATION-BY-ITERATION TRAIL")
    sep()
    blank()

    for (i, ia, ib, fa, fb, ic, fc, w, dec) in history:
        h(f"  [ ITERATION {i} ]")
        lv("  Current bracket :", f"[ {ia:.8f},  {ib:.8f} ]")
        lv("  Bracket width   :", f"{w:.8f}")
        blank()
        p("We split the bracket in half to find the midpoint c:")
        lv("  c = (a + b) / 2", "")
        lv(f"    = ({ia:.6f} + {ib:.6f}) / 2", "")
        lv("    =", f"{ic:.10f}")
        blank()
        p("Now evaluate the function at the midpoint:")
        lv(f"  f(c) = f({ic:.8f})", "")
        lv("       =", f"{fc:.10f}")
        blank()
        p("Check stopping condition:")
        if abs(fc) < tol:
            lv("  |f(c)| =", f"{abs(fc):.3e}")
            lv("  tol    =", f"{tol}")
            good(f"  {abs(fc):.3e}  <  {tol}  - f(c) is close enough to zero!")
            good("  ROOT FOUND - stopping here.")
        elif w / 2 < tol:
            lv("  bracket/2 =", f"{w/2:.3e}")
            lv("  tol       =", f"{tol}")
            good(f"  {w/2:.3e}  <  {tol}  - bracket is tiny enough!")
            good("  ROOT FOUND - stopping here.")
        else:
            lv("  |f(c)| =", f"{abs(fc):.3e}  (still above tol {tol})")
            p("  Not precise enough yet - keep narrowing.")
        blank()
        p("Which half contains the root?")
        lv("  f(a) x f(c) =", f"{fa:.6f} x {fc:.6f} = {fa*fc:.8f}")
        if fa * fc < 0:
            good("  Product is NEGATIVE - root is in the LEFT half [ a, c ]")
            lv("  New bracket:", f"b = c  ->  [ {ia:.7f},  {ic:.7f} ]")
        else:
            good("  Product is POSITIVE - root is in the RIGHT half [ c, b ]")
            lv("  New bracket:", f"a = c  ->  [ {ic:.7f},  {ib:.7f} ]")
        blank()
        sep()
        blank()

    f_root = float(f(root_val))
    n = len(history)
    err_b = (b - a) / (2 ** n)

    h("  FINAL ANSWER")
    sep()
    blank()
    lv("  Root            ~", f"{root_val:.12f}")
    lv("  f(root)          =", f"{f_root:.6e}")
    lv("  Total iterations =", str(n))
    lv("  Error bound      =", f"(b-a) / 2^{n}  =  {err_b:.4e}")
    blank()
    # ── Completion / stopping explanation ──
    h("  WHY THE PROCESS STOPPED")
    sep()
    if stop_reason == "f(c)_tol":
        good(f"  Rule 1 fired — |f(c)| < {tol}")
        p (  "  The function value at the midpoint became smaller than")
        p (  "  the tolerance, confirming the root with full precision.")
        good("  STATUS: CONVERGED  (exact-form tolerance reached)")
    elif stop_reason == "bracket_tol":
        good(f"  Rule 2 fired — bracket half-width < {tol}")
        p (  "  The interval shrank so small that both halves are")
        p (  "  indistinguishable within the required precision.")
        good("  STATUS: CONVERGED  (bracket tolerance reached)")
    else:
        warn(f"  Rule 3 fired — reached max iterations ({max_iter})")
        warn(  "  Neither tolerance rule triggered within the limit.")
        p (  "  The answer above is the best midpoint found so far.")
        warn("  STATUS: INCOMPLETE  (consider a tighter interval or")
        warn("          higher max iterations for better accuracy)")
    blank()
    p("Each iteration cuts the search bracket exactly in half.")
    p(f"After {n} steps, the bracket shrank from width {b-a}")
    p(f"down to just {err_b:.4e} - so the true root is within")
    p(f"{err_b:.4e} of our answer.")
    blank()
    h("=" * 56)
    blank()

    return segs


def stream_trail(segs, widget, delay_ms=55):
    widget.config(state=NORMAL)
    def _write(idx):
        if idx >= len(segs):
            widget.config(state=DISABLED)
            return
        text, tag = segs[idx]
        widget.insert(END, text, tag)
        widget.see(END)
        widget.after(delay_ms, _write, idx + 1)
    _write(0)


# ── Compute ──────────────────────────────────
def compute():
    for tb in [steps_text, results_text]:
        tb.config(state=NORMAL)
        tb.delete(1.0, END)
    for row in iter_tree.get_children():
        iter_tree.delete(row)

    f_expr   = entry_function.get().strip()
    a_str    = entry_a.get().strip()
    b_str    = entry_b.get().strip()
    tol_str  = entry_tol.get().strip()
    iter_str = entry_iter.get().strip()

    errors = []
    if not f_expr:
        errors.append("- Function f(x) is required.")
    a = b = tol = None
    max_iter = 100
    try:    a = float(a_str)
    except: errors.append("- Left endpoint (a) must be a number.")
    try:    b = float(b_str)
    except: errors.append("- Right endpoint (b) must be a number.")
    try:
        tol = float(tol_str)
        if tol <= 0: errors.append("- Tolerance must be positive.")
    except: errors.append("- Tolerance must be a number.")
    try:
        max_iter = int(iter_str)
        if max_iter <= 0: errors.append("- Max iterations must be a positive integer.")
    except: errors.append("- Max iterations must be an integer.")

    if errors:
        messagebox.showerror("Input Error", "\n".join(errors))
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return
    if a >= b:
        messagebox.showerror("Input Error", "a must be less than b.")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return
    try:
        f = make_f(f_expr)
        fa, fb = float(f(a)), float(f(b))
    except Exception as exc:
        messagebox.showerror("Function Error", f"Cannot evaluate f(x):\n{exc}")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return
    if fa * fb > 0:
        messagebox.showerror("Bisection Error",
            f"f({a}) = {fa:.4f} and f({b}) = {fb:.4f} have the SAME sign.\n"
            "Choose a different interval where f(a) and f(b) have opposite signs.")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return

    try:
        root_val, history, brackets, stop_reason = bisection(f, a, b, tol, max_iter)
    except Exception as exc:
        messagebox.showerror("Computation Error", str(exc))
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return

    n = len(history)
    f_root = float(f(root_val))

    # ── Stopping rule label for Summary tab ──
    if stop_reason == "f(c)_tol":
        stop_label = f"Yes  (Rule 1: |f(c)| < {tol})"
    elif stop_reason == "bracket_tol":
        stop_label = f"Yes  (Rule 2: bracket/2 < {tol})"
    else:
        stop_label = f"No   (Rule 3: hit max iter = {max_iter})"

    results_text.insert(END,
        f"{'='*46}\n"
        f"  BISECTION RESULT\n"
        f"{'='*46}\n\n"
        f"  f(x)          =  {f_expr}\n"
        f"  Interval      =  [{a}, {b}]\n"
        f"  Tolerance     =  {tol}\n"
        f"  Max Iterations=  {max_iter}\n\n"
        f"  {'-'*40}\n"
        f"  STOPPING RULES:\n"
        f"    Rule 1: |f(c)| < {tol}          (function value)\n"
        f"    Rule 2: (b-a)/2 < {tol}         (bracket width)\n"
        f"    Rule 3: iterations >= {max_iter}  (safety cap)\n\n"
        f"  {'-'*40}\n"
        f"  Root          ~  {root_val:.10f}\n"
        f"  f(root)       =  {f_root:.4e}\n"
        f"  Iterations    =  {n}\n"
        f"  Error Bound   =  {(b-a)/(2**n):.2e}\n"
        f"  Converged     =  {stop_label}\n"
        f"  {'-'*40}\n\n"
        f"  Done!\n"
    )
    results_text.config(state=DISABLED)

    steps_text.config(state=NORMAL)
    steps_text.delete(1.0, END)
    trail_segs = build_trail_segments(f_expr, a, b, tol, max_iter, history, root_val, stop_reason)
    stream_trail(trail_segs, steps_text, delay_ms=55)

    for (i, ia, ib, fa_i, fb_i, ic, fc, w, dec) in history:
        tag = "odd" if i % 2 == 0 else "even"
        iter_tree.insert("", END, values=(
            i, f"{ia:.7f}", f"{ib:.7f}", f"{ic:.9f}",
            f"{fa_i:.5f}", f"{fb_i:.5f}", f"{fc:.5e}",
            f"{w:.5e}", dec
        ), tags=(tag,))

    plot_graph(f_expr, root_val, brackets)
    notebook.select(1)
    update_status(f"Root = {root_val:.8f}  |  {n} iterations  |  Ready")
    ToastNotification(title="Done!",
        message=f"Root = {root_val:.8f}",
        duration=3000, bootstyle=SUCCESS).show_toast()


# ── Clear ────────────────────────────────────
def clear_all():
    for tb in [results_text]:
        tb.config(state=NORMAL); tb.delete(1.0, END); tb.config(state=DISABLED)
    steps_text.config(state=NORMAL)
    steps_text.delete(1.0, END)
    steps_text.insert(END,
        "The Solution Trail will appear here after you click COMPUTE ROOT.\n\n"
        "It will stream line-by-line, showing exactly how the algorithm\n"
        "reasons through every iteration - like watching it think.\n",
        "explain")
    steps_text.config(state=DISABLED)
    for row in iter_tree.get_children():
        iter_tree.delete(row)
    for entry, val in zip(
        [entry_function, entry_a, entry_b, entry_tol, entry_iter],
        ["x**3 - x - 2", "1", "2", "1e-6", "100"]
    ):
        entry.delete(0, END); entry.insert(0, val)
    for w in graph_frame.winfo_children():
        w.destroy()
    tk.Label(graph_frame, text="Graph appears after computation",
             bg=BG, fg=MUTED, font=("Segoe UI", 12)
             ).place(relx=0.5, rely=0.5, anchor="center")
    notebook.select(0)
    update_status("Ready")

def update_status(text):
    status_label.config(text=f"  {text}")
    root.update_idletasks()

def compute_with_status():
    btn_compute.config_btn(state=DISABLED, text="  Computing...  ")
    update_status("Computing... please wait")
    root.update_idletasks()
    try:
        compute()
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
        update_status("Error - check inputs")
    finally:
        btn_compute.config_btn(state=NORMAL, text="  COMPUTE ROOT  ")

def load_example(expr, a, b):
    entry_function.delete(0, END); entry_function.insert(0, expr)
    entry_a.delete(0, END);        entry_a.insert(0, a)
    entry_b.delete(0, END);        entry_b.insert(0, b)


# ════════════════════════════════════════════
#  WINDOW
# ════════════════════════════════════════════
root = ttkb.Window(themename="superhero",
                   title="Bisection Method Root Finder",
                   size=(1400, 860))
root.minsize(1100, 700)
root.configure(bg=BG)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# ── Header ───────────────────────────────────
hdr = tk.Frame(root, bg="#0a0a18", height=58)
hdr.grid(row=0, column=0, sticky="ew")
hdr.grid_propagate(False)
hdr.grid_columnconfigure(0, weight=1)
tk.Label(hdr, text="Bisection Method Root Finder",
         bg="#0a0a18", fg=ACCENT1,
         font=("Segoe UI", 19, "bold"),
         anchor="center").grid(row=0, column=0, sticky="ew", pady=14)
tk.Label(hdr, text="Enter = Compute    Esc = Clear  ",
         bg="#0a0a18", fg="#44446a",
         font=("Segoe UI", 9)).place(relx=1.0, rely=0.5, anchor="e", x=-10)

# ── Two-column master layout ──────────────────
master = tk.Frame(root, bg=BG)
master.grid(row=1, column=0, sticky="nsew")
master.grid_rowconfigure(0, weight=1)
master.grid_columnconfigure(0, weight=0)
master.grid_columnconfigure(1, weight=1)

sep = tk.Frame(master, bg="#2a2a4a", width=2)
sep.grid(row=0, column=0, sticky="ns", padx=(340,0))

# ════════════════════════════════════════════
#  LEFT — INPUT PANEL
# ════════════════════════════════════════════
left = tk.Frame(master, bg=CARD_BG, width=340)
left.grid(row=0, column=0, sticky="nsew")
left.grid_propagate(False)
left.grid_columnconfigure(0, weight=1)

canvas_scroll = tk.Canvas(left, bg=CARD_BG, bd=0, highlightthickness=0, width=320)
scroll_bar = tk.Scrollbar(left, orient=VERTICAL, command=canvas_scroll.yview)
canvas_scroll.configure(yscrollcommand=scroll_bar.set)
scroll_bar.pack(side=RIGHT, fill=Y)
canvas_scroll.pack(side=LEFT, fill=BOTH, expand=True)

scroll_inner = tk.Frame(canvas_scroll, bg=CARD_BG)
canvas_scroll.create_window((0, 0), window=scroll_inner, anchor="nw", width=320)

def _on_configure(e):
    canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
scroll_inner.bind("<Configure>", _on_configure)

def _on_mousewheel(e):
    canvas_scroll.yview_scroll(int(-1*(e.delta/120)), "units")
canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)

# ── Section title helper ──
def section_title(parent, text, fg=ACCENT1):
    f = tk.Frame(parent, bg=CARD_BG)
    f.pack(fill=X, padx=16, pady=(18, 4))
    tk.Label(f, text=text, bg=CARD_BG, fg=fg,
             font=("Segoe UI", 11, "bold")).pack(side=LEFT)
    tk.Frame(f, bg=fg, height=2).pack(side=LEFT, fill=X, expand=True, padx=(8,0), pady=6)

# ── Field helper ──
def field(parent, label, default, tip="", white_bg=False):
    area_bg  = "#ffffff" if white_bg else CARD_BG
    label_fg = "#000000" if white_bg else TEXT_FG
    tip_fg   = "#555555" if white_bg else MUTED

    wrap = tk.Frame(parent, bg=area_bg)
    wrap.pack(fill=X, padx=16, pady=6)

    tk.Label(wrap, text=label, bg=area_bg, fg=label_fg,
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    if tip:
        tk.Label(wrap, text=tip, bg=area_bg, fg=tip_fg,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 3))

    border = tk.Frame(wrap, bg="#b0bec5", padx=2, pady=2)
    border.pack(fill=X)

    e = tk.Entry(border,
                 font=("Consolas", 13),
                 bg="#ffffff",
                 fg="#000000",
                 insertbackground="#000000",
                 selectbackground="#4fc3f7",
                 selectforeground="#000000",
                 relief="flat", bd=0,
                 highlightthickness=0)
    e.pack(fill=X, ipady=10, padx=4, pady=4)
    e.insert(0, default)

    def on_focus_in(evt):  border.config(bg=ACCENT1)
    def on_focus_out(evt): border.config(bg="#b0bec5")
    e.bind("<FocusIn>",  on_focus_in)
    e.bind("<FocusOut>", on_focus_out)
    return e

# ─── inputs ───
section_title(scroll_inner, "ENTER YOUR FUNCTION", ACCENT1)
entry_function = field(scroll_inner, "f(x)  - the equation to solve",
                       "x**3 - x - 2",
                       "Operators: **  *  /  +  -   |  Functions: sin cos exp log sqrt",
                       white_bg=True)

section_title(scroll_inner, "SEARCH INTERVAL  [a, b]", ACCENT2)
tk.Label(scroll_inner,
    text="  f(a) and f(b) must have OPPOSITE signs\n"
         "  (one negative, one positive)",
    bg=CARD_BG, fg=MUTED, font=("Segoe UI", 9), justify=LEFT
).pack(anchor="w", padx=16, pady=(0,4))
entry_a = field(scroll_inner, "a  (left endpoint)",  "1")
entry_b = field(scroll_inner, "b  (right endpoint)", "2")

section_title(scroll_inner, "SETTINGS", ACCENT3)
entry_tol  = field(scroll_inner, "Tolerance  (stopping precision)",
                   "1e-6",  "Smaller = more precise.  Try: 1e-4, 1e-6, 1e-10")
entry_iter = field(scroll_inner, "Max Iterations  (safety limit)",
                   "100",   "Usually 50-200 is enough")

# ─── 3-D button factory ───
def make_3d_button(parent, text, top_color, mid_color, bot_color,
                   text_color="#ffffff", command=None, height=42):
    btn_canvas = tk.Canvas(parent, height=height, bg=CARD_BG,
                           bd=0, highlightthickness=0, cursor="hand2")
    btn_canvas.pack(fill=X, padx=16, pady=4)

    def draw(pressed=False):
        btn_canvas.delete("all")
        w = btn_canvas.winfo_width() or 280
        h = height
        offset = 4
        if not pressed:
            btn_canvas.create_rectangle(offset, offset, w, h,
                                        fill=bot_color, outline="")
            btn_canvas.create_rectangle(0, 0, w-offset, h-offset,
                                        fill=mid_color, outline="")
            btn_canvas.create_rectangle(0, 0, w-offset, 4,
                                        fill=top_color, outline="")
            btn_canvas.create_rectangle(0, 0, 3, h-offset,
                                        fill=top_color, outline="")
            ty = (h-offset) // 2
        else:
            btn_canvas.create_rectangle(offset, offset, w, h,
                                        fill=mid_color, outline="")
            btn_canvas.create_rectangle(offset, offset, w, offset+3,
                                        fill=bot_color, outline="")
            btn_canvas.create_rectangle(offset, offset, offset+3, h,
                                        fill=bot_color, outline="")
            ty = (h-offset) // 2 + 2
        btn_canvas.create_text(w//2, ty, text=text, fill=text_color,
                               font=("Segoe UI", 11, "bold"), anchor="center")

    def on_press(e):     draw(pressed=True)
    def on_release(e):   draw(pressed=False); command and command()
    def on_configure(e): draw(pressed=False)

    btn_canvas.bind("<ButtonPress-1>",   on_press)
    btn_canvas.bind("<ButtonRelease-1>", on_release)
    btn_canvas.bind("<Configure>",       on_configure)

    def btn_config(**kw):
        nonlocal text
        if "text" in kw:
            text = kw["text"]; draw()
        if "state" in kw:
            if kw["state"] == DISABLED:
                btn_canvas.unbind("<ButtonPress-1>")
                btn_canvas.unbind("<ButtonRelease-1>")
                btn_canvas.config(cursor="")
            else:
                btn_canvas.bind("<ButtonPress-1>",   on_press)
                btn_canvas.bind("<ButtonRelease-1>", on_release)
                btn_canvas.config(cursor="hand2")
    btn_canvas.config_btn = btn_config
    return btn_canvas

# ─── buttons ───
tk.Frame(scroll_inner, bg=CARD_BG, height=14).pack()

btn_compute = make_3d_button(
    scroll_inner, text="  COMPUTE ROOT  ",
    top_color=BTN_GREEN_TOP, mid_color=BTN_GREEN_MID, bot_color=BTN_GREEN_BOT,
    text_color="#ffffff", command=compute_with_status, height=48)

make_3d_button(
    scroll_inner, text="  CLEAR ALL  ",
    top_color=BTN_RED_TOP, mid_color=BTN_RED_MID, bot_color=BTN_RED_BOT,
    text_color="#ffffff", command=clear_all, height=40)

section_title(scroll_inner, "QUICK EXAMPLES", MUTED)
tk.Label(scroll_inner, text="  Click any example to load it instantly:",
         bg=CARD_BG, fg=MUTED, font=("Segoe UI", 9)
         ).pack(anchor="w", padx=16, pady=(0,6))

examples = [
    ("x^3 - x - 2",  "x**3 - x - 2", "1", "2"),
    ("cos(x) - x",   "cos(x) - x",   "0", "1"),
    ("x^2 - 4",      "x**2 - 4",     "1", "3"),
    ("exp(x) - 3x",  "exp(x) - 3*x", "0", "1"),
    ("sin(x)",       "sin(x)",        "2", "4"),
    ("log(x) - 1",   "log(x) - 1",   "2", "3"),
]
for lbl, expr, ea, eb in examples:
    make_3d_button(
        scroll_inner, text=f"  {lbl}",
        top_color=BTN_EX_TOP, mid_color=BTN_EX_MID, bot_color=BTN_EX_BOT,
        text_color=ACCENT1,
        command=lambda e=expr, a=ea, b=eb: load_example(e, a, b),
        height=34)

tk.Frame(scroll_inner, bg=CARD_BG, height=20).pack()

# ════════════════════════════════════════════
#  RIGHT — OUTPUT (notebook + graph side by side)
# ════════════════════════════════════════════
right = tk.Frame(master, bg=BG)
right.grid(row=0, column=1, sticky="nsew")
right.grid_rowconfigure(0, weight=1)
right.grid_columnconfigure(0, weight=1)
right.grid_columnconfigure(1, weight=1)

# ── Notebook (left half of right side) ───────
nb_wrap = tk.Frame(right, bg=BG)
nb_wrap.grid(row=0, column=0, sticky="nsew", padx=(10,4), pady=8)
nb_wrap.grid_rowconfigure(0, weight=1)
nb_wrap.grid_columnconfigure(0, weight=1)

sty = ttk.Style()
sty.configure("TNotebook",     background=BG, borderwidth=0)
sty.configure("TNotebook.Tab", background="#1c1c2e", foreground=MUTED,
              padding=[14,6],  font=("Segoe UI", 10, "bold"))
sty.map("TNotebook.Tab",
        background=[("selected","#0a0a18")],
        foreground=[("selected", ACCENT1)])

notebook = ttk.Notebook(nb_wrap)
notebook.grid(row=0, column=0, sticky="nsew")

def make_text_tab(nb, tab_title, fg_color):
    frm = tk.Frame(nb, bg=BG)
    nb.add(frm, text=f"  {tab_title}  ")
    frm.grid_rowconfigure(0, weight=1)
    frm.grid_columnconfigure(0, weight=1)
    txt = tk.Text(frm, font=("Consolas", 10), wrap=WORD,
                  bg="#0d0d1a", fg=fg_color,
                  insertbackground="white",
                  relief="flat", padx=12, pady=10,
                  selectbackground="#2a2a5a")
    txt.grid(row=0, column=0, sticky="nsew")
    sc = ttkb.Scrollbar(frm, command=txt.yview)
    sc.grid(row=0, column=1, sticky="ns")
    txt.configure(yscrollcommand=sc.set)
    return txt

results_text = make_text_tab(notebook, "Summary",        "#a8ffb0")
steps_text   = make_text_tab(notebook, "Solution Trail", "#ffe082")

steps_text.tag_configure("header",  foreground=TRAIL_HEADER,  font=("Consolas", 10, "bold"))
steps_text.tag_configure("label",   foreground=TRAIL_LABEL,   font=("Consolas", 10))
steps_text.tag_configure("value",   foreground=TRAIL_VALUE,   font=("Consolas", 10, "bold"))
steps_text.tag_configure("explain", foreground=TRAIL_EXPLAIN, font=("Consolas", 10))
steps_text.tag_configure("good",    foreground=TRAIL_GOOD,    font=("Consolas", 10, "bold"))
steps_text.tag_configure("warn",    foreground=TRAIL_WARN,    font=("Consolas", 10, "bold"))
steps_text.tag_configure("dim",     foreground=TRAIL_DIM,     font=("Consolas", 10))

# Iteration table tab
tab_tbl = tk.Frame(notebook, bg=BG)
notebook.add(tab_tbl, text="  Iteration Table  ")
tab_tbl.grid_rowconfigure(0, weight=1)
tab_tbl.grid_columnconfigure(0, weight=1)

t_sty = ttk.Style()
t_sty.configure("T.Treeview",
                background="#0d0d1a", foreground="#c8c8ff",
                fieldbackground="#0d0d1a", rowheight=22,
                font=("Consolas", 9))
t_sty.configure("T.Treeview.Heading",
                background="#1c1c2e", foreground=ACCENT2,
                font=("Segoe UI", 9, "bold"))
t_sty.map("T.Treeview", background=[("selected","#2a2a5e")])

cols = ("Iter","a","b","Midpoint c","f(a)","f(b)","f(c)","Width","Decision")
iter_tree = ttk.Treeview(tab_tbl, columns=cols, show="headings",
                          style="T.Treeview", height=30)
widths = [38,100,100,115,85,85,90,90,120]
for col, w in zip(cols, widths):
    iter_tree.heading(col, text=col)
    iter_tree.column(col, width=w, anchor=CENTER, minwidth=36)
iter_tree.tag_configure("odd",  background="#161628")
iter_tree.tag_configure("even", background="#0d0d1a")
tsy = ttkb.Scrollbar(tab_tbl, command=iter_tree.yview)
tsx = ttkb.Scrollbar(tab_tbl, orient=HORIZONTAL, command=iter_tree.xview)
iter_tree.configure(yscrollcommand=tsy.set, xscrollcommand=tsx.set)
iter_tree.grid(row=0, column=0, sticky="nsew")
tsy.grid(row=0, column=1, sticky="ns")
tsx.grid(row=1, column=0, sticky="ew")

# placeholder text
results_text.insert(END,
    "Results will appear here.\n\n"
    "Enter your function and interval on the LEFT, then click COMPUTE ROOT.")
results_text.config(state=DISABLED)
steps_text.insert(END,
    "The Solution Trail will appear here after you click COMPUTE ROOT.\n\n"
    "It will stream line-by-line, showing exactly how the algorithm\n"
    "reasons through every iteration - like watching it think:\n\n"
    "  -> IVT validity check\n"
    "  -> Midpoint calculation with real numbers\n"
    "  -> f(c) evaluation\n"
    "  -> Left or right decision with reasoning\n"
    "  -> Stopping condition check\n"
    "  -> Final answer with error bound\n",
    "explain")
steps_text.config(state=DISABLED)

# ── Graph (right half of right side) ─────────
gr_wrap = tk.Frame(right, bg=BG)
gr_wrap.grid(row=0, column=1, sticky="nsew", padx=(4,10), pady=8)
gr_wrap.grid_rowconfigure(1, weight=1)
gr_wrap.grid_columnconfigure(0, weight=1)

tk.Label(gr_wrap, text="GRAPH", bg=BG, fg=ACCENT1,
         font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0,4))

graph_frame = tk.Frame(gr_wrap, bg=BG,
                        highlightbackground="#2a2a4a", highlightthickness=1)
graph_frame.grid(row=1, column=0, sticky="nsew")
tk.Label(graph_frame,
         text="Graph appears after computation",
         bg=BG, fg=MUTED, font=("Segoe UI", 12)
         ).place(relx=0.5, rely=0.5, anchor="center")

# ── Status bar ───────────────────────────────
sbar = ttkb.Frame(root, bootstyle=SECONDARY, height=26)
sbar.grid(row=2, column=0, sticky="ew")
status_label = ttkb.Label(sbar, text="  Ready",
                           bootstyle=(SECONDARY, INVERSE),
                           font=("Segoe UI", 10))
status_label.pack(side=LEFT, padx=6)
ttkb.Label(sbar,
           text="Bisection Method  |  Enter = Compute   Esc = Clear  ",
           bootstyle=(SECONDARY, INVERSE),
           font=("Segoe UI", 9)).pack(side=RIGHT, padx=8)

root.bind("<Return>", lambda e: compute_with_status())
root.bind("<Escape>", lambda e: clear_all())

root.mainloop()
