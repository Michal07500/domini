"""Jednoduché grafy kreslené na tkinter Canvas (bez ďalších knižníc)."""

TEXT = "#ece8e1"
MUTED = "#8b99a6"
GRID = "#2a3a48"


def draw_bars(canvas, title, items, color, fmt="{:.0f} %", max_value=None, empty="Zatiaľ málo dát"):
    """Vodorovné stĺpce: items = [(popis, hodnota, poznámka)]."""
    canvas.delete("all")
    w, h = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 120)
    canvas.create_text(12, 14, text=title, anchor="w", fill=TEXT, font=("Segoe UI", 11, "bold"))
    if not items:
        canvas.create_text(w / 2, h / 2, text=empty, fill=MUTED, font=("Segoe UI", 10))
        return
    top, left, right = 40, 110, 120
    max_value = max_value or max(v for _, v, _ in items) or 1
    row = min(34, (h - top - 10) / len(items))
    bar_h = max(6, row * 0.55)
    for i, (label, value, note) in enumerate(items):
        y = top + i * row + row / 2
        canvas.create_text(left - 10, y, text=label, anchor="e", fill=MUTED, font=("Segoe UI", 10))
        length = (w - left - right) * max(0, value) / max_value
        canvas.create_line(left, y, w - right, y, fill=GRID)
        if length > 0:
            canvas.create_rectangle(left, y - bar_h / 2, left + length, y + bar_h / 2, fill=color, outline="")
        canvas.create_text(left + length + 8, y, text=fmt.format(value), anchor="w", fill=TEXT,
                           font=("Segoe UI", 10, "bold"))
        if note:
            canvas.create_text(w - 8, y, text=note, anchor="e", fill=MUTED, font=("Segoe UI", 8))


def draw_line(canvas, title, values, color, reference=None, fmt="{:.2f}", empty="Zatiaľ málo dát"):
    """Čiarový graf hodnôt v čase (napr. K/D v posledných zápasoch)."""
    canvas.delete("all")
    w, h = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 120)
    canvas.create_text(12, 14, text=title, anchor="w", fill=TEXT, font=("Segoe UI", 11, "bold"))
    if len(values) < 2:
        canvas.create_text(w / 2, h / 2, text=empty, fill=MUTED, font=("Segoe UI", 10))
        return
    top, bottom, left, right = 40, 28, 44, 20
    lo = min(values + ([reference] if reference is not None else []))
    hi = max(values + ([reference] if reference is not None else []))
    if hi - lo < 0.2:
        hi, lo = hi + 0.1, lo - 0.1

    def xy(i, v):
        x = left + (w - left - right) * i / (len(values) - 1)
        y = top + (h - top - bottom) * (1 - (v - lo) / (hi - lo))
        return x, y

    for v in (lo, (lo + hi) / 2, hi):
        _, y = xy(0, v)
        canvas.create_line(left, y, w - right, y, fill=GRID)
        canvas.create_text(left - 6, y, text=fmt.format(v), anchor="e", fill=MUTED, font=("Segoe UI", 8))
    if reference is not None:
        _, y = xy(0, reference)
        canvas.create_line(left, y, w - right, y, fill=MUTED, dash=(4, 3))
    points = [c for i, v in enumerate(values) for c in xy(i, v)]
    canvas.create_line(*points, fill=color, width=2, smooth=False)
    for i, v in enumerate(values):
        x, y = xy(i, v)
        canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="#0f1923", width=2)
    x, y = xy(len(values) - 1, values[-1])
    canvas.create_text(x - 6, y - 14, text=fmt.format(values[-1]), anchor="e", fill=TEXT, font=("Segoe UI", 9, "bold"))
    canvas.create_text(left, h - 10, text=f"posledných {len(values)} zápasov  →  najnovší", anchor="w",
                       fill=MUTED, font=("Segoe UI", 8))
