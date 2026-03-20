import tkinter as tk
from tkinter import messagebox

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
        "Click 'Compute' to see a placeholder solution trail."    )
    messagebox.showinfo("How to Use", info)

# ---------------- PLACEHOLDER COMPUTE ----------------
def compute_placeholder():
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "GIVEN:\nf(x) = x**3 - x - 2\na = 1, b = 2\nTolerance = 0.0001\nMax Iterations = 20\n\n")
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
root.title("Bisection Method Root Finder - Week 1")
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
                        command=compute_placeholder)
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
