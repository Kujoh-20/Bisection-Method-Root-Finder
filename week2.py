import tkinter as tk
from tkinter import messagebox
from datetime import datetime

# ---------------- STARTUP INFO ----------------
def show_startup_info():
    info = (
        "Welcome to the Bisection Method Root Finder!\n\n"
        "Inputs:\n"
        "- f(x): Function in terms of x, e.g., x**3 - x - 2\n"
        "- a: Left endpoint of interval\n"
        "- b: Right endpoint of interval\n"
        "- Tolerance: Desired accuracy (e.g., 0.0001)\n"
        "- Max Iterations: Maximum allowed iterations\n\n"
        "Click 'Compute' to see a placeholder solution trail.\n"
        "Invalid inputs will show an error without crashing."
    )
    messagebox.showinfo("How to Use", info)

# ---------------- VALIDATED COMPUTE ----------------
def compute_week2():
    output_text.delete(1.0, tk.END)
    validation_passed = True
    errors = []

    # Validate required fields
    f_expr = entry_function.get().strip()
    a_str = entry_a.get().strip()
    b_str = entry_b.get().strip()
    tol_str = entry_tol.get().strip()
    iter_str = entry_iter.get().strip()

    if not f_expr: errors.append("f(x) is required.")
    if not a_str: errors.append("a is required.")
    if not b_str: errors.append("b is required.")
    if not tol_str: errors.append("Tolerance is required.")
    if not iter_str: errors.append("Max Iterations is required.")

    # Validate numeric types
    try: a_val = float(a_str)
    except: errors.append("a must be a number.")
    try: b_val = float(b_str)
    except: errors.append("b must be a number.")
    try: tol_val = float(tol_str)
    except: errors.append("Tolerance must be a number.")
    try: iter_val = int(iter_str)
    except: errors.append("Max Iterations must be an integer.")

    # Validate a < b
    if 'a_val' in locals() and 'b_val' in locals() and a_val >= b_val:
        errors.append("a must be less than b.")

    # Show errors if any
    if errors:
        messagebox.showerror("Input Validation Error", "\n".join(errors))
        for e in errors:
            output_text.insert(tk.END, f"VALIDATION FAIL: {e}\n")
        validation_passed = False
    else:
        output_text.insert(tk.END, "VALIDATION PASS: All inputs are valid.\n")

    # Placeholder trail output (only if valid)
    if validation_passed:
        output_text.insert(tk.END, "\nGIVEN:\n")
        output_text.insert(tk.END, f"f(x) = {f_expr}\n")
        output_text.insert(tk.END, f"a = {a_val}, b = {b_val}\n")
        output_text.insert(tk.END, f"Tolerance = {tol_val}\n")
        output_text.insert(tk.END, f"Max Iterations = {iter_val}\n\n")
        output_text.insert(tk.END, "METHOD:\nBisection Method\n\n")
        output_text.insert(tk.END, "STEPS:\n1. Placeholder step output...\n2. Placeholder step output...\n\n")
        output_text.insert(tk.END, "FINAL ANSWER:\nRoot ≈ 1.521\n")

# ---------------- CLEAR ----------------
def clear_all():
    output_text.delete(1.0, tk.END)
    for entry in [entry_function, entry_a, entry_b, entry_tol, entry_iter]:
        entry.delete(0, tk.END)

# ---------------- ROOT WINDOW ----------------
root = tk.Tk()
root.title("Bisection Method Root Finder - Week 2")
root.geometry("900x500")
root.configure(bg="#1f1f2e")

# ---------------- INPUT FRAME ----------------
input_frame = tk.Frame(root, bg="#2e2e3e", padx=10, pady=10)
input_frame.pack(fill="x", padx=10, pady=10)

labels = ["f(x):", "a:", "b:", "Tolerance:", "Max Iterations:"]
entries = []

for i, text in enumerate(labels):
    tk.Label(input_frame, text=text, bg="#2e2e3e", fg="white").grid(row=i, column=0, sticky="w", pady=5)
    entry = tk.Entry(input_frame, bg="#3c3c4e", fg="white", insertbackground="white")
    entry.grid(row=i, column=1, pady=5, padx=8, sticky="we")
    entries.append(entry)

entry_function, entry_a, entry_b, entry_tol, entry_iter = entries

compute_btn = tk.Button(input_frame, text="Compute", bg="#4e89ff", fg="white",
                        command=compute_week2)
compute_btn.grid(row=5, column=0, pady=15, sticky="we")

clear_btn = tk.Button(input_frame, text="Clear", bg="#ff4e4e", fg="white",
                      command=clear_all)
clear_btn.grid(row=5, column=1, pady=15, sticky="we")

# ---------------- OUTPUT ----------------
output_frame = tk.Frame(root, bg="#2e2e3e", padx=10, pady=10, bd=2, relief="ridge")
output_frame.pack(fill="both", expand=True, padx=10, pady=10)

output_text = tk.Text(output_frame, wrap="none", font=("Courier New", 11), bg="#1c1c2c", fg="white")
output_text.pack(fill="both", expand=True)

# Show startup pop-up
root.after(500, show_startup_info)

root.mainloop()
