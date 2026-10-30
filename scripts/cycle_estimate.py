"""Pre-simulation cycle-time estimate from the RAPID path (trapezoidal motion model).
MoveL: TCP speed limited by speeddata, accel 4 m/s^2.  MoveJ: modelled as TCP move at an
effective 1.6 m/s with 4 m/s^2 accel (IRB 1300 joint speeds allow > 2 m/s at the TCP).
Fine points add 0.08 s settling. This is an ESTIMATE; replace with RobotStudio results."""
import numpy as np, csv, sys

A = 4000.0      # mm/s^2
def tmove(d, v, fine=False):
    d = abs(d)
    if d <= v*v/A: t = 2*np.sqrt(d/A)
    else: t = d/v + v/A
    return t + (0.08 if fine else 0.0)

W = {"conv": np.array([400,540,600]), "int": np.array([625,-275,630]), "box": np.array([-150,-750,406])}
CP1 = np.array([106.07,106.07,215]); CP2 = np.array([38.82,144.89,215])
slots = [(-272+(n%4)%2*280, -272+(n%4)//2*280, (n//4)*215) for n in range(8)]
vF, vA, vG = 1600, 600, 150

rows = []
for k, s in enumerate(slots):
    pc = W["conv"]+CP1; pi1 = W["int"]+CP1; pi2 = W["int"]+CP2; pb = W["box"]+CP2+np.array(s)
    seg = []
    prev_box_up = (W["box"]+CP2+np.array(slots[k-1]) + [0,0,350]) if k else np.array([0,0,1300])
    seg.append(("J box->conv", tmove(np.linalg.norm(prev_box_up-(pc+[0,0,150])), vF)))
    seg.append(("L approach", tmove(130, vA)+tmove(20, vG, True)))
    seg.append(("vacuum on", 0.2))
    seg.append(("L retract", tmove(150, vA)))
    seg.append(("J conv->int", tmove(np.linalg.norm((pc+[0,0,150])-(pi1+[0,0,150])), vF)))
    seg.append(("L place int", tmove(140, vA)+tmove(10, vG, True)))
    seg.append(("vacuum off", 0.2))
    seg.append(("L up + move to CP2", tmove(60, vA)+tmove(np.linalg.norm(pi1-pi2), vA, True)))
    seg.append(("gasket dwell", 1.5))
    seg.append(("L regrip", tmove(40, vA)+tmove(20, vG, True)))
    seg.append(("vacuum on", 0.2))
    seg.append(("L retract", tmove(150, vA)))
    seg.append(("J int->box", tmove(np.linalg.norm((pi2+[0,0,150])-(pb+[0,0,350])), vF)))
    seg.append(("L place box", tmove(320, vA)+tmove(30, vG, True)))
    seg.append(("vacuum off", 0.2))
    seg.append(("L retract", tmove(350, vA)))
    tot = sum(t for _, t in seg)
    rows.append((k+1, tot, seg))
    print(f"slot {k+1}: {tot:5.2f} s")
avg = np.mean([r[1] for r in rows])
print(f"average {avg:.2f} s  -> {3600/avg:.0f} parts/h")
# breakdown of an average cycle
cats = {}
for name, t in rows[3][2]:
    key = "Gasket dwell" if "gasket" in name else ("Vacuum on/off" if "vacuum" in name else
          ("Joint transfers (MoveJ)" if name.startswith("J") else "Linear approach/retract (MoveL)"))
    cats[key] = cats.get(key, 0) + t
for k, v in cats.items(): print(f"  {k:32s} {v:5.2f} s")
with open(sys.argv[1], "w", newline="") as f:
    w = csv.writer(f); w.writerow(["slot","est_cycle_s"]); [w.writerow([r[0], f"{r[1]:.2f}"]) for r in rows]
    w.writerow(["avg", f"{avg:.2f}"])
    for k, v in cats.items(): w.writerow([k, f"{v:.2f}"])
