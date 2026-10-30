"""Top-view layout of the cell (world frame, mm) + reach check."""
import numpy as np, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge, FancyArrowPatch, Annulus

out = sys.argv[1]
fig, ax = plt.subplots(figsize=(11, 9))
def rect(x0, y0, x1, y1, fc, ec="#333", lab=None, a=1, lw=1.2, ls="-"):
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fc=fc, ec=ec, alpha=a, lw=lw, ls=ls))
    if lab: ax.text((x0+x1)/2, (y0+y1)/2, lab, ha="center", va="center", fontsize=9.5)
def elbow(ox, oy, col="#222"):
    ax.add_patch(Wedge((ox, oy), 257.5, 0, 90, width=215, fc=col, ec="k", lw=0.6, alpha=0.85))

# reach envelope IRB 1300-7/1.4 (approx. wrist-centre reach 1400 mm)
ax.add_patch(Circle((0, 0), 1400, fc="#eaf2fb", ec="#3b6ea8", ls="--", lw=1.2, alpha=0.6))
ax.text(-1200, 1150, "IRB 1300-7/1.4 reach ≈ 1400 mm (dashed)", color="#3b6ea8", fontsize=9)
# fence
rect(-1250, -1300, 1700, 1250, "none", ec="#d4ac0d", lw=2.2, ls="-.")
ax.text(1680, 1220, "Safety fence", ha="right", va="top", color="#b7950b", fontsize=9)
# infeed belt conveyor
rect(-300, 450, 1700, 850, "#555", lab=None)
ax.text(1250, 650, "Infeed belt conveyor  (z = 600)\n← flow", color="w", ha="center", va="center", fontsize=9.5)
elbow(400, 540, "#111"); elbow(1000, 540, "#333")
ax.add_patch(Circle((400+106.1, 540+106.1), 30, fc="none", ec="red", lw=2))
ax.add_patch(Rectangle((400-60, 540-60), 377.5, 377.5, fc="none", ec="red", ls=":", lw=1.2))
ax.text(400-60, 540+330, "Vision ROI / wobjConv\n(random ±20 mm, ±10°)", color="red", fontsize=8.5)
# interim station
rect(400, -450, 1000, 50, "#c9d3de", lab=None)
rect(660, -450, 890, -415, "#7a8fa6")
ax.text(700, 15, "Interim gasket station (z = 600)", fontsize=9.5, va="top")
elbow(625, -275, "#111")
ax.add_patch(Rectangle((760, -450), 30, 175, fc="#8a5a2b", ec="k"))
ax.text(800, -470, "gasket press", fontsize=8.5, va="top")
ax.add_patch(Circle((625+38.8, -275+144.9), 30, fc="none", ec="orange", lw=2))
ax.add_patch(Circle((625+106.1, -275+106.1), 30, fc="none", ec="red", lw=2, ls="--"))
# box conveyor + carton
rect(-850, -1100, 550, -400, "#d5dbe1", lab=None)
ax.text(-820, -1080, "Carton roller conveyor (z = 400)  → out", fontsize=9)
rect(-436, -1036, 136, -464, "#e8d3a8")
for i in range(2):
    for j in range(2):
        ox, oy = -150-272+i*280, -750-272+j*280
        ax.add_patch(Rectangle((ox, oy), 257.5, 257.5, fc="none", ec="#7d5a2b", ls=":"))
        ax.text(ox+128, oy+128, f"slot {1+i+2*j}\n(+{5+i+2*j} on layer 2)", ha="center", va="center", fontsize=7.5)
elbow(-150-272, -750-272, "#222")
ax.text(-150, -440, "Packing box  inner 560×560×460", ha="center", fontsize=9)
# robot
ax.add_patch(Circle((0, 0), 200, fc="#f4f6f7", ec="k", lw=1.5))
ax.text(0, 0, "IRB 1300\n(on 400 mm\nstand)", ha="center", va="center", fontsize=9)
# path arrows
kw = dict(arrowstyle="-|>", mutation_scale=18, lw=2)
ax.add_patch(FancyArrowPatch((506, 646), (731, -169), connectionstyle="arc3,rad=-0.35", color="#c0392b", **kw))
ax.add_patch(FancyArrowPatch((664, -130), (-286, -886), connectionstyle="arc3,rad=-0.35", color="#e67e22", **kw))
ax.text(900, 250, "① pick → interim", color="#c0392b", fontsize=10)
ax.text(-120, -250, "② re-grip → box", color="#e67e22", fontsize=10)
ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", mfc="none", mec="red", ms=10, mew=2, label="Contact point CP1"),
                   plt.Line2D([], [], marker="o", ls="", mfc="none", mec="orange", ms=10, mew=2, label="Contact point CP2")],
          loc="lower right", fontsize=9)
ax.set_xlim(-1350, 1800); ax.set_ylim(-1400, 1350); ax.set_aspect("equal")
ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.grid(alpha=0.3)
ax.set_title("Work-cell layout – top view (world frame, robot base at origin)")
fig.tight_layout(); fig.savefig(out, dpi=160)

# reach check (wrist centre ≈ TCP + 175 mm tool + ~ 80 mm wrist, robot base z = 400, shoulder z ≈ 400+544)
pts = {"conveyor CP1": (506, 646, 815), "interim CP1 place": (731, -169, 845),
       "interim CP2 re-grip": (664, -130, 845), "box slot1 L1": (-316, -916, 621),
       "box slot4 L1": (-36, -636, 621), "box slot1 L2": (-316, -916, 836)}
for k, (x, y, z) in pts.items():
    print(f"{k:22s} horiz {np.hypot(x,y):6.0f} mm   height above base {z-400:5.0f} mm")
