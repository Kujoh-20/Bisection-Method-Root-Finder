# Test Plan — Bisection Method Root Finder
### Numerical Analysis — v1.0

**Group Members:** John Oniel Thomas Q. Araque | Niel Allen S. Jauculan | Tiff Anthony R. Parnala

---

## Test 1: System Launch

**Objective:** Verify that the program starts without errors and the UI loads correctly.

**Steps:**
1. Open a terminal in the project folder.
2. Run `python bisection_method.py`.
3. Observe whether the application window opens.

**Expected Result:**
The application window opens with title "Root Finder — Bisection & False Position", all UI elements are visible (header, input panel, notebook tabs, graph area, status bar), and the status bar reads "Ready".

**Actual Result:**
Program runs and the full UI appears without errors. Status bar shows "Ready". All panels, tabs, and buttons are visible and properly styled.

---

## Test 2: Valid Input and Root Computation (Bisection)

**Objective:** Verify that the Bisection method correctly computes the root of a known function.

**Steps:**
1. Select **Bisection** method using the radio button.
2. Enter `x**3 - x - 2` in the function field.
3. Set `a = 1`, `b = 2`.
4. Set tolerance to `1e-6`, max iterations to `100`.
5. Click **COMPUTE ROOT**.

**Expected Result:**
- Root computed near `x ≈ 1.5213797068` (known root of x³ - x - 2).
- Summary tab shows root, f(root) ≈ 0, iteration count, error bound, and convergence status "Yes".
- Solution Trail streams line by line, starting with ">> BISECTION METHOD <<".
- Iteration Table populates with all iterations.
- Graph shows the function curve with a red dashed root marker.
- Toast notification appears: "Root = 1.52137971".

**Actual Result:**
All expected outputs appear correctly. Root found at x ≈ 1.5213797068. Bisection badge shown in trail. Graph renders with root marker.

---

## Test 3: Valid Input and Root Computation (False Position)

**Objective:** Verify that the False Position method computes the correct root and produces fewer iterations than Bisection for the same function.

**Steps:**
1. Select **False Position** method using the radio button.
2. Enter `x**3 - x - 2` in the function field.
3. Set `a = 1`, `b = 2`.
4. Set tolerance to `1e-6`, max iterations to `100`.
5. Click **COMPUTE ROOT**.

**Expected Result:**
- Root computed near `x ≈ 1.5213797068` (same root as Bisection).
- Summary tab shows "METHOD: FALSE POSITION".
- Fewer iterations than Bisection (False Position converges faster on smooth functions).
- Solution Trail starts with ">> FALSE POSITION METHOD (Regula Falsi) <<".
- Graph curve is plotted in orange (Bisection uses cyan).

**Actual Result:**
Root found correctly. False Position used fewer iterations than Bisection. Method badge in trail reads "False Position". Graph curve rendered in orange.

---

## Test 4: Invalid Input — Same Sign Error Handling

**Objective:** Verify that the system correctly rejects an interval where f(a) and f(b) have the same sign (IVT violation).

**Steps:**
1. Select either method.
2. Enter `x**2 + 1` in the function field (this function has no real roots).
3. Set `a = -1`, `b = 1`.
4. Click **COMPUTE ROOT**.

**Expected Result:**
An error dialog appears stating that f(a) and f(b) have the same sign and the method cannot be applied. No computation is performed. No results appear in the tabs.

**Actual Result:**
Error dialog appears: "f(-1.0) = 2.0000 and f(1.0) = 2.0000 have the SAME sign." Computation is blocked. Tabs remain empty.

---

## Test 5: Invalid Input — Empty / Non-Numeric Fields

**Objective:** Verify that the system handles missing or invalid input gracefully without crashing.

**Steps:**
1. Clear the function field (leave it empty).
2. Type `abc` in the `a` field.
3. Type `xyz` in the `b` field.
4. Click **COMPUTE ROOT**.

**Expected Result:**
An error dialog lists all input errors: function is required, a must be a number, b must be a number. No computation is performed. Program does not crash.

**Actual Result:**
Error dialog appears listing all three validation errors. Program remains stable and ready for correct input.

---

## Test 6: Test Case Loader — Pre-Built Examples

**Objective:** Verify that clicking a test case button correctly loads the function and interval into the input fields.

**Steps:**
1. Scroll down the left panel to the TEST CASES section.
2. Click **TC3: x^2-4**.
3. Observe the input fields.

**Expected Result:**
- Function field updates to `x**2 - 4`.
- `a` field updates to `1`.
- `b` field updates to `3`.
- Fields are immediately ready for computation.

**Actual Result:**
All three fields update correctly after clicking TC3. Clicking COMPUTE ROOT immediately produces the correct root at x = 2.0.

---

## Test 7: Max Iterations Cap (Rule 3 Stopping)

**Objective:** Verify that the system correctly stops at the max iteration limit and reports it as "not converged" when the limit is too low.

**Steps:**
1. Select Bisection method.
2. Enter `x**3 - x - 2`, `a = 1`, `b = 2`.
3. Set tolerance to `1e-15` (very tight) and max iterations to `3`.
4. Click **COMPUTE ROOT**.

**Expected Result:**
- Computation stops after exactly 3 iterations.
- Summary shows "Converged = No (Rule 3: hit max iter = 3)".
- Solution Trail shows "Rule 3 fired" warning in orange.
- Status bar shows "STATUS: INCOMPLETE".

**Actual Result:**
Loop stops at iteration 3. Summary and trail both report max iteration stop reason. Warning correctly displayed in orange text.

---

## Test 8: Solution Trail Method Identification

**Objective:** Verify that the Solution Trail clearly identifies which method was used at the top.

**Steps:**
1. Run any computation with **Bisection** selected. Note the top of the Solution Trail.
2. Run the same computation with **False Position** selected. Note the top of the Solution Trail.

**Expected Result:**
- Bisection run: Trail starts with ">> BISECTION METHOD <<" in orange.
- False Position run: Trail starts with ">> FALSE POSITION METHOD (Regula Falsi) <<" in orange.
- Different midpoint formulas are shown inline at each iteration step.

**Actual Result:**
Both methods correctly display their name badge at the top of the trail. Method-specific formula shown at each iteration.

---

## Test Summary Table

| # | Test Name | Method | Pass/Fail |
|---|---|---|---|
| 1 | System Launch | — | Pass |
| 2 | Valid Root Computation (Bisection) | Bisection | Pass |
| 3 | Valid Root Computation (False Position) | False Position | Pass |
| 4 | Same Sign Error Handling | Both | Pass |
| 5 | Empty / Invalid Input | Both | Pass |
| 6 | Test Case Loader | Both | Pass |
| 7 | Max Iterations Cap | Bisection | Pass |
| 8 | Solution Trail Method ID | Both | Pass |

---

*Bisection Method Root Finder — Test Plan v1 — Numerical Analysis*
