"""Render STL previews and the assembled cell layout (matplotlib)."""
import numpy as np, struct, sys, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

CAD, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

def load(name):
    with open(os.path.join(CAD, name), "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n*50), dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")]))
    return d["v"].reshape(-1, 3, 3).astype(float)

def rz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def rx(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])

def place(tris, t=(0,0,0), R=np.eye(3)):
    return tris @ R.T + np.asarray(t, float)

LIGHT = np.array([0.4, -0.5, 0.8]); LIGHT /= np.linalg.norm(LIGHT)
def add(ax, tris, color, alpha=1.0, edge=False):
    n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.45 + 0.55*np.abs(n @ LIGHT)
    base = np.array(matplotlib.colors.to_rgb(color))
    fc = np.clip(base[None,:]*shade[:,None], 0, 1)
    pc = Poly3DCollection(tris, facecolors=fc, alpha=alpha,
                          edgecolors=(0,0,0,0.15) if edge else "none", linewidths=0.2)
    ax.add_collection3d(pc)

def finish(ax, pts, title, elev=25, azim=-60):
    mn, mx = pts.min((0,1)), pts.max((0,1)); c = (mn+mx)/2; r = (mx-mn).max()/2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect((1,1,1)); ax.view_init(elev, azim)
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)"); ax.set_zlabel("Z (mm)")
    ax.set_title(title, fontsize=12)

# ---- individual models
items = [("elbow_pipe.stl","#2b2b2b","Elbow pipe (OD 215 / ID 185, R 150)"),
         ("gasket.stl","#8a5a2b","Gasket ring (OD 185 / ID 161 x 20)"),
         ("interim_station.stl","#7a8fa6","Interim gasket station"),
         ("packing_box.stl","#c8a165","Packing box (inner 560x560x460)"),
         ("vacuum_gripper.stl","#d0d0d0","Vacuum suction gripper (TCP z=175)"),
         ("box_conveyor.stl","#9aa5b1","Carton roller conveyor")]
fig = plt.figure(figsize=(15, 9.5))
for k, (name, col, title) in enumerate(items):
    ax = fig.add_subplot(2, 3, k+1, projection="3d")
    tr = load(name); add(ax, tr, col, edge=name in ("interim_station.stl","packing_box.stl"))
    finish(ax, tr, title)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_models.png"), dpi=150); plt.close(fig)

# ---- assembled layout (world frame, robot base at (0,0,400) on stand)
LAY = {
  "stand":    ("robot_stand.stl", (0,0,0)),
  "interim":  ("interim_station.stl", (700,-200,0)),
  "boxconv":  ("box_conveyor.stl", (-150,-750,0)),
  "box":      ("packing_box.stl", (-150,-750,400)),
}
fig = plt.figure(figsize=(13, 10)); ax = fig.add_subplot(111, projection="3d")
allp = []
def put(tr, col, a=1.0, e=False):
    add(ax, tr, col, a, e); allp.append(tr)
put(place(load("robot_stand.stl")), "#5d6d7e", e=True)
put(place(load("interim_station.stl"), (700,-200,0)), "#7a8fa6", e=True)
put(place(load("box_conveyor.stl"), (-150,-750,0)), "#9aa5b1")
put(place(load("packing_box.stl"), (-150,-750,400)), "#c8a165", 0.55, True)
# infeed belt conveyor (drawn as slab), surface z = 600, along X, centred y = 650
from make_models_helpers import slab  # noqa: E402  (helper module next to this script)
put(slab(-200, 450, 0, 1600, 850, 600), "#3d3d3d")
put(slab(-200, 440, 560, 1600, 450, 620), "#b0b7bf"); put(slab(-200, 850, 560, 1600, 860, 620), "#b0b7bf")
# fence (low wireframe panels)
put(slab(-900,-1250,0,-890,1100,1600), "#f1c40f", 0.12)
put(slab(-900,-1250,0,1700,-1240,1600), "#f1c40f", 0.12)
elbow = load("elbow_pipe.stl"); gask = load("gasket.stl")
for x in (400, 1000):                                   # parts on infeed (pick one + queued)
    put(place(elbow, (x, 540, 600)), "#1f1f1f")
put(place(elbow, (625, -275, 630)), "#1f1f1f")          # at interim station
put(place(gask, (775, -275-0.0, 737.5), rx(-np.pi/2)) @ np.eye(3), "#8a5a2b")  # gasket at end A
for (i, j) in [(0,0),(1,0),(0,1)]:                       # 3 parts already packed
    put(place(elbow, (-150-272+i*280, -750-272+j*280, 406)), "#1f1f1f")
# robot placeholder (IRB 1300 is loaded from the ABB library in RobotStudio)
put(place(load("robot_stand.stl"), (0,0,400), np.diag([0.55,0.55,1.2])), "#f4f6f7", e=True)
# key frames
for (p, lab) in [((506,646,815),"pick (CP1)"),((731,-169,845),"interim"),((-150,-750,880),"box"),((0,0,900),"IRB 1300")]:
    ax.text(*p, lab, fontsize=10, color="crimson")
pts = np.concatenate([a.reshape(-1,3) for a in allp])[:, None, :]
finish(ax, pts, "Work-cell layout (world frame, mm)", elev=28, azim=-125)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_layout_top_3d_unused.png"), dpi=150); plt.close(fig)
print("rendered")
