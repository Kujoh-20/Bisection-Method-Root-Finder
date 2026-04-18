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
ACCENT4   = "#ff8a65"
TEXT_FG   = "#e8eaf6"
MUTED     = "#7986cb"

BTN_GREEN_TOP = "#2ecc71"; BTN_GREEN_MID = "#27ae60"; BTN_GREEN_BOT = "#1a7a43"
BTN_RED_TOP   = "#e74c3c"; BTN_RED_MID   = "#c0392b"; BTN_RED_BOT   = "#922b21"
BTN_EX_TOP    = "#3d3d6b"; BTN_EX_MID    = "#2e2e55"; BTN_EX_BOT    = "#1a1a38"

TRAIL_HEADER  = "#4fc3f7"
TRAIL_LABEL   = "#c792ea"
TRAIL_VALUE   = "#ffffff"
TRAIL_EXPLAIN = "#ffe082"
TRAIL_GOOD    = "#69f0ae"
TRAIL_WARN    = "#ff7043"
TRAIL_DIM     = "#546e7a"
TRAIL_METHOD  = "#ff8a65"
TRAIL_EDGE    = "#ff4444"   # bright red — edge case warnings in trail

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


# ════════════════════════════════════════════
#  EDGE CASE DETECTOR
#  Returns a list of warning strings (empty = no edge cases).
#  Called BEFORE running the numerical method so the UI can
#  display in-trail warnings without crashing.
# ════════════════════════════════════════════
def detect_edge_cases(f_expr, a, b, tol, max_iter):
    """
    Checks for 5 known edge cases and returns a list of
    (code, message) tuples for any that are detected.

    Edge Case List
    --------------
    EC1 — Same-sign endpoints (IVT violated)
    EC2 — f(a) = 0 or f(b) = 0 (root exactly at endpoint)
    EC3 — Function undefined / evaluates to NaN or Inf at a or b
    EC4 — Max iterations too low (fewer than 10) — likely to not converge
    EC5 — Tolerance too loose relative to interval width (tol >= (b-a)/2)
    """
    warnings = []
    f = make_f(f_expr)

    # EC3 — Evaluate at endpoints first (catches undefined functions)
    try:
        fa = float(f(a))
        fb = float(f(b))
        fa_ok = np.isfinite(fa)
        fb_ok = np.isfinite(fb)
        if not fa_ok:
            warnings.append(("EC3", f"f(a) = f({a}) is undefined or infinite. "
                             "The function cannot be evaluated at the left endpoint."))
        if not fb_ok:
            warnings.append(("EC3", f"f(b) = f({b}) is undefined or infinite. "
                             "The function cannot be evaluated at the right endpoint."))
        if not fa_ok or not fb_ok:
            return warnings   # can't check the rest reliably
    except Exception as exc:
        warnings.append(("EC3", f"Function evaluation error at endpoints: {exc}"))
        return warnings

    # EC2 — Root exactly at endpoint
    if abs(fa) < 1e-14:
        warnings.append(("EC2", f"f(a) = f({a}) = {fa:.6e} is exactly zero (or near zero). "
                         "The root is at the left endpoint itself."))
    if abs(fb) < 1e-14:
        warnings.append(("EC2", f"f(b) = f({b}) = {fb:.6e} is exactly zero (or near zero). "
                         "The root is at the right endpoint itself."))

    # EC1 — Same sign (only warn here; hard block happens in compute())
    if fa * fb > 0:
        warnings.append(("EC1", f"f(a)={fa:.4f} and f(b)={fb:.4f} have the SAME sign. "
                         "IVT cannot guarantee a root in [{a}, {b}]."))

    # EC4 — Max iterations too low
    if max_iter < 10:
        warnings.append(("EC4", f"Max iterations = {max_iter} is very low. "
                         "The method is unlikely to converge to the required tolerance. "
                         "Recommended minimum: 10."))

    # EC5 — Tolerance too loose
    half_width = (b - a) / 2.0
    if tol >= half_width:
        warnings.append(("EC5", f"Tolerance ({tol}) is larger than or equal to half the "
                         f"bracket width ({half_width:.6f}). The stopping condition will "
                         "fire immediately without meaningful narrowing."))

    return warnings


# ════════════════════════════════════════════
#  NUMERICAL METHODS
# ════════════════════════════════════════════

def run_bisection(f, a, b, tol, max_iter):
    history, brackets = [], []
    ca, cb = a, b
    stop_reason = "max_iter"
    for i in range(1, max_iter + 1):
        fa, fb = float(f(ca)), float(f(cb))
        c  = (ca + cb) / 2.0
        fc = float(f(c))
        w  = cb - ca
        dec = "Left  [a->c]" if fa * fc < 0 else "Right [c->b]"
        brackets.append((ca, cb))
        history.append((i, ca, cb, fa, fb, c, fc, w, dec))
        if abs(fc) < tol:
            stop_reason = "f(c)_tol"; break
        if w / 2 < tol:
            stop_reason = "bracket_tol"; break
        if fa * fc < 0:
            cb = c
        else:
            ca = c
    return c, history, brackets, stop_reason


def run_false_position(f, a, b, tol, max_iter):
    history, brackets = [], []
    ca, cb = a, b
    stop_reason = "max_iter"
    for i in range(1, max_iter + 1):
        fa, fb = float(f(ca)), float(f(cb))
        denom = fb - fa
        if abs(denom) < 1e-15:
            stop_reason = "max_iter"; break
        c  = cb - fb * (cb - ca) / denom
        fc = float(f(c))
        w  = cb - ca
        dec = "Left  [a->c]" if fa * fc < 0 else "Right [c->b]"
        brackets.append((ca, cb))
        history.append((i, ca, cb, fa, fb, c, fc, w, dec))
        if abs(fc) < tol:
            stop_reason = "f(c)_tol"; break
        if abs(cb - ca) / 2 < tol:
            stop_reason = "bracket_tol"; break
        if fa * fc < 0:
            cb = c
        else:
            ca = c
    return c, history, brackets, stop_reason


# ── Graph ────────────────────────────────────
def plot_graph(expr, root_val, brackets, method_name):
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

    color = ACCENT1 if method_name == "Bisection" else ACCENT4
    fig = Figure(figsize=(5, 4), dpi=100, facecolor=BG)
    ax  = fig.add_subplot(111, facecolor=BG)
    for sp in ax.spines.values():
        sp.set_edgecolor("#2a2a4a")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_xlabel("x", color=MUTED, fontsize=10)
    ax.set_ylabel("f(x)", color=MUTED, fontsize=10)
    ax.set_title(f"[{method_name}]  f(x) = {expr}", color=TEXT_FG, fontsize=10, pad=8)
    ax.grid(True, alpha=0.12, color="#444488")
    ax.axhline(0, color="#444466", linewidth=0.8)
    ax.axvline(0, color="#444466", linewidth=0.8)
    ax.plot(x, y, color=color, linewidth=2.2, label="f(x)", zorder=3)
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


# ════════════════════════════════════════════
#  SOLUTION TRAIL
# ════════════════════════════════════════════

def build_trail_segments(method_name, f_expr, a, b, tol, max_iter,
                          history, root_val, stop_reason, edge_warnings=None):
    f = make_f(f_expr)
    fa0, fb0 = float(f(a)), float(f(b))
    segs = []

    def h(t):    segs.append((t + "\n", "header"))
    def m(t):    segs.append((t + "\n", "method"))
    def e(t):    segs.append((t + "\n", "edge"))      # edge case warning line
    def lv(label, val):
        segs.append((f"  {label}", "label"))
        segs.append((f"  {val}\n", "value"))
    def p(t):    segs.append(("  " + t + "\n", "explain"))
    def good(t): segs.append(("  " + t + "\n", "good"))
    def warn(t): segs.append(("  " + t + "\n", "warn"))
    def sep():   segs.append(("  " + "-" * 52 + "\n", "dim"))
    def blank(): segs.append(("\n", "explain"))

    h("=" * 56)
    h("  SOLUTION TRAIL")
    h("=" * 56)
    blank()

    # ── Edge case warnings block (top of trail) ──
    if edge_warnings:
        h("  !! EDGE CASE WARNINGS DETECTED !!")
        sep()
        for code, msg in edge_warnings:
            e(f"  [{code}] WARNING:")
            # wrap the message manually at ~54 chars
            words = msg.split()
            line = "    "
            for word in words:
                if len(line) + len(word) + 1 > 56:
                    e(line)
                    line = "    " + word + " "
                else:
                    line += word + " "
            if line.strip():
                e(line)
            blank()
        h("  Proceed with caution — results may be unreliable.")
        sep()
        blank()

    # ── Method badge ──
    m("  METHOD USED:")
    if method_name == "Bisection":
        m("  >> BISECTION METHOD <<")
        p("  Midpoint formula:  c = (a + b) / 2")
        p("  Splits the bracket exactly in half each iteration.")
        p("  Guaranteed to converge, but convergence is slow (linear).")
    else:
        m("  >> FALSE POSITION METHOD  (Regula Falsi) <<")
        p("  Midpoint formula:  c = b - f(b)*(b-a) / (f(b)-f(a))")
        p("  Uses a weighted secant line to estimate the root.")
        p("  Often converges faster than bisection for smooth functions.")
    blank()

    # ── Setup ──
    h("  PROBLEM SETUP")
    sep()
    lv("Function  :", f"f(x) = {f_expr}")
    lv("Interval  :", f"a = {a},   b = {b}")
    lv("Tolerance :", str(tol))
    lv("Max Iters :", str(max_iter))
    blank()

    # ── Stopping rules ──
    h("  STOPPING / COMPLETION RULES")
    sep()
    p("The loop stops as soon as ANY of these rules fires:")
    blank()
    lv("  Rule 1 - Tolerance on f(c) :",
       f"|f(c)| < {tol}  (midpoint value close enough to zero)")
    lv("  Rule 2 - Tolerance on bracket :",
       f"(b-a)/2 < {tol}  (bracket too narrow to matter)")
    lv("  Rule 3 - Max iterations :",
       f"i > {max_iter}  (safety cap)")
    blank()
    if stop_reason == "f(c)_tol":
        good("  ACTIVE THIS RUN  ->  Rule 1  (|f(c)| < tolerance)")
    elif stop_reason == "bracket_tol":
        good("  ACTIVE THIS RUN  ->  Rule 2  (bracket width < tolerance)")
    else:
        warn(f"  ACTIVE THIS RUN  ->  Rule 3  (hit max iterations = {max_iter})")
    blank()

    # ── IVT check ──
    h("  STEP 0 - VALIDITY CHECK  (Intermediate Value Theorem)")
    sep()
    p("f(a) and f(b) must have OPPOSITE signs for a root to exist")
    p("in the interval [a, b].")
    blank()
    lv(f"f(a) = f({a})  =", f"{fa0:.8f}  ({'negative' if fa0 < 0 else 'positive'})")
    lv(f"f(b) = f({b})  =", f"{fb0:.8f}  ({'negative' if fb0 < 0 else 'positive'})")
    lv("f(a) x f(b)   =", f"{fa0 * fb0:.6f}")
    blank()
    if fa0 * fb0 < 0:
        good("OK  Opposite signs confirmed - safe to proceed!")
    else:
        warn("X  Same sign - method cannot be applied here.")
    blank()

    # ── Iterations ──
    h("  ITERATION-BY-ITERATION TRAIL")
    sep()
    blank()

    for (i, ia, ib, fa, fb, ic, fc, w, dec) in history:
        h(f"  [ ITERATION {i} ]")
        lv("  Current bracket :", f"[ {ia:.8f},  {ib:.8f} ]")
        lv("  Bracket width   :", f"{w:.8f}")
        blank()
        if method_name == "Bisection":
            p("Bisection: split bracket exactly in half.")
            lv("  c = (a + b) / 2", "")
            lv(f"    = ({ia:.6f} + {ib:.6f}) / 2", "")
        else:
            p("False Position: draw secant line through (a, f(a)) and (b, f(b)),")
            p("find where it crosses the x-axis.")
            lv("  c = b - f(b)*(b-a) / (f(b)-f(a))", "")
            lv(f"    = {ib:.6f} - ({fb:.6f})*({ib:.6f}-{ia:.6f}) / ({fb:.6f}-{fa:.6f})", "")
        lv("    =", f"{ic:.10f}")
        blank()
        p("Evaluate the function at the new point c:")
        lv(f"  f(c) = f({ic:.8f})", "")
        lv("       =", f"{fc:.10f}")
        blank()
        p("Check stopping condition:")
        if abs(fc) < tol:
            lv("  |f(c)| =", f"{abs(fc):.3e}")
            lv("  tol    =", f"{tol}")
            good(f"  {abs(fc):.3e}  <  {tol}  - f(c) close enough to zero!")
            good("  ROOT FOUND - stopping here.")
        elif w / 2 < tol:
            lv("  bracket/2 =", f"{w/2:.3e}")
            lv("  tol       =", f"{tol}")
            good(f"  {w/2:.3e}  <  {tol}  - bracket tiny enough!")
            good("  ROOT FOUND - stopping here.")
        else:
            lv("  |f(c)| =", f"{abs(fc):.3e}  (still above tol {tol})")
            p("  Not precise enough yet - keep narrowing.")
        blank()
        p("Which half contains the root?")
        lv("  f(a) x f(c) =", f"{fa:.6f} x {fc:.6f} = {fa*fc:.8f}")
        if fa * fc < 0:
            good("  Product NEGATIVE - root in LEFT half [ a, c ]")
            lv("  New bracket:", f"b = c  ->  [ {ia:.7f},  {ic:.7f} ]")
        else:
            good("  Product POSITIVE - root in RIGHT half [ c, b ]")
            lv("  New bracket:", f"a = c  ->  [ {ic:.7f},  {ib:.7f} ]")
        blank()
        sep()
        blank()

    # ── Final answer ──
    f_root = float(f(root_val))
    n = len(history)
    err_b = (b - a) / (2 ** n)

    h("  FINAL ANSWER")
    sep()
    blank()
    m(f"  Method used: {method_name}")
    blank()
    lv("  Root            ~", f"{root_val:.12f}")
    lv("  f(root)          =", f"{f_root:.6e}")
    lv("  Total iterations =", str(n))
    lv("  Error bound      =", f"(b-a) / 2^{n}  =  {err_b:.4e}")
    blank()

    h("  WHY THE PROCESS STOPPED")
    sep()
    if stop_reason == "f(c)_tol":
        good(f"  Rule 1 fired - |f(c)| < {tol}")
        p("  The function value at the midpoint became smaller than")
        p("  the tolerance, confirming the root with full precision.")
        good("  STATUS: CONVERGED")
    elif stop_reason == "bracket_tol":
        good(f"  Rule 2 fired - bracket half-width < {tol}")
        p("  The interval shrank so small both halves are")
        p("  indistinguishable within the required precision.")
        good("  STATUS: CONVERGED")
    else:
        warn(f"  Rule 3 fired - reached max iterations ({max_iter})")
        warn("  Neither tolerance rule triggered within the limit.")
        p("  The answer above is the best point found so far.")
        warn("  STATUS: INCOMPLETE - try higher max iterations")
    blank()

    # ── Repeat edge case warnings at bottom ──
    if edge_warnings:
        h("  !! EDGE CASE SUMMARY (logged at bottom) !!")
        sep()
        for code, msg in edge_warnings:
            e(f"  [{code}]  " + msg[:60] + ("..." if len(msg) > 60 else ""))
        blank()

    p(f"After {n} steps the bracket shrank from width {b-a}")
    p(f"down to {err_b:.4e} - the true root is within {err_b:.4e} of our answer.")
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


# ════════════════════════════════════════════
#  COMPUTE
# ════════════════════════════════════════════
def compute():
    for tb in [steps_text, results_text]:
        tb.config(state=NORMAL)
        tb.delete(1.0, END)
    for row in iter_tree.get_children():
        iter_tree.delete(row)

    method_name = method_var.get()
    f_expr   = entry_function.get().strip()
    a_str    = entry_a.get().strip()
    b_str    = entry_b.get().strip()
    tol_str  = entry_tol.get().strip()
    iter_str = entry_iter.get().strip()

    # ── Basic input validation ──
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

    # ── EC3: function evaluation test ──
    try:
        f = make_f(f_expr)
        fa, fb = float(f(a)), float(f(b))
    except Exception as exc:
        messagebox.showerror("Function Error",
            f"EC3 — Cannot evaluate f(x) at endpoints:\n{exc}\n\n"
            "Check your function syntax (use ** for powers, * for multiply).")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return

    # ── EC3: NaN/Inf at endpoints ──
    if not np.isfinite(fa) or not np.isfinite(fb):
        bad = []
        if not np.isfinite(fa): bad.append(f"f(a) = f({a}) = {fa}")
        if not np.isfinite(fb): bad.append(f"f(b) = f({b}) = {fb}")
        messagebox.showerror("Edge Case EC3 — Undefined Function",
            "The function is undefined (NaN or Infinite) at one or both endpoints:\n\n"
            + "\n".join(bad) +
            "\n\nChoose different endpoints where f(x) is defined.")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        update_status("EC3 — Function undefined at endpoint. Choose different interval.")
        return

    # ── EC2: root exactly at endpoint (warn but continue) ──
    ec2_warning = None
    if abs(fa) < 1e-14:
        ec2_warning = f"EC2: f(a) = f({a}) is exactly zero — root is at the left endpoint!"
        messagebox.showwarning("Edge Case EC2 — Root at Endpoint",
            f"f(a) = f({a}) = {fa:.2e} is essentially zero.\n\n"
            "The root is already at the left endpoint.\n"
            "Computation will continue, but convergence is immediate.")
    elif abs(fb) < 1e-14:
        ec2_warning = f"EC2: f(b) = f({b}) is exactly zero — root is at the right endpoint!"
        messagebox.showwarning("Edge Case EC2 — Root at Endpoint",
            f"f(b) = f({b}) = {fb:.2e} is essentially zero.\n\n"
            "The root is already at the right endpoint.\n"
            "Computation will continue, but convergence is immediate.")

    # ── EC1: same sign — hard stop ──
    if fa * fb > 0:
        messagebox.showerror("Edge Case EC1 — IVT Violated",
            f"EC1: f({a}) = {fa:.4f} and f({b}) = {fb:.4f} have the SAME sign.\n\n"
            "By the Intermediate Value Theorem, this interval does NOT\n"
            "guarantee a root exists between a and b.\n\n"
            "Fix: Choose a different interval where f(a) and f(b) have opposite signs.")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        update_status("EC1 — Same-sign endpoints. IVT violated. Choose a different interval.")
        return

    # ── Run edge case detector for EC4 & EC5 (soft warnings) ──
    edge_warnings = detect_edge_cases(f_expr, a, b, tol, max_iter)
    # Filter out EC1/EC2/EC3 already handled above — keep EC4 and EC5
    soft_warnings = [(c, m) for c, m in edge_warnings if c in ("EC4", "EC5")]

    # Show soft warning popup if needed
    if soft_warnings:
        msg_lines = []
        for code, msg in soft_warnings:
            msg_lines.append(f"[{code}] {msg}")
        messagebox.showwarning("Edge Case Warning",
            "The following potential issues were detected:\n\n" +
            "\n\n".join(msg_lines) +
            "\n\nComputation will still proceed. Check the Solution Trail for details.")

    # ── Run the selected method ──
    try:
        runner = run_bisection if method_name == "Bisection" else run_false_position
        root_val, history, brackets, stop_reason = runner(f, a, b, tol, max_iter)
    except Exception as exc:
        messagebox.showerror("Computation Error", str(exc))
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return

    n = len(history)
    f_root = float(f(root_val))

    if stop_reason == "f(c)_tol":
        stop_label = f"Yes  (Rule 1: |f(c)| < {tol})"
    elif stop_reason == "bracket_tol":
        stop_label = f"Yes  (Rule 2: bracket/2 < {tol})"
    else:
        stop_label = f"No   (Rule 3: hit max iter = {max_iter})"

    # Build edge warning section for summary
    edge_summary = ""
    all_warnings = detect_edge_cases(f_expr, a, b, tol, max_iter)
    if all_warnings:
        edge_summary = "\n  EDGE CASE WARNINGS:\n"
        for code, msg in all_warnings:
            edge_summary += f"    [{code}] {msg[:55]}...\n" if len(msg) > 55 else f"    [{code}] {msg}\n"
        edge_summary += "\n"

    results_text.insert(END,
        f"{'='*46}\n"
        f"  METHOD: {method_name.upper()}\n"
        f"{'='*46}\n\n"
        f"  f(x)          =  {f_expr}\n"
        f"  Interval      =  [{a}, {b}]\n"
        f"  Tolerance     =  {tol}\n"
        f"  Max Iterations=  {max_iter}\n\n"
        f"  {'-'*40}\n"
        f"  STOPPING RULES:\n"
        f"    Rule 1: |f(c)| < {tol}\n"
        f"    Rule 2: (b-a)/2 < {tol}\n"
        f"    Rule 3: iterations >= {max_iter}\n\n"
        f"{edge_summary}"
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

    # Pass all_warnings to trail so it logs them
    steps_text.config(state=NORMAL)
    steps_text.delete(1.0, END)
    trail_segs = build_trail_segments(
        method_name, f_expr, a, b, tol, max_iter,
        history, root_val, stop_reason,
        edge_warnings=all_warnings if all_warnings else None)
    stream_trail(trail_segs, steps_text, delay_ms=55)

    for (i, ia, ib, fa_i, fb_i, ic, fc, w, dec) in history:
        tag = "odd" if i % 2 == 0 else "even"
        iter_tree.insert("", END, values=(
            i, f"{ia:.7f}", f"{ib:.7f}", f"{ic:.9f}",
            f"{fa_i:.5f}", f"{fb_i:.5f}", f"{fc:.5e}",
            f"{w:.5e}", dec
        ), tags=(tag,))

    plot_graph(f_expr, root_val, brackets, method_name)
    notebook.select(1)

    # Status bar edge case note
    status_suffix = ""
    if all_warnings:
        codes = ", ".join(c for c, _ in all_warnings)
        status_suffix = f"  | EDGE: {codes}"
    update_status(f"[{method_name}]  Root = {root_val:.8f}  |  {n} iterations{status_suffix}  |  Ready")

    ToastNotification(title=f"{method_name} Done!",
        message=f"Root = {root_val:.8f}",
        duration=3000, bootstyle=SUCCESS).show_toast()


def clear_all():
    for tb in [results_text]:
        tb.config(state=NORMAL); tb.delete(1.0, END); tb.config(state=DISABLED)
    steps_text.config(state=NORMAL)
    steps_text.delete(1.0, END)
    steps_text.insert(END,
        "The Solution Trail will appear here after you click COMPUTE ROOT.\n\n"
        "It will stream line-by-line and clearly identify which method\n"
        "was used at the top of the trail.\n\n"
        "Edge case warnings will appear in RED at the top of the trail.\n",
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

def show_about():
    win = tk.Toplevel(root)
    win.title("About — Root Finder")
    win.configure(bg=BG)
    win.resizable(False, False)
    win.grab_set()
    win.update_idletasks()
    w, h = 540, 660
    x = root.winfo_x() + (root.winfo_width()  - w) // 2
    y = root.winfo_y() + (root.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

    canvas = tk.Canvas(win, bg=BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    def _on_mousewheel(ev):
        canvas.yview_scroll(int(-1*(ev.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def row(label, value, y_pos):
        canvas.create_text(30, y_pos, text=label, anchor="w",
                           fill=ACCENT1, font=("Segoe UI", 10, "bold"))
        canvas.create_text(200, y_pos, text=value, anchor="w",
                           fill=TEXT_FG, font=("Segoe UI", 10))

    def section(title, y_pos):
        canvas.create_text(30, y_pos, text=title, anchor="w",
                           fill=ACCENT2, font=("Segoe UI", 11, "bold"))
        canvas.create_line(30, y_pos+18, w-30, y_pos+18, fill="#2a2a4a", width=1)

    canvas.create_rectangle(0, 0, w, 80, fill="#0a0a18", outline="")
    canvas.create_text(w//2, 28, text="Bisection Method Root Finder",
                       fill=ACCENT1, font=("Segoe UI", 16, "bold"))
    canvas.create_text(w//2, 54, text="Numerical Analysis Project | v1.0",
                       fill=MUTED, font=("Segoe UI", 10))
    canvas.create_line(0, 80, w, 80, fill="#1f1f35", width=2)

    yp = 100
    section("PROJECT INFO", yp); yp += 35
    row("Project:", "Bisection Method Root Finder", yp); yp += 28
    row("Version:", "v1.0", yp); yp += 28
    row("Course:", "Numerical Analysis", yp); yp += 40

    section("GROUP MEMBERS", yp); yp += 35
    for name in ["John Oniel Thomas Q. Araque",
                 "Niel Allen S. Jauculan",
                 "Tiff Anthony R. Parnala"]:
        canvas.create_text(30, yp, text=name, anchor="w",
                           fill=TEXT_FG, font=("Segoe UI", 10))
        yp += 24
    yp += 20

    section("DESCRIPTION", yp); yp += 35
    desc = ("This system finds roots of mathematical functions using two "
            "bracketing methods: Bisection and False Position (Regula Falsi).\n\n"
            "Both methods require an interval [a, b] where f(a) and f(b) have "
            "opposite signs, guaranteeing a root by the Intermediate Value Theorem.\n\n"
            "The app detects edge cases (undefined functions, same-sign endpoints, "
            "root at endpoint, low iterations, loose tolerance) and logs them clearly "
            "in the Solution Trail without crashing.")
    desc_id = canvas.create_text(30, yp, text=desc, anchor="nw",
                                  fill=MUTED, font=("Segoe UI", 9), width=460)
    canvas.update_idletasks()
    yp = canvas.bbox(desc_id)[3] + 25

    section("EDGE CASES HANDLED", yp); yp += 35
    ec_list = [
        "EC1 — Same-sign endpoints (IVT violated) — hard stop + error dialog",
        "EC2 — Root exactly at endpoint — warning dialog, continues",
        "EC3 — Undefined/infinite f(x) at endpoint — hard stop + error dialog",
        "EC4 — Max iterations too low — soft warning, continues",
        "EC5 — Tolerance too loose — soft warning, continues",
    ]
    for ec in ec_list:
        ec_id = canvas.create_text(30, yp, text=ec, anchor="nw",
                                    fill=TRAIL_WARN, font=("Segoe UI", 9), width=460)
        canvas.update_idletasks()
        yp = canvas.bbox(ec_id)[3] + 6
    yp += 20

    section("HOW TO USE", yp); yp += 35
    steps = ("1. Select a method (Bisection or False Position)\n"
             "2. Enter f(x) — use ** for powers, e.g. x**3 - x - 2\n"
             "3. Set the interval [a, b] with opposite-sign endpoints\n"
             "4. Click COMPUTE ROOT or press Enter\n"
             "5. View results in Summary, Solution Trail, and Graph tabs")
    steps_id = canvas.create_text(30, yp, text=steps, anchor="nw",
                                   fill=TEXT_FG, font=("Segoe UI", 9), width=460)
    canvas.update_idletasks()
    yp = canvas.bbox(steps_id)[3] + 40

    close_btn = tk.Button(win, text="  Close  ",
                          bg=ACCENT1, fg="#000000",
                          font=("Segoe UI", 10, "bold"),
                          relief="flat", bd=0, padx=20, pady=8,
                          cursor="hand2", command=win.destroy)
    canvas.create_window(w//2, yp, window=close_btn)
    canvas.configure(scrollregion=(0, 0, w, yp + 60))

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
                   title="Root Finder — Bisection & False Position",
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
about_btn = tk.Button(hdr, text=" ? Help / About ",
                      bg="#1a1a35", fg=ACCENT1,
                      font=("Segoe UI", 9, "bold"),
                      relief="flat", bd=0, padx=10, pady=4,
                      cursor="hand2", activebackground="#2a2a55",
                      activeforeground=ACCENT1, command=show_about)
about_btn.place(relx=0.0, rely=0.5, anchor="w", x=12)

# ── Master layout ─────────────────────────────
master = tk.Frame(root, bg=BG)
master.grid(row=1, column=0, sticky="nsew")
master.grid_rowconfigure(0, weight=1)
master.grid_columnconfigure(0, weight=0)
master.grid_columnconfigure(1, weight=1)
tk.Frame(master, bg="#2a2a4a", width=2).grid(row=0, column=0, sticky="ns", padx=(340,0))

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

def _on_configure(ev):
    canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
scroll_inner.bind("<Configure>", _on_configure)

def _on_mousewheel(ev):
    canvas_scroll.yview_scroll(int(-1*(ev.delta/120)), "units")
canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)

def section_title(parent, text, fg=ACCENT1):
    f = tk.Frame(parent, bg=CARD_BG)
    f.pack(fill=X, padx=16, pady=(18, 4))
    tk.Label(f, text=text, bg=CARD_BG, fg=fg,
             font=("Segoe UI", 11, "bold")).pack(side=LEFT)
    tk.Frame(f, bg=fg, height=2).pack(side=LEFT, fill=X, expand=True, padx=(8,0), pady=6)

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
    e = tk.Entry(border, font=("Consolas", 13),
                 bg="#ffffff", fg="#000000",
                 insertbackground="#000000",
                 selectbackground="#4fc3f7", selectforeground="#000000",
                 relief="flat", bd=0, highlightthickness=0)
    e.pack(fill=X, ipady=10, padx=4, pady=4)
    e.insert(0, default)
    def on_focus_in(evt):  border.config(bg=ACCENT1)
    def on_focus_out(evt): border.config(bg="#b0bec5")
    e.bind("<FocusIn>",  on_focus_in)
    e.bind("<FocusOut>", on_focus_out)
    return e

# ── Method selector ──────────────────────────
section_title(scroll_inner, "SELECT METHOD", ACCENT4)
method_var = tk.StringVar(value="Bisection")
method_frame = tk.Frame(scroll_inner, bg=CARD_BG)
method_frame.pack(fill=X, padx=16, pady=(0, 4))

def make_method_btn(parent, label, value, desc):
    card = tk.Frame(parent, bg="#12121e", pady=6, padx=10)
    card.pack(fill=X, pady=3)
    top = tk.Frame(card, bg="#12121e")
    top.pack(fill=X)
    rb = tk.Radiobutton(top, text=label, variable=method_var, value=value,
                        bg="#12121e", fg=ACCENT4,
                        selectcolor="#0a0a18",
                        activebackground="#12121e", activeforeground=ACCENT4,
                        font=("Segoe UI", 10, "bold"), indicatoron=True)
    rb.pack(side=LEFT)
    tk.Label(card, text=desc, bg="#12121e", fg=MUTED,
             font=("Segoe UI", 8), wraplength=260, justify=LEFT).pack(anchor="w")

make_method_btn(method_frame, "Bisection",      "Bisection",
                "c = (a+b)/2  |  Guaranteed convergence, steady halving")
make_method_btn(method_frame, "False Position", "False Position",
                "c = b - f(b)*(b-a)/(f(b)-f(a))  |  Faster for smooth f(x)")

# ── Inputs ───────────────────────────────────
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

# ── 3-D buttons ──────────────────────────────
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
            btn_canvas.create_rectangle(offset, offset, w, h, fill=bot_color, outline="")
            btn_canvas.create_rectangle(0, 0, w-offset, h-offset, fill=mid_color, outline="")
            btn_canvas.create_rectangle(0, 0, w-offset, 4, fill=top_color, outline="")
            btn_canvas.create_rectangle(0, 0, 3, h-offset, fill=top_color, outline="")
            ty = (h-offset) // 2
        else:
            btn_canvas.create_rectangle(offset, offset, w, h, fill=mid_color, outline="")
            btn_canvas.create_rectangle(offset, offset, w, offset+3, fill=bot_color, outline="")
            btn_canvas.create_rectangle(offset, offset, offset+3, h, fill=bot_color, outline="")
            ty = (h-offset) // 2 + 2
        btn_canvas.create_text(w//2, ty, text=text, fill=text_color,
                               font=("Segoe UI", 11, "bold"), anchor="center")
    def on_press(ev):     draw(pressed=True)
    def on_release(ev):   draw(pressed=False); command and command()
    def on_configure(ev): draw(pressed=False)
    btn_canvas.bind("<ButtonPress-1>",   on_press)
    btn_canvas.bind("<ButtonRelease-1>", on_release)
    btn_canvas.bind("<Configure>",       on_configure)
    def btn_config(**kw):
        nonlocal text
        if "text" in kw:  text = kw["text"]; draw()
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

tk.Frame(scroll_inner, bg=CARD_BG, height=14).pack()
btn_compute = make_3d_button(
    scroll_inner, text="  COMPUTE ROOT  ",
    top_color=BTN_GREEN_TOP, mid_color=BTN_GREEN_MID, bot_color=BTN_GREEN_BOT,
    text_color="#ffffff", command=compute_with_status, height=48)
make_3d_button(
    scroll_inner, text="  CLEAR ALL  ",
    top_color=BTN_RED_TOP, mid_color=BTN_RED_MID, bot_color=BTN_RED_BOT,
    text_color="#ffffff", command=clear_all, height=40)

# ── Test Cases ───────────────────────────────
section_title(scroll_inner, "TEST CASES", MUTED)
tk.Label(scroll_inner, text="  5 built-in test cases — click to load:",
         bg=CARD_BG, fg=MUTED, font=("Segoe UI", 9)
         ).pack(anchor="w", padx=16, pady=(0,6))

test_cases = [
    ("TC1: x^3-x-2",   "x**3 - x - 2", "1", "2",  "Cubic polynomial — classic test"),
    ("TC2: cos(x)-x",  "cos(x) - x",   "0", "1",  "Transcendental — Dottie number"),
    ("TC3: x^2-4",     "x**2 - 4",     "1", "3",  "Quadratic — root at x=2"),
    ("TC4: exp(x)-3x", "exp(x) - 3*x", "0", "1",  "Exp vs linear — smooth curve"),
    ("TC5: sin(x)",    "sin(x)",        "2", "4",  "Trig function — root at pi"),
]
for lbl, expr, ea, eb, desc in test_cases:
    make_3d_button(
        scroll_inner, text=f"  {lbl}",
        top_color=BTN_EX_TOP, mid_color=BTN_EX_MID, bot_color=BTN_EX_BOT,
        text_color=ACCENT1,
        command=lambda e=expr, a=ea, b=eb: load_example(e, a, b),
        height=34)
    tk.Label(scroll_inner, text=f"     {desc}",
             bg=CARD_BG, fg=MUTED, font=("Segoe UI", 8)
             ).pack(anchor="w", padx=20)

# ── Edge Case Quick Loads ─────────────────────
section_title(scroll_inner, "EDGE CASE DEMOS", TRAIL_WARN)
tk.Label(scroll_inner, text="  Reproduce edge cases for evidence screenshots:",
         bg=CARD_BG, fg=MUTED, font=("Segoe UI", 9)
         ).pack(anchor="w", padx=16, pady=(0,6))

edge_demos = [
    ("EC1: Same sign",    "x**2 + 1",     "-1", "1",  "EC1 — IVT violated"),
    ("EC2: Root at a",    "x**2 - 1",     "1",  "3",  "EC2 — root exactly at a=1"),
    ("EC3: Undefined",    "log(x)",        "-1", "1",  "EC3 — log undefined at x<0"),
    ("EC4: Low max iter", "x**3 - x - 2", "1",  "2",  "EC4 — set max iter to 2"),
    ("EC5: Loose tol",    "x**3 - x - 2", "1",  "2",  "EC5 — set tolerance to 1.0"),
]
for lbl, expr, ea, eb, desc in edge_demos:
    make_3d_button(
        scroll_inner, text=f"  {lbl}",
        top_color="#5a1a1a", mid_color="#3a1010", bot_color="#1a0808",
        text_color=TRAIL_WARN,
        command=lambda e=expr, a=ea, b=eb: load_example(e, a, b),
        height=32)
    tk.Label(scroll_inner, text=f"     {desc}",
             bg=CARD_BG, fg=MUTED, font=("Segoe UI", 8)
             ).pack(anchor="w", padx=20)

tk.Frame(scroll_inner, bg=CARD_BG, height=20).pack()

# ════════════════════════════════════════════
#  RIGHT — OUTPUT (notebook + graph)
# ════════════════════════════════════════════
right = tk.Frame(master, bg=BG)
right.grid(row=0, column=1, sticky="nsew")
right.grid_rowconfigure(0, weight=1)
right.grid_columnconfigure(0, weight=1)
right.grid_columnconfigure(1, weight=1)

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
                  insertbackground="white", relief="flat",
                  padx=12, pady=10, selectbackground="#2a2a5a")
    txt.grid(row=0, column=0, sticky="nsew")
    sc = ttkb.Scrollbar(frm, command=txt.yview)
    sc.grid(row=0, column=1, sticky="ns")
    txt.configure(yscrollcommand=sc.set)
    return txt

results_text = make_text_tab(notebook, "Summary",        "#a8ffb0")
steps_text   = make_text_tab(notebook, "Solution Trail", "#ffe082")

steps_text.tag_configure("header",  foreground=TRAIL_HEADER,  font=("Consolas", 10, "bold"))
steps_text.tag_configure("method",  foreground=TRAIL_METHOD,  font=("Consolas", 10, "bold"))
steps_text.tag_configure("edge",    foreground=TRAIL_EDGE,    font=("Consolas", 10, "bold"))
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
                fieldbackground="#0d0d1a", rowheight=22, font=("Consolas", 9))
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

results_text.insert(END,
    "Results will appear here.\n\n"
    "Select a method, enter your function and interval, then click COMPUTE ROOT.\n\n"
    "Edge case warnings will appear here and in the Solution Trail.")
results_text.config(state=DISABLED)
steps_text.insert(END,
    "The Solution Trail will appear here after you click COMPUTE ROOT.\n\n"
    "Edge case warnings appear in RED at the very top of the trail.\n\n"
    "  -> EC1: Same-sign endpoints\n"
    "  -> EC2: Root exactly at endpoint\n"
    "  -> EC3: Undefined function at endpoint\n"
    "  -> EC4: Max iterations too low\n"
    "  -> EC5: Tolerance too loose\n",
    "explain")
steps_text.config(state=DISABLED)

# ── Graph ─────────────────────────────────────
gr_wrap = tk.Frame(right, bg=BG)
gr_wrap.grid(row=0, column=1, sticky="nsew", padx=(4,10), pady=8)
gr_wrap.grid_rowconfigure(1, weight=1)
gr_wrap.grid_columnconfigure(0, weight=1)
tk.Label(gr_wrap, text="GRAPH", bg=BG, fg=ACCENT1,
         font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0,4))
graph_frame = tk.Frame(gr_wrap, bg=BG, highlightbackground="#2a2a4a", highlightthickness=1)
graph_frame.grid(row=1, column=0, sticky="nsew")
tk.Label(graph_frame, text="Graph appears after computation",
         bg=BG, fg=MUTED, font=("Segoe UI", 12)
         ).place(relx=0.5, rely=0.5, anchor="center")

# ── Status bar ────────────────────────────────
sbar = ttkb.Frame(root, bootstyle=SECONDARY, height=26)
sbar.grid(row=2, column=0, sticky="ew")
status_label = ttkb.Label(sbar, text="  Ready",
                           bootstyle=(SECONDARY, INVERSE), font=("Segoe UI", 10))
status_label.pack(side=LEFT, padx=6)
ttkb.Label(sbar, text="Root Finder  |  Enter = Compute   Esc = Clear  ",
           bootstyle=(SECONDARY, INVERSE), font=("Segoe UI", 9)).pack(side=RIGHT, padx=8)

root.bind("<Return>", lambda ev: compute_with_status())
root.bind("<Escape>", lambda ev: clear_all())

root.mainloop()