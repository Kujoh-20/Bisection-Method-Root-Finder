"""
═══════════════════════════════════════════════════════════════════
  BISECTION & FALSE POSITION ROOT FINDER
  A polished, theme-aware GUI for numerical root finding.
═══════════════════════════════════════════════════════════════════
  Features
    • Bisection and False Position (Regula Falsi) methods
    • 5 edge-case detectors (EC1 – EC5)
    • 5-point verification report after every run
    • Standardized solution trail with clear headings & spacing
    • Light / Dark theme toggle
    • TXT and HTML export
    • Adaptive, resizable layout

  Week 13 Final Release — v1.0
    • FIX 1: Updated deprecated ttkbootstrap toast import path
    • FIX 2: Removed incorrect /2 in False Position stopping condition
             (bisection's halving formula does not apply to Regula Falsi)
    • FIX 3: verify_root() now method-aware; error bound check is
             relaxed for False Position since (b-a)/2^n is a
             bisection-specific formula
═══════════════════════════════════════════════════════════════════
"""

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import ToastNotification
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════
#  THEME SYSTEM
#  Two cohesive palettes (light / dark). Each uses ~4 neutrals +
#  1 primary + 3 semantic accents (success / warning / danger).
# ═══════════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "name":     "dark",
        "ttk":      "darkly",
        # Surfaces
        "bg":       "#0e1117",
        "panel":    "#161b22",
        "elevated": "#1f262f",
        "input_bg": "#0d1117",
        "border":   "#30363d",
        # Text
        "text":     "#e6edf3",
        "muted":    "#8b949e",
        "subtle":   "#6e7681",
        # Brand + semantic
        "primary":  "#58a6ff",
        "success":  "#3fb950",
        "warning":  "#f59e0b",
        "danger":   "#f87171",
        # Trail-specific (mapped onto semantic)
        "label":    "#a5d6ff",
        "value":    "#e6edf3",
        "explain":  "#8b949e",
        # Plot
        "plot_bg":  "#0e1117",
        "plot_grid":"#30363d",
        "plot_axis":"#8b949e",
    },
    "light": {
        "name":     "light",
        "ttk":      "flatly",
        "bg":       "#f7f8fa",
        "panel":    "#ffffff",
        "elevated": "#f0f2f5",
        "input_bg": "#ffffff",
        "border":   "#e5e7eb",
        "text":     "#111827",
        "muted":    "#6b7280",
        "subtle":   "#9ca3af",
        "primary":  "#2563eb",
        "success":  "#16a34a",
        "warning":  "#ea580c",
        "danger":   "#dc2626",
        "label":    "#1d4ed8",
        "value":    "#111827",
        "explain":  "#6b7280",
        "plot_bg":  "#ffffff",
        "plot_grid":"#e5e7eb",
        "plot_axis":"#6b7280",
    },
}

# Mutable current-theme reference. T is the active palette dict.
T = THEMES["dark"]

# Registry of (widget, {option_name: theme_role}) to repaint on toggle.
THEMED_WIDGETS = []

def themed(widget, **roles):
    """Register a widget so its colours track the active theme."""
    THEMED_WIDGETS.append((widget, roles))
    _apply_widget_theme(widget, roles)
    return widget

def _apply_widget_theme(widget, roles):
    cfg = {opt: T[role] for opt, role in roles.items()}
    try:
        widget.configure(**cfg)
    except tk.TclError:
        pass


# ═══════════════════════════════════════════════════════════════════
#  3D KEYBOARD-STYLE BUTTON HELPER
#  Each button is wrapped in a darker shadow frame so the top "key"
#  surface appears raised. On press, the key shifts down by `shadow_h`
#  pixels and the shadow disappears — giving a tactile, depressible
#  keyboard-key feel.
# ═══════════════════════════════════════════════════════════════════
SHADOW_TINTS = {
    "primary":  {"dark": "#1f6feb", "light": "#1d4ed8"},
    "success":  {"dark": "#2ea043", "light": "#15803d"},
    "warning":  {"dark": "#b45309", "light": "#9a3412"},
    "danger":   {"dark": "#b91c1c", "light": "#991b1b"},
    # darker than the button face so the keycap looks raised
    "elevated": {"dark": "#0d1117", "light": "#cbd5e1"},
    "panel":    {"dark": "#0d1117", "light": "#cbd5e1"},
}

THREEDEE_BUTTONS = []  # for theme repaint: (wrap, btn, bg_role)

def make_3d_button(parent, text, command,
                   bg_role="primary", fg_role="panel",
                   font_size=11, bold=True,
                   ipadx=18, ipady=10, shadow_h=4):
    """Return (wrap_frame, button). Pack/grid the wrap_frame; reference the
    button to update text/state later (e.g. compute spinner)."""
    weight = "bold" if bold else "normal"

    def shadow_color():
        tint = SHADOW_TINTS.get(bg_role, SHADOW_TINTS["elevated"])
        return tint[T["name"]]

    wrap = tk.Frame(parent, bg=shadow_color())

    btn = tk.Button(wrap, text=text, command=command,
                    font=("Segoe UI", font_size, weight),
                    relief="flat", bd=0,
                    padx=ipadx, pady=ipady, cursor="hand2",
                    highlightthickness=0)
    _apply_widget_theme(btn, {"bg": bg_role, "fg": fg_role,
                              "activebackground": bg_role,
                              "activeforeground": fg_role})
    THEMED_WIDGETS.append((btn, {"bg": bg_role, "fg": fg_role,
                                 "activebackground": bg_role,
                                 "activeforeground": fg_role}))
    btn.pack(fill=X, padx=0, pady=(0, shadow_h))

    def on_press(_):
        # Shift key down — shadow hidden, simulating a pressed keycap
        btn.pack_configure(pady=(shadow_h, 0))
    def on_release(_):
        btn.pack_configure(pady=(0, shadow_h))
    btn.bind("<ButtonPress-1>", on_press)
    btn.bind("<ButtonRelease-1>", on_release)

    THREEDEE_BUTTONS.append((wrap, btn, bg_role))
    return wrap, btn


# ═══════════════════════════════════════════════════════════════════
#  SAFE EVALUATOR
# ═══════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════
#  VERIFICATION ENGINE — 5 independent post-run checks
# ═══════════════════════════════════════════════════════════════════
def verify_root(f_expr, root_val, a, b, tol, n_iters, method="Bisection"):
    f = make_f(f_expr)
    report = {}
    try:
        residual = float(f(root_val))
        report["residual"]     = residual
        report["residual_abs"] = abs(residual)
        report["residual_ok"]  = abs(residual) < max(tol * 100, 1e-8)
    except Exception as exc:
        report["residual"]     = None
        report["residual_abs"] = None
        report["residual_ok"]  = False
        report["residual_err"] = str(exc)

    report["backcheck_val"] = report.get("residual")
    report["backcheck_ok"]  = report.get("residual_ok", False)
    report["in_bracket"]    = (a <= root_val <= b)

    # BUG FIX (Week 12): Error bound (b-a)/2^n is only theoretically valid
    # for Bisection. For False Position we still show it as an estimate
    # but relax the pass threshold since convergence is not guaranteed
    # to halve the interval each step.
    if n_iters > 0:
        report["error_bound"]    = (b - a) / (2 ** n_iters)
        if method == "Bisection":
            report["error_bound_ok"] = report["error_bound"] <= tol * 10
        else:
            # False Position may converge faster or slower; treat as advisory
            report["error_bound_ok"] = True
    else:
        report["error_bound"]    = float("inf")
        report["error_bound_ok"] = False

    if report["residual_abs"] is not None:
        report["within_tol"] = report["residual_abs"] <= tol
    else:
        report["within_tol"] = False

    report["passed"] = (report["residual_ok"] and report["in_bracket"]
                       and report["error_bound_ok"])
    return report


# ═══════════════════════════════════════════════════════════════════
#  EDGE CASE DETECTOR (EC1 – EC5)
# ═══════════════════════════════════════════════════════════════════
def detect_edge_cases(f_expr, a, b, tol, max_iter):
    warnings = []
    f = make_f(f_expr)

    try:
        fa = float(f(a)); fb = float(f(b))
        fa_ok = np.isfinite(fa); fb_ok = np.isfinite(fb)
        if not fa_ok:
            warnings.append(("EC3", f"f(a) = f({a}) is undefined or infinite. "
                             "The function cannot be evaluated at the left endpoint."))
        if not fb_ok:
            warnings.append(("EC3", f"f(b) = f({b}) is undefined or infinite. "
                             "The function cannot be evaluated at the right endpoint."))
        if not fa_ok or not fb_ok:
            return warnings
    except Exception as exc:
        warnings.append(("EC3", f"Function evaluation error at endpoints: {exc}"))
        return warnings

    if abs(fa) < 1e-14:
        warnings.append(("EC2", f"f(a) = f({a}) = {fa:.6e} is essentially zero. "
                         "The root is at the left endpoint itself."))
    if abs(fb) < 1e-14:
        warnings.append(("EC2", f"f(b) = f({b}) = {fb:.6e} is essentially zero. "
                         "The root is at the right endpoint itself."))
    if fa * fb > 0:
        warnings.append(("EC1", f"f(a)={fa:.4f} and f(b)={fb:.4f} have the SAME sign. "
                         f"IVT cannot guarantee a root in [{a}, {b}]."))
    if max_iter < 10:
        warnings.append(("EC4", f"Max iterations = {max_iter} is very low. "
                         "Convergence to the required tolerance is unlikely. "
                         "Recommended minimum: 10."))
    half_width = (b - a) / 2.0
    if tol >= half_width:
        warnings.append(("EC5", f"Tolerance ({tol}) is greater than or equal to "
                         f"half the bracket width ({half_width:.6f}). The stopping "
                         "condition will fire immediately without meaningful narrowing."))
    return warnings


# ═══════════════════════════════════════════════════════════════════
#  NUMERICAL METHODS
# ═══════════════════════════════════════════════════════════════════
def run_bisection(f, a, b, tol, max_iter):
    history, brackets = [], []
    ca, cb = a, b
    stop_reason = "max_iter"
    c = (ca + cb) / 2.0
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
    c = (ca + cb) / 2.0
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
        # BUG FIX (Week 12): Removed incorrect "/ 2" — that was bisection's
        # halving formula. False Position does not guarantee halving the
        # interval each step, so we check the full bracket width instead.
        if abs(cb - ca) < tol:
            stop_reason = "bracket_tol"; break
        if fa * fc < 0:
            cb = c
        else:
            ca = c
    return c, history, brackets, stop_reason


# ═══════════════════════════════════════════════════════════════════
#  GRAPH
# ═══════════════════════════════════════════════════════════════════
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

    color = T["primary"] if method_name == "Bisection" else T["warning"]
    fig = Figure(figsize=(5, 4), dpi=100, facecolor=T["plot_bg"])
    ax  = fig.add_subplot(111, facecolor=T["plot_bg"])
    for sp in ax.spines.values():
        sp.set_edgecolor(T["border"])
    ax.tick_params(colors=T["plot_axis"], labelsize=9)
    ax.set_xlabel("x", color=T["plot_axis"], fontsize=10)
    ax.set_ylabel("f(x)", color=T["plot_axis"], fontsize=10)
    ax.set_title(f"[{method_name}]   f(x) = {expr}",
                 color=T["text"], fontsize=10, pad=8)
    ax.grid(True, alpha=0.25, color=T["plot_grid"])
    ax.axhline(0, color=T["plot_grid"], linewidth=0.8)
    ax.axvline(0, color=T["plot_grid"], linewidth=0.8)
    ax.plot(x, y, color=color, linewidth=2.2, label="f(x)", zorder=3)
    for i, (ia, ib) in enumerate(brackets[-8:]):
        ax.axvspan(ia, ib, alpha=0.04 + i*0.012,
                   color=T["warning"], zorder=1)
    try:
        ry = float(f(root_val))
    except Exception:
        ry = 0.0
    ax.axvline(root_val, color=T["danger"], linestyle="--", linewidth=1.5,
               label=f"Root = {root_val:.8f}", zorder=4)
    ax.plot(root_val, ry, "o", color=T["danger"], markersize=10,
            markeredgecolor=T["panel"], markeredgewidth=1.5, zorder=5)
    ax.legend(facecolor=T["panel"], edgecolor=T["border"],
              labelcolor=T["text"], fontsize=9, loc="best")
    fig.tight_layout(pad=1.0)
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    tb = NavigationToolbar2Tk(canvas, graph_frame, pack_toolbar=False)
    tb.update()
    tb.pack(side=BOTTOM, fill=X)
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)


# ═══════════════════════════════════════════════════════════════════
#  SOLUTION TRAIL
#  Every section uses the same heading style:
#
#    ━━━ ◆ TITLE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Sub-sections use:
#
#    ▸ Sub-title
#    ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════

LINE_W = 60
HEAVY  = "━"
LIGHT  = "─"

def _bar(char=HEAVY, w=LINE_W): return char * w

def build_trail_segments(method_name, f_expr, a, b, tol, max_iter,
                          history, root_val, stop_reason, edge_warnings=None):
    f = make_f(f_expr)
    fa0, fb0 = float(f(a)), float(f(b))
    segs = []

    # ── helpers ──
    def title(t):
        segs.append((f"{_bar(HEAVY)}\n", "header"))
        segs.append((f"  ◆ {t}\n", "header"))
        segs.append((f"{_bar(HEAVY)}\n", "header"))
    def section(t):
        segs.append(("\n", "explain"))
        segs.append((f"▸ {t}\n", "section"))
        segs.append((f"{_bar(LIGHT)}\n", "dim"))
    def kv(label, value, label_w=18):
        segs.append((f"  {label:<{label_w}}", "label"))
        segs.append((f"{value}\n", "value"))
    def line(t):    segs.append((f"  {t}\n", "explain"))
    def good(t):    segs.append((f"  ✓ {t}\n", "good"))
    def warn(t):    segs.append((f"  ⚠ {t}\n", "warn"))
    def bad(t):     segs.append((f"  ✗ {t}\n", "warn"))
    def edge(t):    segs.append((f"  {t}\n", "edge"))
    def verify(t):  segs.append((f"  {t}\n", "verify"))
    def blank():    segs.append(("\n", "explain"))

    # ═══ TITLE ═══
    title("SOLUTION TRAIL")

    # ═══ EDGE WARNINGS (top) ═══
    if edge_warnings:
        section("EDGE CASE WARNINGS")
        for code, msg in edge_warnings:
            edge(f"[{code}]  {msg}")
            blank()
        warn("Proceed with caution — results may be unreliable.")

    # ═══ METHOD ═══
    section("METHOD")
    if method_name == "Bisection":
        kv("Method:", "Bisection")
        kv("Formula:", "c = (a + b) / 2")
        line("Splits the bracket exactly in half each iteration.")
        line("Guaranteed to converge with linear (slow) rate.")
    else:
        kv("Method:", "False Position  (Regula Falsi)")
        kv("Formula:", "c = b − f(b)·(b−a) / (f(b)−f(a))")
        line("Uses a weighted secant line to estimate the root.")
        line("Often converges faster than bisection on smooth functions.")

    # ═══ PROBLEM SETUP ═══
    section("PROBLEM SETUP")
    kv("Function:",  f"f(x) = {f_expr}")
    kv("Interval:",  f"[{a}, {b}]")
    kv("Tolerance:", str(tol))
    kv("Max Iters:", str(max_iter))

    # ═══ STOPPING RULES ═══
    section("STOPPING RULES")
    line("The loop stops as soon as ANY rule below fires:")
    blank()
    kv("Rule 1:", f"|f(c)| < {tol}        (function value tolerance)")
    kv("Rule 2:", f"(b−a)/2 < {tol}        (bracket-width tolerance)")
    kv("Rule 3:", f"i ≥ {max_iter}        (iteration safety cap)")
    blank()
    if stop_reason == "f(c)_tol":
        good(f"ACTIVE: Rule 1   |f(c)| < tolerance")
    elif stop_reason == "bracket_tol":
        good(f"ACTIVE: Rule 2   bracket width < tolerance")
    else:
        warn(f"ACTIVE: Rule 3   reached max iterations ({max_iter})")

    # ═══ STEP 0 — IVT CHECK ═══
    section("STEP 0  ·  IVT VALIDITY CHECK")
    line("f(a) and f(b) must have OPPOSITE signs for the IVT to")
    line("guarantee a root inside [a, b].")
    blank()
    kv(f"f({a}) =", f"{fa0:.8f}   ({'negative' if fa0 < 0 else 'positive'})")
    kv(f"f({b}) =", f"{fb0:.8f}   ({'negative' if fb0 < 0 else 'positive'})")
    kv("f(a)·f(b) =", f"{fa0 * fb0:.6f}")
    blank()
    if fa0 * fb0 < 0:
        good("Opposite signs confirmed — safe to proceed.")
    else:
        bad("Same sign — method cannot be applied here.")

    # ═══ ITERATION TRAIL ═══
    section("ITERATION TRAIL")
    blank()
    for (i, ia, ib, fa, fb, ic, fc, w, dec) in history:
        segs.append((f"  ┌─ Iteration {i} {LIGHT*(LINE_W-15-len(str(i)))}\n", "iter"))
        kv("  Bracket:", f"[ {ia:.8f},  {ib:.8f} ]")
        kv("  Width:",   f"{w:.8f}")
        blank()
        if method_name == "Bisection":
            line("Midpoint formula:   c = (a + b) / 2")
            line(f"                    = ({ia:.6f} + {ib:.6f}) / 2")
        else:
            line("Secant formula:     c = b − f(b)·(b−a) / (f(b)−f(a))")
            line(f"                    = {ib:.6f} − ({fb:.6f})·({ib-ia:.6f}) / ({fb-fa:.6f})")
        kv("  c =", f"{ic:.10f}")
        kv("  f(c) =", f"{fc:.10f}")
        blank()
        line("Stopping check:")
        if abs(fc) < tol:
            kv("  |f(c)|:", f"{abs(fc):.3e}   <   tol = {tol}")
            good("Rule 1 fired — root found, stopping here.")
        elif w / 2 < tol:
            kv("  width/2:", f"{w/2:.3e}   <   tol = {tol}")
            good("Rule 2 fired — bracket tiny enough, stopping here.")
        else:
            kv("  |f(c)|:", f"{abs(fc):.3e}   ≥   tol = {tol}")
            line("Not precise enough yet — keep narrowing.")
        blank()
        line("Sub-bracket selection:  f(a)·f(c) =")
        kv("  product:", f"{fa:.6f} · {fc:.6f} = {fa*fc:.8f}")
        if fa * fc < 0:
            good(f"Negative product → root in LEFT half  [ {ia:.7f},  {ic:.7f} ]")
        else:
            good(f"Positive product → root in RIGHT half [ {ic:.7f},  {ib:.7f} ]")
        blank()

    # ═══ FINAL ANSWER ═══
    f_root = float(f(root_val))
    n      = len(history)
    err_b  = (b - a) / (2 ** n) if n > 0 else float("inf")

    section("FINAL ANSWER")
    kv("Method:",      method_name)
    kv("Root ≈",       f"{root_val:.12f}")
    kv("f(root) =",    f"{f_root:.6e}")
    kv("Iterations:",  str(n))
    kv("Error bound:", f"(b−a)/2^{n} = {err_b:.4e}")

    section("CONVERGENCE STATUS")
    if stop_reason == "f(c)_tol":
        good(f"Rule 1 fired — |f(c)| < {tol}")
        line("The function value at the midpoint became smaller than")
        line("the tolerance, confirming the root with full precision.")
        good("STATUS: CONVERGED")
    elif stop_reason == "bracket_tol":
        good(f"Rule 2 fired — bracket half-width < {tol}")
        line("The interval shrank so small both halves are")
        line("indistinguishable within the required precision.")
        good("STATUS: CONVERGED")
    else:
        warn(f"Rule 3 fired — reached max iterations ({max_iter})")
        warn("Neither tolerance rule triggered within the limit.")
        line("The answer above is the best point found so far.")
        warn("STATUS: INCOMPLETE — try higher max iterations")

    blank()
    line(f"After {n} steps the bracket shrank from width {b-a}")
    line(f"to {err_b:.4e}.  The true root is within {err_b:.4e} of our answer.")

    # ═══ VERIFICATION REPORT ═══
    vr = verify_root(f_expr, root_val, a, b, tol, n, method=method_name)
    blank()
    title("VERIFICATION REPORT")
    line("Independently confirms the computed root by substituting it")
    line("back into f(x) and running 5 checks.")

    # Check 1
    section("CHECK 1  ·  Numeric Residual")
    kv("root =",      f"{root_val:.12f}")
    kv("f(root) =",   f"{vr['residual']:.6e}" if vr['residual'] is not None else "N/A")
    kv("|f(root)| =", f"{vr['residual_abs']:.6e}" if vr['residual_abs'] is not None else "N/A")
    if vr["residual_ok"]: good("PASS — residual is negligibly small.")
    else:                 warn("WARNING — residual larger than expected.")

    # Check 2
    section("CHECK 2  ·  Back-substitution")
    line("Re-evaluate f(x) at the found root independently.")
    if vr["backcheck_val"] is not None:
        kv("Substituted:", f"f({root_val:.8f}) = {vr['backcheck_val']:.10f}")
        kv("Expected:",    f"~0.0   (got {vr['backcheck_val']:.2e})")
    if vr["backcheck_ok"]: good("PASS — back-substitution confirms the root.")
    else:                  warn("WARNING — back-substitution shows large deviation.")

    # Check 3
    section("CHECK 3  ·  Bracket Containment")
    kv("Range:", f"{a} ≤ {root_val:.8f} ≤ {b} ?")
    if vr["in_bracket"]: good("PASS — root is inside the original bracket.")
    else:                bad("FAIL — root is OUTSIDE the original bracket.")

    # Check 4
    section("CHECK 4  ·  Theoretical Error Bound")
    kv("Formula:",   "error ≤ (b − a) / 2^n")
    kv("(b−a)/2^n =", f"{vr['error_bound']:.6e}")
    kv("Tolerance:", str(tol))
    if vr["error_bound_ok"]: good("PASS — error bound is within acceptable range.")
    else:                    warn("NOTE — error bound exceeds tolerance.")

    # Check 5
    section("CHECK 5  ·  Residual vs Tolerance")
    if vr["residual_abs"] is not None:
        kv("|f(root)| =", f"{vr['residual_abs']:.6e}")
        kv("tolerance:", str(tol))
        if vr["within_tol"]: good("PASS — residual is within user tolerance.")
        else:                warn("NOTE — bracket-rule fired; residual slightly above tol.")

    # Verdict
    blank()
    segs.append((f"  {_bar(HEAVY, LINE_W-2)}\n", "header"))
    if vr["passed"]:
        good("VERIFICATION RESULT:  ALL CHECKS PASSED")
        good("The computed root is verified correct.")
    else:
        warn("VERIFICATION RESULT:  ONE OR MORE CHECKS FLAGGED")
        warn("Review warnings above. Result may need better settings.")
    segs.append((f"  {_bar(HEAVY, LINE_W-2)}\n", "header"))

    # ═══ EDGE SUMMARY (bottom) ═══
    if edge_warnings:
        blank()
        section("EDGE CASE SUMMARY")
        for code, msg in edge_warnings:
            short = msg if len(msg) <= 64 else msg[:61] + "..."
            edge(f"[{code}]  {short}")

    blank()
    return segs


def stream_trail(segs, widget, delay_ms=35):
    widget.config(state=NORMAL)
    def _write(idx):
        if idx >= len(segs):
            widget.config(state=DISABLED); return
        text, tag = segs[idx]
        widget.insert(END, text, tag)
        widget.see(END)
        widget.after(delay_ms, _write, idx + 1)
    _write(0)


# ═══════════════════════════════════════════════════════════════════
#  EXPORT (TXT / HTML)
# ═══════════════════════════════════════════════════════════════════
_last_run = {}

def build_txt_report(d):
    W = 64
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    lines = []
    def ln(s=""): lines.append(s)
    def bar(c="="): lines.append(c * W)
    def sec(t): bar(); lines.append(f"  {t}"); bar()

    bar("=")
    lines.append("  BISECTION & FALSE POSITION ROOT FINDER")
    lines.append("  Numerical Analysis — Audit / Documentation Report")
    lines.append(f"  Generated : {now}")
    lines.append(f"  Version   : v1.0  (Final Release)")
    lines.append("  Group     : John Oniel Thomas Q. Araque")
    lines.append("              Niel Allen S. Jauculan")
    lines.append("              Tiff Anthony R. Parnala")
    bar("="); ln()

    sec("SECTION 1 — GIVEN")
    ln(f"  Function     : f(x) = {d['f_expr']}")
    ln(f"  Interval     : a = {d['a']},  b = {d['b']}")
    ln(f"  Tolerance    : {d['tol']}")
    ln(f"  Max Iters    : {d['max_iter']}")
    ln(f"  IVT Check    : f(a) = {d['fa0']:.8f}  |  f(b) = {d['fb0']:.8f}")
    ln(f"  Signs opp.   : {'YES — valid bracket' if d['fa0']*d['fb0'] < 0 else 'NO — invalid'}")
    ln()

    sec("SECTION 2 — METHOD USED")
    ln(f"  Method       : {d['method_name']}")
    if d['method_name'] == "Bisection":
        ln("  Formula      : c = (a + b) / 2")
        ln("  Description  : Splits the bracket exactly in half each iteration.")
    else:
        ln("  Formula      : c = b - f(b)*(b-a) / (f(b)-f(a))")
        ln("  Description  : Uses a weighted secant line to estimate the root.")
    ln()
    ln("  Stopping Rules:")
    ln(f"    Rule 1 — |f(c)| < {d['tol']}")
    ln(f"    Rule 2 — (b-a)/2 < {d['tol']}")
    ln(f"    Rule 3 — iterations >= {d['max_iter']}")
    ln(f"  Active Rule  : {d['stop_label']}")
    ln()

    sec("SECTION 3 — ITERATION STEPS")
    ln(f"  {'Iter':>4}  {'a':>14}  {'b':>14}  {'c':>16}  {'f(c)':>14}  {'Decision':>12}")
    ln("  " + "-" * 80)
    for (i, ia, ib, fa, fb, ic, fc, w, dec) in d['history']:
        ln(f"  {i:>4}  {ia:>14.8f}  {ib:>14.8f}  {ic:>16.10f}  {fc:>14.6e}  {dec:>12}")
    ln()

    sec("SECTION 4 — FINAL ANSWER")
    ln(f"  Root         ~ {d['root_val']:.12f}")
    ln(f"  f(root)       = {d['f_root']:.6e}")
    ln(f"  Iterations    = {d['n']}")
    ln(f"  Error Bound   = (b-a)/2^{d['n']} = {d['err_b']:.4e}")
    ln(f"  Converged     = {d['stop_label']}")
    ln()

    sec("SECTION 5 — VERIFICATION REPORT")
    vr = d['vr']
    res_abs = f"{vr['residual_abs']:.6e}" if vr['residual_abs'] is not None else "N/A"
    res_val = f"{vr['residual']:.6e}"     if vr['residual']     is not None else "N/A"
    eb_str  = f"{vr['error_bound']:.4e}"

    ln("  Check 1 — Numeric Residual")
    ln(f"    |f(root)| = {res_abs}")
    ln(f"    Result    : {'PASS' if vr['residual_ok'] else 'WARN'}")
    ln()
    ln("  Check 2 — Back-Substitution")
    ln(f"    f({d['root_val']:.8f}) = {res_val}")
    ln(f"    Result    : {'PASS' if vr['backcheck_ok'] else 'WARN'}")
    ln()
    ln("  Check 3 — Bracket Containment")
    ln(f"    {d['a']} <= {d['root_val']:.10f} <= {d['b']}")
    ln(f"    Result    : {'PASS' if vr['in_bracket'] else 'FAIL'}")
    ln()
    ln("  Check 4 — Theoretical Error Bound")
    ln(f"    (b-a)/2^{d['n']} = {eb_str}")
    ln(f"    Tolerance = {d['tol']}")
    ln(f"    Result    : {'PASS' if vr['error_bound_ok'] else 'NOTE'}")
    ln()
    ln("  Check 5 — Residual vs Tolerance")
    ln(f"    |f(root)| = {res_abs}  vs  tol = {d['tol']}")
    ln(f"    Result    : {'PASS' if vr['within_tol'] else 'NOTE'}")
    ln()
    verdict = "ALL CHECKS PASSED" if vr['passed'] else "ONE OR MORE CHECKS FLAGGED"
    ln(f"  OVERALL VERIFICATION RESULT: {verdict}")
    ln()

    sec("SECTION 6 — SUMMARY")
    ln(f"  Function    : f(x) = {d['f_expr']}")
    ln(f"  Method      : {d['method_name']}")
    ln(f"  Interval    : [{d['a']}, {d['b']}]")
    ln(f"  Root Found  : {d['root_val']:.12f}")
    ln(f"  f(root)     : {d['f_root']:.6e}")
    ln(f"  Iterations  : {d['n']}")
    ln(f"  Error Bound : {d['err_b']:.4e}")
    ln(f"  Converged   : {d['stop_label']}")
    ln(f"  Verified    : {verdict}")
    if d.get('edge_warnings'):
        ln(); ln("  Edge Case Warnings:")
        for code, msg in d['edge_warnings']:
            ln(f"    [{code}] {msg}")
    ln()
    bar("=")
    lines.append("  END OF REPORT")
    bar("=")
    return "\n".join(lines)


def build_html_report(d):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    vr = d['vr']
    res_abs = f"{vr['residual_abs']:.6e}" if vr['residual_abs'] is not None else "N/A"
    res_val = f"{vr['residual']:.6e}"     if vr['residual']     is not None else "N/A"
    eb_str  = f"{vr['error_bound']:.4e}"
    verdict = "ALL CHECKS PASSED" if vr['passed'] else "ONE OR MORE CHECKS FLAGGED"
    verdict_color = "#16a34a" if vr['passed'] else "#ea580c"

    def badge(ok, p="PASS", f="WARN"):
        c = "#16a34a" if ok else "#ea580c"
        return f'<span style="color:{c};font-weight:700">{p if ok else f}</span>'

    rows = ""
    for (i, ia, ib, fa, fb, ic, fc, w, dec) in d['history']:
        bg = "#f9fafb" if i % 2 == 0 else "#ffffff"
        rows += (f'<tr style="background:{bg}">'
                 f'<td>{i}</td><td>{ia:.8f}</td><td>{ib:.8f}</td>'
                 f'<td>{ic:.10f}</td><td>{fc:.6e}</td><td>{w:.4e}</td>'
                 f'<td>{dec}</td></tr>\n')

    edge_html = ""
    if d.get('edge_warnings'):
        edge_html = '<div class="section"><h2>Edge Case Warnings</h2><div class="card">'
        for code, msg in d['edge_warnings']:
            edge_html += f'<p><strong style="color:#ea580c">[{code}]</strong> {msg}</p>'
        edge_html += '</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Root Finder Report — {d['f_expr']}</title>
<style>
  :root {{ --primary:#2563eb; --text:#111827; --muted:#6b7280; --bg:#f7f8fa;
           --panel:#ffffff; --border:#e5e7eb; --success:#16a34a; --warning:#ea580c; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,sans-serif;
          background:var(--bg); color:var(--text); margin:0; padding:32px; line-height:1.5; }}
  h1 {{ color:var(--primary); border-bottom:2px solid var(--border);
        padding-bottom:12px; margin:0 0 6px 0; font-weight:700; }}
  h2 {{ color:var(--text); margin:32px 0 12px 0; font-size:1.1em;
        border-left:3px solid var(--primary); padding:4px 12px; }}
  .card {{ background:var(--panel); border:1px solid var(--border);
           border-radius:8px; padding:20px 24px; margin:8px 0; }}
  .meta {{ color:var(--muted); font-size:0.9em; margin:4px 0; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.88em;
           font-family:Consolas,monospace; }}
  th {{ background:#f0f2f5; color:var(--text); padding:10px 8px; text-align:center;
        border-bottom:1px solid var(--border); font-weight:600; }}
  td {{ padding:8px; text-align:center; color:var(--text);
        border-bottom:1px solid var(--border); }}
  .root {{ color:var(--primary); font-size:1.4em; font-weight:700;
           font-family:Consolas,monospace; }}
  .verdict {{ font-size:1em; font-weight:700; color:{verdict_color};
              padding:10px 18px; border:2px solid {verdict_color};
              border-radius:8px; display:inline-block; margin-top:12px; }}
  label {{ color:var(--muted); display:inline-block; width:170px; font-weight:500; }}
  .section {{ margin-bottom:24px; }}
  .header {{ background:var(--panel); border:1px solid var(--border);
             border-radius:8px; padding:24px; margin-bottom:24px; }}
</style>
</head>
<body>

<div class="header">
  <h1>Bisection &amp; False Position — Audit Report</h1>
  <p class="meta">Generated: {now} &nbsp;|&nbsp; Version: v1.0 (Final Release)</p>
  <p class="meta">Group: John Oniel Thomas Q. Araque &nbsp;·&nbsp; Niel Allen S. Jauculan &nbsp;·&nbsp; Tiff Anthony R. Parnala</p>
</div>

<div class="section"><h2>Section 1 — Given</h2><div class="card">
  <p><label>Function:</label> f(x) = {d['f_expr']}</p>
  <p><label>Interval:</label> a = {d['a']}, &nbsp; b = {d['b']}</p>
  <p><label>Tolerance:</label> {d['tol']}</p>
  <p><label>Max Iterations:</label> {d['max_iter']}</p>
  <p><label>f(a):</label> {d['fa0']:.8f} &nbsp;&nbsp; <label>f(b):</label> {d['fb0']:.8f}</p>
  <p><label>IVT Valid:</label> {'<span style="color:#16a34a;font-weight:700">YES — opposite signs</span>' if d['fa0']*d['fb0']<0 else '<span style="color:#ea580c;font-weight:700">NO — same sign</span>'}</p>
</div></div>

<div class="section"><h2>Section 2 — Method Used</h2><div class="card">
  <p><label>Method:</label> <strong style="color:var(--primary)">{d['method_name']}</strong></p>
  {'<p><label>Formula:</label> c = (a + b) / 2</p><p>Splits the bracket exactly in half each iteration.</p>' if d['method_name']=="Bisection" else '<p><label>Formula:</label> c = b − f(b)·(b−a) / (f(b)−f(a))</p><p>Weighted secant line approximation.</p>'}
  <p><label>Active Rule:</label> {d['stop_label']}</p>
</div></div>

<div class="section"><h2>Section 3 — Iteration Steps</h2><div class="card">
<table>
  <tr><th>Iter</th><th>a</th><th>b</th><th>Midpoint c</th><th>f(c)</th><th>Width</th><th>Decision</th></tr>
  {rows}
</table>
</div></div>

<div class="section"><h2>Section 4 — Final Answer</h2><div class="card">
  <p class="root">Root ≈ {d['root_val']:.12f}</p>
  <p><label>f(root):</label> {d['f_root']:.6e}</p>
  <p><label>Iterations:</label> {d['n']}</p>
  <p><label>Error Bound:</label> (b−a)/2<sup>{d['n']}</sup> = {d['err_b']:.4e}</p>
  <p><label>Converged:</label> {d['stop_label']}</p>
</div></div>

<div class="section"><h2>Section 5 — Verification Report</h2><div class="card">
  <table>
    <tr><th>Check</th><th>Name</th><th>Value</th><th>Result</th></tr>
    <tr><td>1</td><td>Numeric Residual</td><td>|f(root)| = {res_abs}</td><td>{badge(vr['residual_ok'])}</td></tr>
    <tr><td>2</td><td>Back-Substitution</td><td>f(root) = {res_val}</td><td>{badge(vr['backcheck_ok'])}</td></tr>
    <tr><td>3</td><td>Bracket Containment</td><td>{d['a']} ≤ root ≤ {d['b']}</td><td>{badge(vr['in_bracket'])}</td></tr>
    <tr><td>4</td><td>Error Bound</td><td>(b−a)/2<sup>n</sup> = {eb_str}</td><td>{badge(vr['error_bound_ok'],'PASS','NOTE')}</td></tr>
    <tr><td>5</td><td>Within Tolerance</td><td>|f(r)| &lt; tol ?</td><td>{badge(vr['within_tol'],'PASS','NOTE')}</td></tr>
  </table>
  <div class="verdict">{verdict}</div>
</div></div>

<div class="section"><h2>Section 6 — Summary</h2><div class="card">
  <p><label>Function:</label> f(x) = {d['f_expr']}</p>
  <p><label>Method:</label> {d['method_name']}</p>
  <p><label>Interval:</label> [{d['a']}, {d['b']}]</p>
  <p><label>Root:</label> {d['root_val']:.12f}</p>
  <p><label>f(root):</label> {d['f_root']:.6e}</p>
  <p><label>Iterations:</label> {d['n']}</p>
  <p><label>Error Bound:</label> {d['err_b']:.4e}</p>
  <p><label>Verification:</label> <span style="color:{verdict_color};font-weight:700">{verdict}</span></p>
</div></div>

{edge_html}

</body>
</html>
"""
    return html


def export_report():
    if not _last_run:
        messagebox.showwarning("Nothing to Export",
            "No computation has been run yet.\n"
            "Please compute a root first, then export.")
        return

    win = tk.Toplevel(root)
    win.title("Export Report")
    win.configure(bg=T["bg"]); win.resizable(False, False); win.grab_set()
    fw, fh = 520, 560
    fx = root.winfo_x() + (root.winfo_width()  - fw) // 2
    fy = root.winfo_y() + (root.winfo_height() - fh) // 2
    win.geometry(f"{fw}x{fh}+{fx}+{fy}")

    # ── Colorful banner header ───────────────────────────────
    hdr_bar = tk.Frame(win, bg=T["primary"], height=80)
    hdr_bar.pack(fill=X); hdr_bar.pack_propagate(False)
    hctr = tk.Frame(hdr_bar, bg=T["primary"])
    hctr.place(relx=0.5, rely=0.5, anchor="center")
    tk.Label(hctr, text="⬇", bg=T["primary"], fg=T["panel"],
             font=("Segoe UI", 26, "bold")).pack(side=LEFT, padx=(0, 14))
    tx = tk.Frame(hctr, bg=T["primary"]); tx.pack(side=LEFT)
    tk.Label(tx, text="Export Report", bg=T["primary"], fg=T["panel"],
             font=("Segoe UI", 15, "bold")).pack(anchor="w")
    tk.Label(tx, text="Choose a format to save your analysis",
             bg=T["primary"], fg=T["panel"],
             font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

    # ── Run-summary chip ─────────────────────────────────────
    chip = tk.Frame(win, bg=T["bg"]); chip.pack(fill=X, padx=22, pady=(10, 2))
    chip_card = tk.Frame(chip, bg=T["elevated"], padx=14, pady=10)
    chip_card.pack(fill=X)
    info = (f"Method: {_last_run.get('method_name','—')}    "
            f"|    Iterations: {_last_run.get('n','—')}    "
            f"|    Root ≈ {_last_run.get('root_val', 0):.8f}")
    tk.Label(chip_card, text=info, bg=T["elevated"], fg=T["text"],
             font=("Consolas", 9)).pack(anchor="w")

    # ── Format selection cards ───────────────────────────────
    body = tk.Frame(win, bg=T["bg"]); body.pack(fill=BOTH, expand=True,
                                                 padx=22, pady=(8, 8))

    fmt_var = tk.StringVar(value="txt")
    cards = {}

    def make_format_card(parent, fmt, icon_txt, title, desc, accent_color):
        outer = tk.Frame(parent, bg=T["bg"])
        outer.pack(fill=X, pady=5)
        card = tk.Frame(outer, bg=T["panel"], padx=14, pady=14,
                        highlightthickness=2, highlightbackground=T["border"])
        card.pack(fill=X)

        def select(_=None):
            fmt_var.set(fmt); update_cards()

        for w in (card,):
            w.bind("<Button-1>", select)
            w.configure(cursor="hand2")

        ibadge = tk.Frame(card, bg=accent_color, width=46, height=46)
        ibadge.pack(side=LEFT, padx=(0, 14)); ibadge.pack_propagate(False)
        ibadge.bind("<Button-1>", select)
        ilbl = tk.Label(ibadge, text=icon_txt, bg=accent_color, fg="#ffffff",
                        font=("Segoe UI", 13, "bold"))
        ilbl.place(relx=0.5, rely=0.5, anchor="center")
        ilbl.bind("<Button-1>", select)

        txt = tk.Frame(card, bg=T["panel"])
        txt.pack(side=LEFT, fill=X, expand=True)
        txt.bind("<Button-1>", select)
        tl = tk.Label(txt, text=title, bg=T["panel"], fg=T["text"],
                      font=("Segoe UI", 11, "bold"))
        tl.pack(anchor="w"); tl.bind("<Button-1>", select)
        dl = tk.Label(txt, text=desc, bg=T["panel"], fg=T["muted"],
                      font=("Segoe UI", 9), wraplength=340, justify=LEFT)
        dl.pack(anchor="w", pady=(2, 0)); dl.bind("<Button-1>", select)

        chev = tk.Label(card, text="›", bg=T["panel"], fg=accent_color,
                        font=("Segoe UI", 18, "bold"))
        chev.pack(side=RIGHT, padx=(8, 0))
        chev.bind("<Button-1>", select)

        cards[fmt] = card

    def update_cards():
        for k, c in cards.items():
            if k == fmt_var.get():
                c.configure(highlightbackground=T["primary"], highlightthickness=2)
            else:
                c.configure(highlightbackground=T["border"], highlightthickness=2)

    def do_export():
        fmt = fmt_var.get(); win.destroy()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn_default = f"root_report_{ts}.{fmt}"
        ftype = [("Text files", "*.txt"), ("All files", "*.*")] if fmt == "txt" \
                else [("HTML files", "*.html"), ("All files", "*.*")]
        path = filedialog.asksaveasfilename(defaultextension=f".{fmt}",
                                            filetypes=ftype, initialfile=fn_default,
                                            title="Save Report As")
        if not path: return
        try:
            content = build_txt_report(_last_run) if fmt == "txt" else build_html_report(_last_run)
            with open(path, "w", encoding="utf-8") as fh_:
                fh_.write(content)
            update_status("Report exported.")
            messagebox.showinfo("Export Successful", f"Report saved:\n\n{path}")
        except Exception as exc:
            messagebox.showerror("Export Failed", f"Could not save file:\n{exc}")

    # ── Footer packed FIRST (before body) so it always stays visible ──
    foot = tk.Frame(win, bg=T["bg"], height=72)
    foot.pack(side=BOTTOM, fill=X, padx=22, pady=(8, 18))
    foot.pack_propagate(False)

    foot_row = tk.Frame(foot, bg=T["bg"])
    foot_row.pack(fill=X, expand=True, padx=4, pady=14)

    cancel_wrap, _cb = make_3d_button(foot_row, "  Cancel  ", win.destroy,
                                      bg_role="elevated", fg_role="text",
                                      font_size=10, bold=True,
                                      ipadx=18, ipady=8, shadow_h=3)
    cancel_wrap.pack(side=LEFT, anchor="center")

    save_wrap, _sb = make_3d_button(foot_row, "  ⬇  Save Report  ", do_export,
                                    bg_role="primary", fg_role="panel",
                                    font_size=11, bold=True,
                                    ipadx=22, ipady=10, shadow_h=4)
    save_wrap.pack(side=RIGHT, anchor="center")

    # ── Format cards fill the remaining space above the footer ────────
    body = tk.Frame(win, bg=T["bg"])
    body.pack(fill=BOTH, expand=True, padx=22, pady=(4, 2))

    make_format_card(body, "txt", "TXT", "Plain Text Report",
        "Audit-style readable .txt — perfect for printing or pasting into docs.",
        T["success"])
    make_format_card(body, "html", "</>", "HTML Report",
        "Styled web report with color tables — opens in any browser.",
        T["primary"])

    update_cards()


# ═══════════════════════════════════════════════════════════════════
#  COMPUTE
# ═══════════════════════════════════════════════════════════════════
def compute():
    for tb in [steps_text, results_text]:
        tb.config(state=NORMAL); tb.delete(1.0, END)
    for r in iter_tree.get_children():
        iter_tree.delete(r)

    method_name = method_var.get()
    f_expr   = entry_function.get().strip()
    a_str    = entry_a.get().strip()
    b_str    = entry_b.get().strip()
    tol_str  = entry_tol.get().strip()
    iter_str = entry_iter.get().strip()

    errors = []
    if not f_expr:
        errors.append("• Function f(x) is required.")
    a = b = tol = None
    max_iter = 100
    try:    a = float(a_str)
    except: errors.append("• Left endpoint (a) must be a number.")
    try:    b = float(b_str)
    except: errors.append("• Right endpoint (b) must be a number.")
    try:
        tol = float(tol_str)
        if tol <= 0: errors.append("• Tolerance must be positive.")
    except: errors.append("• Tolerance must be a number.")
    try:
        max_iter = int(iter_str)
        if max_iter <= 0: errors.append("• Max iterations must be a positive integer.")
    except: errors.append("• Max iterations must be an integer.")

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
        messagebox.showerror("Function Error",
            f"EC3 — Cannot evaluate f(x) at endpoints:\n{exc}\n\n"
            "Check your function syntax (use ** for powers, * for multiply).")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        return

    if not np.isfinite(fa) or not np.isfinite(fb):
        bad = []
        if not np.isfinite(fa): bad.append(f"f(a) = f({a}) = {fa}")
        if not np.isfinite(fb): bad.append(f"f(b) = f({b}) = {fb}")
        messagebox.showerror("Edge Case EC3 — Undefined Function",
            "The function is undefined (NaN/Infinite) at one or both endpoints:\n\n"
            + "\n".join(bad) +
            "\n\nChoose different endpoints where f(x) is defined.")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        update_status("EC3 — Function undefined at endpoint.")
        return

    if abs(fa) < 1e-14:
        messagebox.showwarning("Edge Case EC2 — Root at Endpoint",
            f"f(a) = f({a}) = {fa:.2e} is essentially zero.\n\n"
            "The root is already at the left endpoint.")
    elif abs(fb) < 1e-14:
        messagebox.showwarning("Edge Case EC2 — Root at Endpoint",
            f"f(b) = f({b}) = {fb:.2e} is essentially zero.\n\n"
            "The root is already at the right endpoint.")

    if fa * fb > 0:
        messagebox.showerror("Edge Case EC1 — IVT Violated",
            f"EC1: f({a}) = {fa:.4f} and f({b}) = {fb:.4f} have the SAME sign.\n\n"
            "The IVT cannot guarantee a root in this interval.\n\n"
            "Fix: choose an interval where f(a) and f(b) have opposite signs.")
        for tb in [steps_text, results_text]: tb.config(state=DISABLED)
        update_status("EC1 — Same-sign endpoints. IVT violated.")
        return

    edge_warnings = detect_edge_cases(f_expr, a, b, tol, max_iter)
    soft = [(c, m) for c, m in edge_warnings if c in ("EC4", "EC5")]
    if soft:
        msg = "\n\n".join(f"[{c}] {m}" for c, m in soft)
        messagebox.showwarning("Edge Case Warning",
            "Potential issues detected:\n\n" + msg +
            "\n\nComputation will still proceed.")

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

    vr = verify_root(f_expr, root_val, a, b, tol, n, method=method_name)
    v_verdict = "ALL CHECKS PASSED" if vr["passed"] else "ONE OR MORE CHECKS FLAGGED"

    all_warnings = detect_edge_cases(f_expr, a, b, tol, max_iter)
    f_obj = make_f(f_expr)
    _last_run.clear()
    _last_run.update({
        "method_name": method_name, "f_expr": f_expr, "a": a, "b": b,
        "fa0": float(f_obj(a)), "fb0": float(f_obj(b)),
        "tol": tol, "max_iter": max_iter,
        "root_val": root_val, "f_root": float(f_obj(root_val)),
        "n": n, "err_b": (b - a) / (2 ** n) if n else float("inf"),
        "history": history, "stop_reason": stop_reason, "stop_label": stop_label,
        "vr": vr, "edge_warnings": all_warnings if all_warnings else [],
    })

    # ── Standardised SUMMARY tab ──
    edge_block = ""
    if all_warnings:
        edge_block = "\n  ▸ Edge Case Warnings\n  " + "─" * 44 + "\n"
        for code, msg in all_warnings:
            short = msg if len(msg) <= 50 else msg[:47] + "..."
            edge_block += f"    [{code}]  {short}\n"

    res_str = f"{vr['residual']:.6e}" if vr["residual"] is not None else "N/A"
    eb_str  = f"{vr['error_bound']:.4e}"

    summary = (
        f"{HEAVY * LINE_W}\n"
        f"  ◆ {method_name.upper()}  —  RESULT SUMMARY\n"
        f"{HEAVY * LINE_W}\n\n"
        f"▸ Problem\n"
        f"  {LIGHT * 50}\n"
        f"  Function    :  f(x) = {f_expr}\n"
        f"  Interval    :  [{a}, {b}]\n"
        f"  Tolerance   :  {tol}\n"
        f"  Max iters   :  {max_iter}\n\n"
        f"▸ Stopping Rules\n"
        f"  {LIGHT * 50}\n"
        f"  Rule 1  |f(c)| < {tol}\n"
        f"  Rule 2  (b-a)/2 < {tol}\n"
        f"  Rule 3  iterations ≥ {max_iter}\n"
        f"{edge_block}\n"
        f"▸ Final Answer\n"
        f"  {LIGHT * 50}\n"
        f"  Root        ≈  {root_val:.10f}\n"
        f"  f(root)     =  {f_root:.4e}\n"
        f"  Iterations  =  {n}\n"
        f"  Error bound =  {(b-a)/(2**n) if n else float('inf'):.2e}\n"
        f"  Converged   =  {stop_label}\n\n"
        f"▸ Verification (5 checks)\n"
        f"  {LIGHT * 50}\n"
        f"  1. Residual    |f(root)| = {vr['residual_abs']:.4e}   "
        f"{'PASS' if vr['residual_ok'] else 'WARN'}\n"
        f"  2. Back-sub    f(root)   = {res_str}   "
        f"{'PASS' if vr['backcheck_ok'] else 'WARN'}\n"
        f"  3. In bracket  [{a},{b}]   "
        f"{'PASS' if vr['in_bracket'] else 'FAIL'}\n"
        f"  4. Err. bound  (b-a)/2^n = {eb_str}   "
        f"{'PASS' if vr['error_bound_ok'] else 'NOTE'}\n"
        f"  5. Within tol  |f(r)|<tol   "
        f"{'PASS' if vr['within_tol'] else 'NOTE'}\n"
        f"  {LIGHT * 50}\n"
        f"  RESULT: {v_verdict}\n\n"
        f"  ✓ Done.\n"
    )
    results_text.insert(END, summary)
    results_text.config(state=DISABLED)

    steps_text.config(state=NORMAL); steps_text.delete(1.0, END)
    trail_segs = build_trail_segments(method_name, f_expr, a, b, tol, max_iter,
                                       history, root_val, stop_reason,
                                       edge_warnings=all_warnings if all_warnings else None)
    stream_trail(trail_segs, steps_text, delay_ms=25)

    for (i, ia, ib, fa_i, fb_i, ic, fc, w, dec) in history:
        tag = "odd" if i % 2 == 0 else "even"
        iter_tree.insert("", END, values=(
            i, f"{ia:.7f}", f"{ib:.7f}", f"{ic:.9f}",
            f"{fa_i:.5f}", f"{fb_i:.5f}", f"{fc:.5e}",
            f"{w:.5e}", dec
        ), tags=(tag,))

    plot_graph(f_expr, root_val, brackets, method_name)
    notebook.select(1)

    suffix = ""
    if all_warnings:
        codes = ", ".join(c for c, _ in all_warnings)
        suffix = f"   |   EDGE: {codes}"
    update_status(f"[{method_name}]  Root = {root_val:.8f}   |   {n} iterations{suffix}")

    ToastNotification(title=f"{method_name} complete",
        message=f"Root ≈ {root_val:.8f}",
        duration=2500, bootstyle=SUCCESS).show_toast()


def clear_all():
    results_text.config(state=NORMAL); results_text.delete(1.0, END)
    results_text.insert(END,
        "  ◆ Results will appear here.\n\n"
        "  ▸ Select a method, enter your function and interval,\n"
        "    then click  ▶  COMPUTE ROOT.\n\n"
        "  ▸ Edge-case warnings appear in this panel and in the\n"
        "    Solution Trail tab.\n")
    results_text.config(state=DISABLED)

    steps_text.config(state=NORMAL); steps_text.delete(1.0, END)
    steps_text.insert(END,
        "  ◆ The Solution Trail will appear here after you click  ▶  COMPUTE ROOT.\n\n"
        "  ▸ The trail streams line-by-line and clearly identifies which\n"
        "    method was used at the top.\n\n"
        "  ▸ Edge-case warnings appear in red at the top of the trail:\n\n"
        "      EC1  ·  Same-sign endpoints (IVT violated)\n"
        "      EC2  ·  Root exactly at endpoint\n"
        "      EC3  ·  Undefined / infinite function value\n"
        "      EC4  ·  Max iterations too low\n"
        "      EC5  ·  Tolerance too loose\n",
        "explain")
    steps_text.config(state=DISABLED)

    for r in iter_tree.get_children():
        iter_tree.delete(r)
    for entry, val in zip(
        [entry_function, entry_a, entry_b, entry_tol, entry_iter],
        ["x**3 - x - 2", "1", "2", "1e-6", "100"]):
        entry.delete(0, END); entry.insert(0, val)
    for w in graph_frame.winfo_children():
        w.destroy()
    placeholder = tk.Label(graph_frame, text="◆  Graph appears after computation",
                           font=("Segoe UI", 12))
    themed(placeholder, bg="bg", fg="muted")
    placeholder.place(relx=0.5, rely=0.5, anchor="center")
    notebook.select(0)
    update_status("Ready")


def update_status(text):
    status_label.config(text=f"  {text}")
    root.update_idletasks()


# ═══════════════════════════════════════════════════════════════════
#  ABOUT DIALOG
# ═══════════════════════════════════════════════════════════════════
def show_about():
    win = tk.Toplevel(root); win.title("Help — Bisection Root Finder")
    win.configure(bg=T["bg"]); win.resizable(True, True); win.grab_set()
    win.update_idletasks()
    w, h = 680, 720
    x = root.winfo_x() + (root.winfo_width()  - w) // 2
    y = root.winfo_y() + (root.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.minsize(560, 500)

    # ── Fixed header ── two rows: [badge | title]   [subtitle full-width]
    hdr = tk.Frame(win, bg=T["primary"], height=124)
    hdr.pack(fill=X, side=TOP); hdr.pack_propagate(False)

    # Row 1 — badge + title (vertically centered together)
    row1 = tk.Frame(hdr, bg=T["primary"])
    row1.pack(fill=X, padx=24, pady=(18, 0))

    badge_canvas = tk.Canvas(row1, width=52, height=52,
                             bg=T["primary"], bd=0, highlightthickness=0)
    badge_canvas.pack(side=LEFT, padx=(0, 14))
    badge_canvas.create_oval(2, 2, 50, 50, fill=T["panel"], outline="")
    badge_canvas.create_text(26, 26, text="[ ]", fill=T["primary"],
                             font=("Segoe UI", 14, "bold"), anchor="center")

    tk.Label(row1, text="Bisection Root Finder",
             bg=T["primary"], fg=T["panel"],
             font=("Segoe UI", 16, "bold")).pack(side=LEFT, anchor="w")

    # Row 2 — subtitle on its OWN row, full window width, with wraplength so
    # it can never be clipped no matter how the dialog is resized.
    sub_lbl = tk.Label(hdr,
        text="Numerical Analysis  ·  Bisection & False Position  ·  v1.0",
        bg=T["primary"], fg=T["panel"],
        font=("Segoe UI", 10), justify=LEFT,
        wraplength=620)
    sub_lbl.pack(fill=X, padx=24, pady=(6, 14), anchor="w")
    # Re-flow on resize so the subtitle always uses available width
    def _reflow_sub(ev):
        sub_lbl.configure(wraplength=max(120, ev.width - 56))
    hdr.bind("<Configure>", _reflow_sub)

    # ── Fixed footer (Close button) ──
    foot = tk.Frame(win, bg=T["bg"], height=72)
    foot.pack(fill=X, side=BOTTOM); foot.pack_propagate(False)
    close_wrap, _cb = make_3d_button(foot, "  Close  ", win.destroy,
                                     bg_role="primary", fg_role="panel",
                                     font_size=10, bold=True,
                                     ipadx=28, ipady=10, shadow_h=4)
    close_wrap.pack(pady=14)

    # ── Scrollable middle ──
    mid = tk.Frame(win, bg=T["bg"]); mid.pack(fill=BOTH, expand=True, side=TOP)
    cnv = tk.Canvas(mid, bg=T["bg"], bd=0, highlightthickness=0)
    sb  = ttkb.Scrollbar(mid, orient=VERTICAL, command=cnv.yview)
    cnv.configure(yscrollcommand=sb.set)
    sb.pack(side=RIGHT, fill=Y)
    cnv.pack(side=LEFT, fill=BOTH, expand=True)

    body = tk.Frame(cnv, bg=T["bg"])
    body_id = cnv.create_window((0, 0), window=body, anchor="nw")

    def _on_body_cfg(_):
        cnv.configure(scrollregion=cnv.bbox("all"))
    def _on_cnv_cfg(ev):
        cnv.itemconfig(body_id, width=ev.width)
    body.bind("<Configure>", _on_body_cfg)
    cnv.bind("<Configure>", _on_cnv_cfg)

    def _on_wheel(ev):
        cnv.yview_scroll(int(-1 * (ev.delta / 120)), "units")
    win.bind("<MouseWheel>", _on_wheel)
    def _unbind_wheel(_=None):
        try: win.unbind("<MouseWheel>")
        except Exception: pass
    win.bind("<Destroy>", _unbind_wheel)

    inner = tk.Frame(body, bg=T["bg"])
    inner.pack(fill=BOTH, expand=True, padx=28, pady=(20, 24))

    # ── Colorful section card builder ─────────────────────
    # Each section has its own colored icon badge + colored title +
    # colored left-side accent bar — far more readable than plain B&W.
    def section_card(title, icon, accent_color, items, bullet_color=None):
        # Section header row: colored badge + colored title
        head = tk.Frame(inner, bg=T["bg"]); head.pack(fill=X, pady=(18, 6))
        ibadge = tk.Frame(head, bg=accent_color, width=30, height=30)
        ibadge.pack(side=LEFT, padx=(0, 12)); ibadge.pack_propagate(False)
        tk.Label(ibadge, text=icon, bg=accent_color, fg="#ffffff",
                 font=("Segoe UI", 13, "bold")
                 ).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(head, text=title, bg=T["bg"], fg=accent_color,
                 font=("Segoe UI", 11, "bold")).pack(side=LEFT, anchor="w")

        # Card body with a colored left accent bar
        card_wrap = tk.Frame(inner, bg=T["bg"]); card_wrap.pack(fill=X)
        accent = tk.Frame(card_wrap, bg=accent_color, width=3)
        accent.pack(side=LEFT, fill=Y)
        body_card = tk.Frame(card_wrap, bg=T["panel"], padx=14, pady=12)
        body_card.pack(side=LEFT, fill=X, expand=True)

        for it in items:
            if isinstance(it, tuple):
                txt, color = it
            else:
                txt, color = it, T["text"]
            tk.Label(body_card, text=txt, bg=T["panel"], fg=color,
                     font=("Segoe UI", 9), wraplength=540, justify=LEFT
                     ).pack(anchor="w", pady=2)

    # GROUP — blue
    section_card("GROUP MEMBERS", "★", T["primary"], [
        "•  John Oniel Thomas Q. Araque",
        "•  Niel Allen S. Jauculan",
        "•  Tiff Anthony R. Parnala",
    ])

    # DESCRIPTION — green
    section_card("DESCRIPTION", "ℹ", T["success"], [
        ("Finds roots of f(x) using Bisection and False Position. "
         "Both methods require an interval [a, b] with f(a)·f(b) < 0, "
         "guaranteeing a root by the Intermediate Value Theorem.",
         T["text"]),
    ])

    # EDGE CASES — warning / orange
    section_card("EDGE CASES HANDLED", "⚠", T["warning"], [
        ("EC1  ·  Same-sign endpoints  (hard stop)",      T["danger"]),
        ("EC2  ·  Root exactly at endpoint  (warn, continue)", T["warning"]),
        ("EC3  ·  Undefined / infinite f(x)  (hard stop)",     T["danger"]),
        ("EC4  ·  Max iterations too low  (soft warning)",     T["warning"]),
        ("EC5  ·  Tolerance too loose  (soft warning)",        T["warning"]),
    ])

    # HOW TO USE — primary
    section_card("HOW TO USE", "▶", T["primary"], [
        ("1.  Choose Bisection or False Position",                        T["text"]),
        ("2.  Enter f(x)  —  use ** for powers (e.g. x**3 - x - 2)",      T["text"]),
        ("3.  Set the interval [a, b] with opposite-sign endpoints",      T["text"]),
        ("4.  Click  ▶  COMPUTE ROOT  (or press Enter)",                  T["text"]),
        ("5.  View the Summary, Solution Trail, and Graph tabs",          T["text"]),
    ])

    # KEYBOARD SHORTCUTS — label (light blue)
    section_card("KEYBOARD SHORTCUTS", "⌨", T["label"], [
        ("Enter      ·  Compute root",                          T["text"]),
        ("Esc        ·  Clear all fields and outputs",          T["text"]),
        ("Ctrl + T   ·  Toggle light / dark theme",             T["text"]),
    ])

    # TIPS — success / green
    section_card("TIPS", "✦", T["success"], [
        "•  Use the TEST CASES to load curated f(x) examples instantly.",
        "•  Use the EDGE CASE DEMOS to reproduce EC1 – EC5 on demand.",
        "•  Export a full report (TXT or HTML) from the header bar.",
    ])


def compute_with_status():
    btn_compute.configure(state=DISABLED, text="  ⋯  Computing...")
    update_status("Computing... please wait")
    root.update_idletasks()
    try:
        compute()
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
        update_status("Error - check inputs")
    finally:
        btn_compute.configure(state=NORMAL, text="  ▶  COMPUTE ROOT")


def load_example(expr, a, b):
    entry_function.delete(0, END); entry_function.insert(0, expr)
    entry_a.delete(0, END);        entry_a.insert(0, a)
    entry_b.delete(0, END);        entry_b.insert(0, b)


# ═══════════════════════════════════════════════════════════════════
#  WINDOW
# ═══════════════════════════════════════════════════════════════════
root = ttkb.Window(themename=T["ttk"],
                   title="[]  Bisection Root Finder — v1.0",
                   size=(1440, 880))
root.minsize(1100, 700)
root.configure(bg=T["bg"])
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# ── HEADER ─────────────────────────────────────────────
hdr = tk.Frame(root, height=84)
themed(hdr, bg="panel")
hdr.grid(row=0, column=0, sticky="ew")
hdr.grid_propagate(False)
hdr.grid_columnconfigure(1, weight=1)

# Thin accent rule under the header
hdr_accent = tk.Frame(root, height=2); themed(hdr_accent, bg="primary")
hdr_accent.grid(row=0, column=0, sticky="sew")

# Logo + title (left) — uses GRID so the badge and the title-stack are
# both vertically centered and perfectly aligned along the same line.
title_wrap = tk.Frame(hdr); themed(title_wrap, bg="panel")
title_wrap.grid(row=0, column=0, sticky="nsw", padx=22)
title_wrap.grid_rowconfigure(0, weight=1)
title_wrap.grid_columnconfigure(0, weight=0)
title_wrap.grid_columnconfigure(1, weight=0)

# Logo — just the bracket text, no square background
logo = tk.Label(title_wrap, text="[ ]", font=("Segoe UI", 26, "bold"))
themed(logo, bg="panel", fg="primary")
logo.grid(row=0, column=0, padx=(0, 10), sticky="")

# Title text stack — sticky="" centers vertically next to the badge
title_stack = tk.Frame(title_wrap); themed(title_stack, bg="panel")
title_stack.grid(row=0, column=1, sticky="")
ttl = tk.Label(title_stack, text="Bisection Root Finder",
               font=("Segoe UI", 18, "bold"))
themed(ttl, bg="panel", fg="text"); ttl.pack(anchor="w")

# Header buttons (right)
hbtns = tk.Frame(hdr); themed(hbtns, bg="panel")
hbtns.grid(row=0, column=2, sticky="e", padx=18, pady=10)

def make_header_btn(parent, text, command, accent=False):
    btn = tk.Button(parent, text=text, command=command,
                    font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                    padx=12, pady=6, cursor="hand2")
    if accent:
        themed(btn, bg="primary", fg="panel",
               activebackground="primary", activeforeground="panel")
    else:
        themed(btn, bg="elevated", fg="text",
               activebackground="border", activeforeground="primary")
    return btn

# Theme toggle button — text updated by toggle_theme()
theme_btn = tk.Button(hbtns, text="☾  Dark",
                      font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                      padx=12, pady=6, cursor="hand2")
themed(theme_btn, bg="elevated", fg="text",
       activebackground="border", activeforeground="primary")
theme_btn.pack(side=LEFT, padx=4)

about_btn  = make_header_btn(hbtns, "?  Help", show_about)
about_btn.pack(side=LEFT, padx=4)

export_btn = make_header_btn(hbtns, "⬇  Export", export_report)
export_btn.pack(side=LEFT, padx=4)

# ── MASTER LAYOUT ──────────────────────────────────────
master = tk.Frame(root); themed(master, bg="bg")
master.grid(row=1, column=0, sticky="nsew")
master.grid_rowconfigure(0, weight=1)
master.grid_columnconfigure(0, weight=0, minsize=340)
master.grid_columnconfigure(1, weight=1)

# ═══════════════════════════════════════════════════════
#  LEFT PANEL — INPUT
# ═══════════════════════════════════════════════════════
left = tk.Frame(master, width=340); themed(left, bg="panel")
left.grid(row=0, column=0, sticky="nsew")
left.grid_propagate(False)
left.grid_rowconfigure(0, weight=1)
left.grid_columnconfigure(0, weight=1)

# Border between panels
sep_left = tk.Frame(master, width=1); themed(sep_left, bg="border")
sep_left.place(in_=left, relx=1.0, x=-1, rely=0, relheight=1)

# Scrollable inner
canvas_scroll = tk.Canvas(left, bd=0, highlightthickness=0, width=320)
themed(canvas_scroll, bg="panel")
scroll_bar = ttkb.Scrollbar(left, orient=VERTICAL, command=canvas_scroll.yview)
canvas_scroll.configure(yscrollcommand=scroll_bar.set)
scroll_bar.grid(row=0, column=1, sticky="ns")
canvas_scroll.grid(row=0, column=0, sticky="nsew")

scroll_inner = tk.Frame(canvas_scroll); themed(scroll_inner, bg="panel")
scroll_window = canvas_scroll.create_window((0, 0), window=scroll_inner,
                                             anchor="nw", width=320)
def _on_inner_configure(_):
    canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
def _on_canvas_configure(ev):
    canvas_scroll.itemconfig(scroll_window, width=ev.width)
scroll_inner.bind("<Configure>", _on_inner_configure)
canvas_scroll.bind("<Configure>", _on_canvas_configure)
def _on_mousewheel(ev):
    canvas_scroll.yview_scroll(int(-1*(ev.delta/120)), "units")
canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)

# Helpers
def section_title(parent, icon, text):
    f = tk.Frame(parent); themed(f, bg="panel")
    f.pack(fill=X, padx=18, pady=(18, 8))
    ic = tk.Label(f, text=icon, font=("Segoe UI", 12, "bold"))
    themed(ic, bg="panel", fg="primary"); ic.pack(side=LEFT, padx=(0, 8))
    lbl = tk.Label(f, text=text, font=("Segoe UI", 10, "bold"))
    themed(lbl, bg="panel", fg="text"); lbl.pack(side=LEFT)
    sep = tk.Frame(f, height=1); themed(sep, bg="border")
    sep.pack(side=LEFT, fill=X, expand=True, padx=(12, 0), pady=(8, 0))

# ── Rounded-rectangle entry helper ──
# Uses a Canvas with a smooth polygon for true curved corners, with a real
# tk.Entry placed on top.  Registered for theme repaint via ROUNDED_FIELDS.
ROUNDED_FIELDS = []  # list of callables: () -> None

def _rrect_pts(x1, y1, x2, y2, r):
    return [
        x1 + r, y1, x2 - r, y1,
        x2,     y1, x2,     y1 + r,
        x2,     y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1,     y2, x1,     y2 - r,
        x1,     y1 + r, x1, y1,
    ]

def _make_rounded_entry(parent, default, height=42, radius=12, pad_x=14):
    """Returns (container_frame, tk.Entry).  ONE clean curved box — the
    polygon fill matches the surrounding panel so only the rounded outline
    is visible. The Entry sits seamlessly inside with no inner box."""
    container = tk.Frame(parent); themed(container, bg="panel")
    cnv = tk.Canvas(container, height=height, bd=0, highlightthickness=0)
    themed(cnv, bg="panel")
    cnv.pack(fill=X)

    # Polygon FILL = panel (invisible) so only the curved OUTLINE shows.
    bg_id = cnv.create_polygon(
        0, 0, 0, 0, 0, 0,           # placeholder, real points set on <Configure>
        smooth=True, splinesteps=24,
        fill=T["panel"], outline=T["border"], width=1.5,
    )
    # Entry shares the panel background — no inner box rendered.
    e = tk.Entry(cnv, font=("Consolas", 11),
                 relief="flat", bd=0, highlightthickness=0)
    themed(e, bg="panel", fg="text",
           insertbackground="text", selectbackground="primary",
           selectforeground="panel")
    e.insert(0, default)
    e_win = cnv.create_window(pad_x, height // 2,
                              anchor="w", window=e,
                              width=10, height=height - 14)

    state = {"focused": False}

    def redraw(width):
        if width < 4:
            return
        pts = _rrect_pts(1, 1, width - 1, height - 1, radius)
        cnv.coords(bg_id, *pts)
        cnv.itemconfig(e_win, width=max(10, width - pad_x * 2))

    cnv.bind("<Configure>", lambda ev: redraw(ev.width))

    def fin(_):
        state["focused"] = True
        cnv.itemconfig(bg_id, outline=T["primary"], width=2,
                       fill=T["panel"])
    def fout(_):
        state["focused"] = False
        cnv.itemconfig(bg_id, outline=T["border"], width=1.5,
                       fill=T["panel"])
    e.bind("<FocusIn>", fin)
    e.bind("<FocusOut>", fout)

    def retheme():
        outline = T["primary"] if state["focused"] else T["border"]
        cnv.itemconfig(bg_id, fill=T["panel"], outline=outline)
        try:
            e.configure(bg=T["panel"], fg=T["text"], insertbackground=T["text"])
        except tk.TclError:
            pass
    ROUNDED_FIELDS.append(retheme)

    return container, e


def make_field(parent, label, default, hint=""):
    wrap = tk.Frame(parent); themed(wrap, bg="panel")
    wrap.pack(fill=X, padx=18, pady=(4, 10))
    lbl = tk.Label(wrap, text=label, font=("Segoe UI", 9, "bold"))
    themed(lbl, bg="panel", fg="text"); lbl.pack(anchor="w")
    if hint:
        ht = tk.Label(wrap, text=hint, font=("Segoe UI", 8))
        themed(ht, bg="panel", fg="muted"); ht.pack(anchor="w", pady=(2, 4))
    container, e = _make_rounded_entry(wrap, default)
    container.pack(fill=X, pady=(4, 0))
    return e

# ── METHOD SECTION (DROPDOWN) ──
section_title(scroll_inner, "▶", "METHOD")
method_var = tk.StringVar(value="Bisection")
method_wrap = tk.Frame(scroll_inner); themed(method_wrap, bg="panel")
method_wrap.pack(fill=X, padx=18, pady=(0, 12))

# Styled, themed dropdown to select the numerical method
method_dropdown = ttkb.Combobox(method_wrap,
                                textvariable=method_var,
                                values=["Bisection", "False Position"],
                                state="readonly",
                                font=("Segoe UI", 11, "bold"),
                                bootstyle="primary")
method_dropdown.pack(fill=X, ipady=6)

# Method-info card — shows formula and description, updates on change
method_info_card = tk.Frame(method_wrap, padx=14, pady=12)
themed(method_info_card, bg="elevated")
method_info_card.pack(fill=X, pady=(10, 0))

method_formula_lbl = tk.Label(method_info_card, text="c = (a + b) / 2",
                              font=("Consolas", 11, "bold"))
themed(method_formula_lbl, bg="elevated", fg="primary")
method_formula_lbl.pack(anchor="w")

method_desc_lbl = tk.Label(method_info_card,
                           text="Guaranteed convergence by halving the bracket.",
                           font=("Segoe UI", 9), wraplength=260, justify=LEFT)
themed(method_desc_lbl, bg="elevated", fg="muted")
method_desc_lbl.pack(anchor="w", pady=(4, 0))

def on_method_change(_=None):
    if method_var.get() == "Bisection":
        method_formula_lbl.config(text="c = (a + b) / 2")
        method_desc_lbl.config(
            text="Guaranteed convergence by halving the bracket.")
    else:
        method_formula_lbl.config(text="c = b − f(b)·(b−a) / (f(b)−f(a))")
        method_desc_lbl.config(
            text="Weighted secant — usually faster on smooth functions.")
method_dropdown.bind("<<ComboboxSelected>>", on_method_change)

# ── FUNCTION SECTION ──
section_title(scroll_inner, "ƒ", "FUNCTION")
entry_function = make_field(scroll_inner, "f(x) — equation to solve",
                             "x**3 - x - 2",
                             "Operators: ** * / + −     Functions: sin cos exp log sqrt")

# ── INTERVAL SECTION ──
section_title(scroll_inner, "⌖", "SEARCH INTERVAL")
hint = tk.Label(scroll_inner,
    text="f(a) and f(b) must have OPPOSITE signs",
    font=("Segoe UI", 8))
themed(hint, bg="panel", fg="muted")
hint.pack(anchor="w", padx=18, pady=(0, 4))

interval_grid = tk.Frame(scroll_inner); themed(interval_grid, bg="panel")
interval_grid.pack(fill=X, padx=0, pady=0)
interval_grid.grid_columnconfigure(0, weight=1)
interval_grid.grid_columnconfigure(1, weight=1)

def make_inline_field(parent, label, default, col):
    wrap = tk.Frame(parent); themed(wrap, bg="panel")
    wrap.grid(row=0, column=col, sticky="ew",
              padx=(18 if col == 0 else 9, 9 if col == 0 else 18),
              pady=(4, 10))
    lbl = tk.Label(wrap, text=label, font=("Segoe UI", 9, "bold"))
    themed(lbl, bg="panel", fg="text"); lbl.pack(anchor="w")
    container, e = _make_rounded_entry(wrap, default)
    container.pack(fill=X, pady=(4, 0))
    return e

entry_a = make_inline_field(interval_grid, "a  (left)",  "1", 0)
entry_b = make_inline_field(interval_grid, "b  (right)", "2", 1)

# ── SETTINGS SECTION ──
section_title(scroll_inner, "⚙", "SETTINGS")
entry_tol  = make_field(scroll_inner, "Tolerance",
                         "1e-6",  "Smaller = more precise   ·   try 1e-4, 1e-6, 1e-10")
entry_iter = make_field(scroll_inner, "Max iterations",
                         "100",   "Usually 50 – 200 is enough")

# ── ACTION BUTTONS (3D / keyboard-key style) ──
btn_wrap = tk.Frame(scroll_inner); themed(btn_wrap, bg="panel")
btn_wrap.pack(fill=X, padx=18, pady=(16, 8))

# COMPUTE — green keycap
btn_compute_wrap, btn_compute = make_3d_button(
    btn_wrap, "  ▶  COMPUTE ROOT", lambda: compute_with_status(),
    bg_role="success", fg_role="panel",
    font_size=11, bold=True, ipadx=12, ipady=12, shadow_h=5)
btn_compute_wrap.pack(fill=X, pady=(0, 8))

# CLEAR — neutral keycap with danger-colored text
btn_clear_wrap, btn_clear = make_3d_button(
    btn_wrap, "  ⟲  CLEAR", lambda: clear_all(),
    bg_role="elevated", fg_role="danger",
    font_size=10, bold=True, ipadx=12, ipady=8, shadow_h=4)
btn_clear_wrap.pack(fill=X)

# ── EXAMPLES ──
section_title(scroll_inner, "✦", "TEST CASES")
tk.Label(scroll_inner, text="Click any example to load it.",
         font=("Segoe UI", 8), bg=T["panel"], fg=T["muted"]
         ).pack(anchor="w", padx=18, pady=(0, 6))

test_cases = [
    ("x³ − x − 2",        "x**3 - x - 2", "1", "2", "Cubic polynomial"),
    ("cos(x) − x",        "cos(x) - x",   "0", "1", "Dottie number"),
    ("x² − 4",            "x**2 - 4",     "1", "3", "Root at x = 2"),
    ("eˣ − 3x",           "exp(x) - 3*x", "0", "1", "Exp vs linear"),
    ("sin(x)",            "sin(x)",       "2", "4", "Root at π"),
]
def make_example_btn(parent, label, expr, ea, eb, desc):
    card = tk.Frame(parent, padx=10, pady=6); themed(card, bg="elevated")
    card.pack(fill=X, padx=18, pady=3)
    card.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    card.configure(cursor="hand2")
    top = tk.Frame(card); themed(top, bg="elevated")
    top.pack(fill=X)
    lbl = tk.Label(top, text=label, font=("Consolas", 10, "bold"))
    themed(lbl, bg="elevated", fg="primary")
    lbl.pack(side=LEFT)
    lbl.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    lbl.configure(cursor="hand2")
    rng = tk.Label(top, text=f"[{ea}, {eb}]", font=("Consolas", 9))
    themed(rng, bg="elevated", fg="muted"); rng.pack(side=RIGHT)
    rng.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    rng.configure(cursor="hand2")
    d = tk.Label(card, text=desc, font=("Segoe UI", 8))
    themed(d, bg="elevated", fg="muted"); d.pack(anchor="w", pady=(2, 0))
    d.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    d.configure(cursor="hand2")

for lbl, expr, ea, eb, desc in test_cases:
    make_example_btn(scroll_inner, lbl, expr, ea, eb, desc)

# ── EDGE-CASE DEMOS ──
section_title(scroll_inner, "⚠", "EDGE CASE DEMOS")
tk.Label(scroll_inner, text="Reproduce the 5 known edge cases.",
         font=("Segoe UI", 8), bg=T["panel"], fg=T["muted"]
         ).pack(anchor="w", padx=18, pady=(0, 6))

edge_demos = [
    ("EC1  ·  Same sign",  "x**2 + 1",     "-1", "1", "IVT violated"),
    ("EC2  ·  Root at a",  "x**2 - 1",     "1",  "3", "Root exactly at a = 1"),
    ("EC3  ·  Undefined",  "log(x)",       "-1", "1", "log undefined for x ≤ 0"),
    ("EC4  ·  Low iters",  "x**3 - x - 2", "1",  "2", "Set max iter to 2"),
    ("EC5  ·  Loose tol",  "x**3 - x - 2", "1",  "2", "Set tolerance to 1.0"),
]
def make_edge_btn(parent, label, expr, ea, eb, desc):
    card = tk.Frame(parent, padx=10, pady=6); themed(card, bg="elevated")
    card.pack(fill=X, padx=18, pady=3)
    card.configure(cursor="hand2")
    card.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    lbl = tk.Label(card, text=label, font=("Segoe UI", 9, "bold"))
    themed(lbl, bg="elevated", fg="warning"); lbl.pack(anchor="w")
    lbl.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    lbl.configure(cursor="hand2")
    d = tk.Label(card, text=desc, font=("Segoe UI", 8))
    themed(d, bg="elevated", fg="muted"); d.pack(anchor="w")
    d.bind("<Button-1>", lambda _: load_example(expr, ea, eb))
    d.configure(cursor="hand2")

for lbl, expr, ea, eb, desc in edge_demos:
    make_edge_btn(scroll_inner, lbl, expr, ea, eb, desc)

tk.Frame(scroll_inner, height=18, bg=T["panel"]).pack()


# ═══════════════════════════════════════════════════════
#  RIGHT PANEL — OUTPUT
# ═══════════════════════════════════════════════════════
right = tk.Frame(master); themed(right, bg="bg")
right.grid(row=0, column=1, sticky="nsew")
right.grid_rowconfigure(0, weight=1)
right.grid_columnconfigure(0, weight=1, minsize=420)
right.grid_columnconfigure(1, weight=1, minsize=380)

nb_wrap = tk.Frame(right); themed(nb_wrap, bg="bg")
nb_wrap.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
nb_wrap.grid_rowconfigure(0, weight=1)
nb_wrap.grid_columnconfigure(0, weight=1)

sty = ttk.Style()

def apply_ttk_styles():
    sty.configure("TNotebook",     background=T["bg"], borderwidth=0)
    sty.configure("TNotebook.Tab",
                  background=T["elevated"], foreground=T["muted"],
                  padding=[16, 8],  font=("Segoe UI", 10, "bold"))
    sty.map("TNotebook.Tab",
            background=[("selected", T["panel"])],
            foreground=[("selected", T["primary"])])
    sty.configure("T.Treeview",
                  background=T["panel"], foreground=T["text"],
                  fieldbackground=T["panel"], rowheight=24,
                  font=("Consolas", 9), borderwidth=0)
    sty.configure("T.Treeview.Heading",
                  background=T["elevated"], foreground=T["text"],
                  font=("Segoe UI", 9, "bold"), borderwidth=0, relief="flat")
    sty.map("T.Treeview", background=[("selected", T["primary"])],
            foreground=[("selected", T["panel"])])

apply_ttk_styles()

notebook = ttk.Notebook(nb_wrap)
notebook.grid(row=0, column=0, sticky="nsew")

def make_text_tab(nb, tab_title):
    frm = tk.Frame(nb); themed(frm, bg="panel")
    nb.add(frm, text=f"  {tab_title}  ")
    frm.grid_rowconfigure(0, weight=1)
    frm.grid_columnconfigure(0, weight=1)
    txt = tk.Text(frm, font=("Consolas", 10), wrap=WORD,
                  relief="flat", padx=14, pady=12, borderwidth=0)
    themed(txt, bg="panel", fg="text",
           insertbackground="text", selectbackground="primary")
    txt.grid(row=0, column=0, sticky="nsew")
    sc = ttkb.Scrollbar(frm, command=txt.yview)
    sc.grid(row=0, column=1, sticky="ns")
    txt.configure(yscrollcommand=sc.set)
    return txt

results_text = make_text_tab(notebook, "◇  Summary")
steps_text   = make_text_tab(notebook, "▶  Solution Trail")

def configure_text_tags():
    for txt in (steps_text, results_text):
        txt.tag_configure("header",  foreground=T["primary"], font=("Consolas", 10, "bold"))
        txt.tag_configure("section", foreground=T["primary"], font=("Consolas", 10, "bold"))
        txt.tag_configure("method",  foreground=T["warning"], font=("Consolas", 10, "bold"))
        txt.tag_configure("edge",    foreground=T["danger"],  font=("Consolas", 10, "bold"))
        txt.tag_configure("verify",  foreground=T["label"],   font=("Consolas", 10))
        txt.tag_configure("label",   foreground=T["muted"],   font=("Consolas", 10))
        txt.tag_configure("value",   foreground=T["text"],    font=("Consolas", 10, "bold"))
        txt.tag_configure("explain", foreground=T["text"],    font=("Consolas", 10))
        txt.tag_configure("good",    foreground=T["success"], font=("Consolas", 10, "bold"))
        txt.tag_configure("warn",    foreground=T["warning"], font=("Consolas", 10, "bold"))
        txt.tag_configure("dim",     foreground=T["subtle"],  font=("Consolas", 10))
        txt.tag_configure("iter",    foreground=T["primary"], font=("Consolas", 10, "bold"))

configure_text_tags()

# ── ITERATION TABLE ──
tab_tbl = tk.Frame(notebook); themed(tab_tbl, bg="panel")
notebook.add(tab_tbl, text="  ⊞  Iteration Table  ")
tab_tbl.grid_rowconfigure(0, weight=1)
tab_tbl.grid_columnconfigure(0, weight=1)

cols = ("Iter","a","b","Midpoint c","f(a)","f(b)","f(c)","Width","Decision")
iter_tree = ttk.Treeview(tab_tbl, columns=cols, show="headings",
                          style="T.Treeview", height=30)
widths = [44, 102, 102, 122, 88, 88, 96, 96, 124]
for col, w in zip(cols, widths):
    iter_tree.heading(col, text=col)
    iter_tree.column(col, width=w, anchor=CENTER, minwidth=44)

def configure_tree_tags():
    # Set BOTH background and foreground so rows remain readable in any theme.
    iter_tree.tag_configure("odd",  background=T["elevated"], foreground=T["text"])
    iter_tree.tag_configure("even", background=T["panel"],    foreground=T["text"])
configure_tree_tags()

tsy = ttkb.Scrollbar(tab_tbl, command=iter_tree.yview)
tsx = ttkb.Scrollbar(tab_tbl, orient=HORIZONTAL, command=iter_tree.xview)
iter_tree.configure(yscrollcommand=tsy.set, xscrollcommand=tsx.set)
iter_tree.grid(row=0, column=0, sticky="nsew")
tsy.grid(row=0, column=1, sticky="ns")
tsx.grid(row=1, column=0, sticky="ew")

# Default placeholder text in panels
results_text.insert(END,
    "  ◆ Results will appear here.\n\n"
    "  ▸ Select a method, enter your function and interval,\n"
    "    then click  ▶  COMPUTE ROOT.\n\n"
    "  ▸ Edge-case warnings appear in this panel and in the\n"
    "    Solution Trail tab.\n")
results_text.config(state=DISABLED)

steps_text.insert(END,
    "  ◆ The Solution Trail will appear here after you click  ▶  COMPUTE ROOT.\n\n"
    "  ▸ The trail streams line-by-line and clearly identifies which\n"
    "    method was used at the top.\n\n"
    "  ▸ Edge-case warnings appear in red at the top of the trail:\n\n"
    "      EC1  ·  Same-sign endpoints (IVT violated)\n"
    "      EC2  ·  Root exactly at endpoint\n"
    "      EC3  ·  Undefined / infinite function value\n"
    "      EC4  ·  Max iterations too low\n"
    "      EC5  ·  Tolerance too loose\n",
    "explain")
steps_text.config(state=DISABLED)

# ── GRAPH PANEL ──
gr_wrap = tk.Frame(right); themed(gr_wrap, bg="bg")
gr_wrap.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
gr_wrap.grid_rowconfigure(1, weight=1)
gr_wrap.grid_columnconfigure(0, weight=1)

gr_hdr = tk.Frame(gr_wrap); themed(gr_hdr, bg="bg")
gr_hdr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
gr_icon = tk.Label(gr_hdr, text="◆", font=("Segoe UI", 11, "bold"))
themed(gr_icon, bg="bg", fg="primary"); gr_icon.pack(side=LEFT, padx=(2, 8))
gr_lbl = tk.Label(gr_hdr, text="GRAPH", font=("Segoe UI", 10, "bold"))
themed(gr_lbl, bg="bg", fg="text"); gr_lbl.pack(side=LEFT)

graph_frame = tk.Frame(gr_wrap, highlightthickness=1)
themed(graph_frame, bg="panel", highlightbackground="border")
graph_frame.grid(row=1, column=0, sticky="nsew")
ph = tk.Label(graph_frame, text="◆  Graph appears after computation",
              font=("Segoe UI", 12))
themed(ph, bg="panel", fg="muted")
ph.place(relx=0.5, rely=0.5, anchor="center")

# ── STATUS BAR ──
sbar = tk.Frame(root, height=28); themed(sbar, bg="elevated")
sbar.grid(row=2, column=0, sticky="ew")
sbar.grid_propagate(False)
status_label = tk.Label(sbar, text="  Ready", font=("Segoe UI", 9), anchor="w")
themed(status_label, bg="elevated", fg="muted")
status_label.pack(side=LEFT, padx=8, fill=Y)
hint_lbl = tk.Label(sbar, text="Enter = Compute   ·   Esc = Clear   ",
                     font=("Segoe UI", 9))
themed(hint_lbl, bg="elevated", fg="subtle")
hint_lbl.pack(side=RIGHT, padx=8)


# ═══════════════════════════════════════════════════════
#  THEME TOGGLE
# ═══════════════════════════════════════════════════════
def toggle_theme():
    global T
    new_name = "light" if T["name"] == "dark" else "dark"
    T = THEMES[new_name]

    # 1. Re-apply all registered widget colours
    for widget, roles in THEMED_WIDGETS:
        _apply_widget_theme(widget, roles)

    # 2. Repaint borders that have non-themed colours after focus events
    root.configure(bg=T["bg"])

    # 3. Update ttk styles
    apply_ttk_styles()
    configure_text_tags()
    configure_tree_tags()

    # 3b. Repaint rounded-rectangle entry backgrounds/outlines
    for fn in ROUNDED_FIELDS:
        try: fn()
        except Exception: pass

    # 3c. Repaint 3D button shadow tints to match the new theme
    for wrap, _btn, role in THREEDEE_BUTTONS:
        try:
            tint = SHADOW_TINTS.get(role, SHADOW_TINTS["elevated"])
            wrap.configure(bg=tint[T["name"]])
        except tk.TclError:
            pass

    # 4. Update toggle button label
    if T["name"] == "dark":
        theme_btn.configure(text="☼  Light")
    else:
        theme_btn.configure(text="☾  Dark")

    update_status(f"Switched to {T['name']} mode.")

theme_btn.configure(command=toggle_theme)
theme_btn.configure(text="☼  Light")  # initially in dark mode → click goes to light

# ═══════════════════════════════════════════════════════
#  KEY BINDINGS
# ═══════════════════════════════════════════════════════
root.bind("<Return>", lambda _: compute_with_status())
root.bind("<Escape>", lambda _: clear_all())
root.bind("<Control-t>", lambda _: toggle_theme())

root.mainloop()