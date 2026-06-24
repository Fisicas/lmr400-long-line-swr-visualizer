"""LMR-400 Long-Line SWR Visualizer.

Educational GUI comparing a datasheet-style LMR-400 attenuation model with an
approximate physical RLCG transmission-line model.  The main lesson is that a
long open-ended lossy feedline can show a moderate apparent SWR at the analyzer
because the reflected wave is attenuated on the outbound and return paths.
"""

from __future__ import annotations

import csv
import math
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

C0 = 299_792_458.0
FT_PER_M = 3.280839895013123
MU0 = 4.0 * math.pi * 1e-7
EPS = 1e-15

LMR400_TABLE_MHZ = np.array([30, 50, 150, 220, 450, 900, 1500, 1800, 2000, 2500, 5800, 8000], float)
LMR400_TABLE_DB_100FT = np.array([0.7, 0.9, 1.5, 1.9, 2.7, 3.9, 5.1, 5.7, 6.0, 6.8, 10.8, 13.0], float)


@dataclass
class Result:
    name: str
    f: np.ndarray
    swr: np.ndarray
    gamma: np.ndarray
    zin: np.ndarray
    loss_db: np.ndarray
    env_swr: np.ndarray
    warning: str = ""


def swr(gamma_mag: np.ndarray) -> np.ndarray:
    g = np.clip(np.asarray(gamma_mag, float), 0.0, 0.999999999)
    return (1.0 + g) / (1.0 - g)


def gamma_from_z(z: np.ndarray, zref: float) -> np.ndarray:
    return (z - zref) / (z + zref + EPS)


def fmt_freq(f_hz: float) -> str:
    if f_hz >= 1e9:
        return f"{f_hz/1e9:.4g} GHz"
    if f_hz >= 1e6:
        return f"{f_hz/1e6:.4g} MHz"
    if f_hz >= 1e3:
        return f"{f_hz/1e3:.4g} kHz"
    return f"{f_hz:.4g} Hz"


def lmr400_formula_db_100ft(f_hz: np.ndarray) -> np.ndarray:
    """LMR-400 attenuation equation in dB/100 ft, f in Hz."""
    f_mhz = np.maximum(np.asarray(f_hz, float) / 1e6, 1e-12)
    return 0.122290 * np.sqrt(f_mhz) + 0.000260 * f_mhz


def lmr400_table_db_100ft(f_hz: np.ndarray) -> np.ndarray:
    """Log-log interpolation through table; formula outside 30 MHz to 8 GHz."""
    f_mhz = np.asarray(f_hz, float) / 1e6
    y = lmr400_formula_db_100ft(f_hz)
    m = (f_mhz >= LMR400_TABLE_MHZ[0]) & (f_mhz <= LMR400_TABLE_MHZ[-1])
    if np.any(m):
        y[m] = np.exp(np.interp(np.log(f_mhz[m]), np.log(LMR400_TABLE_MHZ), np.log(LMR400_TABLE_DB_100FT)))
    return y


def load_gamma(kind: str, zload: complex, z0: complex) -> complex:
    if kind == "Open circuit":
        return 1.0 + 0j
    if kind == "Short circuit":
        return -1.0 + 0j
    return (zload - z0) / (zload + z0 + EPS)


def datasheet_model(f: np.ndarray, length_m: float, kind: str, zload: complex, zref: float, source: str) -> Result:
    att = lmr400_table_db_100ft(f) if source.startswith("Table") else lmr400_formula_db_100ft(f)
    loss_db = att * (length_m * FT_PER_M) / 100.0
    rt_mag = 10.0 ** (-loss_db / 10.0)  # reflected voltage-wave attenuation after down-and-back path
    vf = 0.84
    z0 = 50.0
    beta = 2.0 * np.pi * f / (vf * C0)
    gl = load_gamma(kind, zload, z0)
    gamma_nominal = gl * rt_mag * np.exp(-2j * beta * length_m)
    zin = z0 * (1.0 + gamma_nominal) / (1.0 - gamma_nominal + EPS)
    gamma_analyzer = gamma_from_z(zin, zref)
    warning = ""
    if f.min() < 30e6 or f.max() > 8e9:
        warning = "Datasheet mode is extrapolated outside the 30 MHz to 8 GHz table range."
    return Result("Datasheet practical", f, swr(np.abs(gamma_analyzer)), gamma_analyzer, zin, loss_db, swr(np.abs(gl) * rt_mag), warning)


def physical_model(f: np.ndarray, length_m: float, kind: str, zload: complex, zref: float, tan_delta: float, loss_scale: float) -> Result:
    omega = 2.0 * np.pi * f
    c_per_m = 78.4e-12
    l_per_m = 0.20e-6
    a = 2.74e-3 / 2.0
    b = 7.39e-3 / 2.0
    rho_cu = 1.68e-8
    rs = np.sqrt(np.pi * f * MU0 * rho_cu)
    r_skin = rs / (2.0 * np.pi * a) + rs / (2.0 * np.pi * b)
    r_dc = (4.6 + 5.4) / 1000.0
    R = np.sqrt(r_dc**2 + (loss_scale * r_skin) ** 2)
    G = omega * c_per_m * tan_delta
    Zs = R + 1j * omega * l_per_m
    Ys = G + 1j * omega * c_per_m
    gamma = np.sqrt(Zs * Ys)
    zc = np.sqrt(Zs / Ys)
    glen = gamma * length_m
    if kind == "Open circuit":
        zin = zc / np.tanh(glen)
        glmag = 1.0
    elif kind == "Short circuit":
        zin = zc * np.tanh(glen)
        glmag = 1.0
    else:
        t = np.tanh(glen)
        zin = zc * (zload + zc * t) / (zc + zload * t + EPS)
        glmag = abs((zload - 50.0) / (zload + 50.0 + EPS))
    gamma_analyzer = gamma_from_z(zin, zref)
    alpha = np.real(gamma)
    loss_db = 8.686 * alpha * length_m
    return Result(
        "Physical RLCG",
        f,
        swr(np.abs(gamma_analyzer)),
        gamma_analyzer,
        zin,
        loss_db,
        swr(glmag * np.exp(-2.0 * alpha * length_m)),
        "Physical conductor/shield loss is approximate; use datasheet mode for field estimates.",
    )


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("LMR-400 Long-Line SWR Visualizer")
        root.geometry("1320x900")
        self.results: dict[str, Result] = {}
        self._vars()
        self._layout()
        self.update()

    def _vars(self) -> None:
        self.length = tk.DoubleVar(value=21.0)
        self.fmin = tk.DoubleVar(value=1.0)
        self.fmax = tk.DoubleVar(value=1000.0)
        self.units = tk.StringVar(value="MHz")
        self.mode = tk.StringVar(value="Compare both")
        self.term = tk.StringVar(value="Open circuit")
        self.zref = tk.DoubleVar(value=50.0)
        self.load_r = tk.DoubleVar(value=50.0)
        self.load_x = tk.DoubleVar(value=0.0)
        self.source = tk.StringVar(value="Table interpolation + formula outside table")
        self.points_per_ripple = tk.IntVar(value=25)
        self.max_points = tk.IntVar(value=12000)
        self.logx = tk.BooleanVar(value=False)
        self.symlogz = tk.BooleanVar(value=True)
        self.swr_cap = tk.DoubleVar(value=50.0)
        self.tan_delta = tk.DoubleVar(value=0.0003)
        self.loss_scale = tk.DoubleVar(value=1.0)

    def _layout(self) -> None:
        controls = ttk.LabelFrame(self.root, text="Parameters", padding=10)
        controls.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        plots = ttk.Frame(self.root, padding=5)
        plots.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        def row(label: str, var: tk.Variable, width: int = 12) -> None:
            ttk.Label(controls, text=label).pack(anchor=tk.W)
            ttk.Entry(controls, textvariable=var, width=width).pack(fill=tk.X, pady=(0, 6))

        row("Cable length (m)", self.length)
        row("Start frequency", self.fmin)
        row("Stop frequency", self.fmax)
        ttk.Label(controls, text="Frequency units").pack(anchor=tk.W)
        ttk.Combobox(controls, textvariable=self.units, values=["Hz", "kHz", "MHz", "GHz"], state="readonly").pack(fill=tk.X, pady=(0, 6))
        ttk.Label(controls, text="Model").pack(anchor=tk.W)
        ttk.Combobox(controls, textvariable=self.mode, values=["Datasheet practical", "Physical RLCG", "Compare both"], state="readonly").pack(fill=tk.X, pady=(0, 6))
        ttk.Label(controls, text="Termination").pack(anchor=tk.W)
        ttk.Combobox(controls, textvariable=self.term, values=["Open circuit", "Short circuit", "Custom load"], state="readonly").pack(fill=tk.X, pady=(0, 6))
        row("Analyzer Zref (ohm)", self.zref)
        row("Custom load R (ohm)", self.load_r)
        row("Custom load X (ohm)", self.load_x)
        ttk.Label(controls, text="Datasheet attenuation").pack(anchor=tk.W)
        ttk.Combobox(controls, textvariable=self.source, values=["Table interpolation + formula outside table", "Formula only"], state="readonly").pack(fill=tk.X, pady=(0, 6))
        row("RLCG dielectric tan(delta)", self.tan_delta)
        row("RLCG conductor-loss scale", self.loss_scale)
        row("SWR display cap", self.swr_cap)
        row("Points per half-wave ripple", self.points_per_ripple)
        row("Maximum plotted points", self.max_points)
        ttk.Checkbutton(controls, text="Log x-axis", variable=self.logx).pack(anchor=tk.W)
        ttk.Checkbutton(controls, text="Sym-log impedance axis", variable=self.symlogz).pack(anchor=tk.W)
        ttk.Button(controls, text="Update plot", command=self.update).pack(fill=tk.X, pady=(10, 4))
        ttk.Button(controls, text="Export CSV", command=self.export_csv).pack(fill=tk.X, pady=4)
        ttk.Button(controls, text="Save figure", command=self.save_fig).pack(fill=tk.X, pady=4)
        self.status = tk.Text(controls, width=42, height=17, wrap=tk.WORD)
        self.status.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.fig, self.ax = plt.subplots(2, 2, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plots)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, plots).update()

    def freq_grid(self) -> tuple[np.ndarray, str]:
        mult = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9}[self.units.get()]
        f1 = max(float(self.fmin.get()) * mult, 1.0)
        f2 = max(float(self.fmax.get()) * mult, f1 * 1.001)
        length = max(float(self.length.get()), 1e-6)
        ripple = 0.84 * C0 / (2.0 * length)
        span = f2 - f1
        n = int(np.ceil(span / max(ripple / max(int(self.points_per_ripple.get()), 2), 1.0)))
        n = max(600, min(n, int(self.max_points.get())))
        if self.logx.get() or f2 / f1 > 100:
            f = np.logspace(np.log10(f1), np.log10(f2), n)
            msg = f"Log grid: {n:,} points. Half-wave impedance-rotation spacing is about {fmt_freq(ripple)}."
        else:
            f = np.linspace(f1, f2, n)
            msg = f"Linear grid: {n:,} points. Half-wave impedance-rotation spacing is about {fmt_freq(ripple)}."
        return f, msg

    def selected_results(self) -> tuple[dict[str, Result], str]:
        f, msg = self.freq_grid()
        length = float(self.length.get())
        zload = complex(float(self.load_r.get()), float(self.load_x.get()))
        zref = float(self.zref.get())
        out: dict[str, Result] = {}
        if self.mode.get() in ("Datasheet practical", "Compare both"):
            out["Datasheet practical"] = datasheet_model(f, length, self.term.get(), zload, zref, self.source.get())
        if self.mode.get() in ("Physical RLCG", "Compare both"):
            out["Physical RLCG"] = physical_model(f, length, self.term.get(), zload, zref, float(self.tan_delta.get()), float(self.loss_scale.get()))
        return out, msg

    def update(self) -> None:
        try:
            self.results, grid_msg = self.selected_results()
        except Exception as exc:
            messagebox.showerror("Model error", str(exc))
            return
        ax_swr, ax_loss, ax_z, ax_g = self.ax.ravel()
        for a in self.ax.ravel():
            a.clear()
        cap = max(float(self.swr_cap.get()), 2.0)
        for r in self.results.values():
            ax_swr.plot(r.f, np.minimum(r.swr, cap), label=r.name)
            if self.term.get() in ("Open circuit", "Short circuit"):
                ax_swr.plot(r.f, np.minimum(r.env_swr, cap), "--", lw=1, label=f"{r.name} envelope")
            ax_loss.plot(r.f, r.loss_db, label=r.name)
            ax_z.plot(r.f, np.real(r.zin), label=f"Re Zin {r.name}")
            ax_z.plot(r.f, np.imag(r.zin), "--", label=f"Im Zin {r.name}")
        f1, f2 = min(next(iter(self.results.values())).f), max(next(iter(self.results.values())).f)
        table_f = LMR400_TABLE_MHZ * 1e6
        m = (table_f >= f1) & (table_f <= f2)
        if np.any(m):
            ax_loss.scatter(table_f[m], LMR400_TABLE_DB_100FT[m] * float(self.length.get()) * FT_PER_M / 100.0, s=18, label="table points", zorder=3)
        theta = np.linspace(0, 2 * np.pi, 400)
        ax_g.plot(np.cos(theta), np.sin(theta), lw=0.8, label="|Γ|=1")
        for rad in (0.2, 0.5, 0.8):
            ax_g.plot(rad * np.cos(theta), rad * np.sin(theta), ":", lw=0.6)
        for r in self.results.values():
            step = max(1, len(r.f) // 5000)
            ax_g.plot(np.real(r.gamma[::step]), np.imag(r.gamma[::step]), label=r.name)
            ax_g.plot(np.real(r.gamma[0]), np.imag(r.gamma[0]), "o", ms=4)
            ax_g.plot(np.real(r.gamma[-1]), np.imag(r.gamma[-1]), "x", ms=5)
        ax_swr.set_title("Apparent SWR at analyzer")
        ax_swr.set_ylabel(f"SWR, capped at {cap:g}")
        ax_loss.set_title("One-way matched-line loss")
        ax_loss.set_ylabel("dB")
        ax_z.set_title("Input impedance transformation")
        ax_z.set_ylabel("ohms")
        ax_z.set_xlabel("frequency (Hz)")
        ax_g.set_title("Analyzer reflection coefficient Γ")
        ax_g.set_xlabel("Re(Γ)")
        ax_g.set_ylabel("Im(Γ)")
        ax_g.set_aspect("equal", adjustable="box")
        ax_g.set_xlim(-1.05, 1.05)
        ax_g.set_ylim(-1.05, 1.05)
        if self.logx.get() or f2 / f1 > 100:
            for a in (ax_swr, ax_loss, ax_z):
                a.set_xscale("log")
        if self.symlogz.get():
            ax_z.set_yscale("symlog", linthresh=50)
        for a in self.ax.ravel():
            a.grid(True, which="both", linestyle=":", alpha=0.5)
            a.legend(fontsize=7)
        self.fig.suptitle(f"LMR-400 long-line response | {float(self.length.get()):g} m | {self.term.get()}")
        self.fig.tight_layout(rect=(0, 0, 1, 0.96))
        self.canvas.draw_idle()
        self._status(grid_msg)

    def _status(self, grid_msg: str) -> None:
        lines = [grid_msg, "", "For open/short loads, impedance and phase rotate periodically, but ideal SWR magnitude mainly follows feedline attenuation.", ""]
        probes = [30e6, 146e6, 220e6, 446e6, 915e6, 2.4e9, 5.8e9]
        for r in self.results.values():
            lines.append(r.name)
            if r.warning:
                lines.append("  Warning: " + r.warning)
            for p in probes:
                if r.f.min() <= p <= r.f.max():
                    lines.append(f"  {fmt_freq(p):>10}: loss {np.interp(p, r.f, r.loss_db):5.2f} dB, SWR {np.interp(p, r.f, r.swr):6.2f}:1")
            lines.append("")
        self.status.configure(state=tk.NORMAL)
        self.status.delete("1.0", tk.END)
        self.status.insert(tk.END, "\n".join(lines).strip())
        self.status.configure(state=tk.DISABLED)

    def export_csv(self) -> None:
        if not self.results:
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="lmr400_long_line_results.csv")
        if not path:
            return
        first = next(iter(self.results.values()))
        cols = [first.f]
        headers = ["frequency_Hz"]
        for key, r in self.results.items():
            prefix = key.lower().replace(" ", "_")
            headers += [f"{prefix}_swr", f"{prefix}_one_way_loss_dB", f"{prefix}_zin_real_ohm", f"{prefix}_zin_imag_ohm", f"{prefix}_gamma_real", f"{prefix}_gamma_imag"]
            cols += [r.swr, r.loss_db, np.real(r.zin), np.imag(r.zin), np.real(r.gamma), np.imag(r.gamma)]
        with open(path, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(np.column_stack(cols))
        messagebox.showinfo("Export complete", f"Saved {path}")

    def save_fig(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")], initialfile="lmr400_long_line_visualizer.png")
        if path:
            self.fig.savefig(Path(path), dpi=200, bbox_inches="tight")
            messagebox.showinfo("Figure saved", f"Saved {path}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
