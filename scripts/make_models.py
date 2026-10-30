"""Generate STL models (units: mm) for the MA6212 elbow-pipe pick-and-place cell.

Models
  elbow_pipe.stl      90 deg elbow, OD 215, wall 15 (ID 185), centre-to-end 150 (bend radius 150)
  gasket.stl          rubber ring seated in the pipe socket, OD 185, ID 161, width 20
  interim_station.stl gasket-insertion fixture: frame table + cradle + insertion unit
  packing_box.stl     open carton, inner 560 x 560 x 460, wall 6
  vacuum_gripper.stl  flange + body + bellows suction cup, TCP 175 mm from flange
  box_conveyor.stl    roller-conveyor table carrying the carton
  robot_stand.stl     pedestal for the IRB 1300
Origins are documented in the report (Assumptions table).
"""
import numpy as np, struct, os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "cad"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- primitives
def quad(a, b, c, d):
    return [(a, b, c), (a, c, d)]

def box(x0, y0, z0, x1, y1, z1):
    p = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
                  [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]], float)
    f = []
    for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        f += quad(p[a],p[b],p[c],p[d])
    return f

def tube_z(cx, cy, z0, z1, ro, ri=0.0, n=64):
    """Cylinder (ri=0) or annulus along +z."""
    t = np.linspace(0, 2*np.pi, n+1)
    f = []
    for i in range(n):
        c0, s0, c1, s1 = np.cos(t[i]), np.sin(t[i]), np.cos(t[i+1]), np.sin(t[i+1])
        o0b = (cx+ro*c0, cy+ro*s0, z0); o1b = (cx+ro*c1, cy+ro*s1, z0)
        o0t = (cx+ro*c0, cy+ro*s0, z1); o1t = (cx+ro*c1, cy+ro*s1, z1)
        f += quad(o0b, o1b, o1t, o0t)
        if ri > 0:
            i0b = (cx+ri*c0, cy+ri*s0, z0); i1b = (cx+ri*c1, cy+ri*s1, z0)
            i0t = (cx+ri*c0, cy+ri*s0, z1); i1t = (cx+ri*c1, cy+ri*s1, z1)
            f += quad(i1b, i0b, i0t, i1t)
            f += quad(o0t, o1t, i1t, i0t)
            f += quad(o1b, o0b, i0b, i1b)
        else:
            f += [((cx,cy,z1), o0t, o1t), ((cx,cy,z0), o1b, o0b)]
    return f

def transform(faces, R=np.eye(3), t=(0,0,0)):
    t = np.asarray(t, float)
    return [tuple(R @ np.asarray(v, float) + t for v in tri) for tri in faces]

def rot_x(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rot_y(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def rot_z(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def elbow(R=150.0, ro=107.5, ri=92.5, ang=np.pi/2, nb=48, nc=64):
    """Annular torus segment. Bend plane = XY, bend centre at origin,
    pipe axis at height z = ro so the elbow rests flat on z = 0.
    End A at theta = 0 (face normal -Y), end B at theta = 90 deg (face normal -X)."""
    th = np.linspace(0, ang, nb+1); ph = np.linspace(0, 2*np.pi, nc+1)
    def P(r, a, p):   # centreline angle a, circle angle p, tube radius r
        rr = R + r*np.cos(p)
        return (rr*np.cos(a), rr*np.sin(a), ro + r*np.sin(p))
    f = []
    for i in range(nb):
        for j in range(nc):
            a0,a1,p0,p1 = th[i],th[i+1],ph[j],ph[j+1]
            f += quad(P(ro,a0,p0), P(ro,a1,p0), P(ro,a1,p1), P(ro,a0,p1))
            f += quad(P(ri,a0,p1), P(ri,a1,p1), P(ri,a1,p0), P(ri,a0,p0))
    for j in range(nc):   # end caps
        p0, p1 = ph[j], ph[j+1]
        f += quad(P(ro,0,p1), P(ro,0,p0), P(ri,0,p0), P(ri,0,p1))
        f += quad(P(ro,ang,p0), P(ro,ang,p1), P(ri,ang,p1), P(ri,ang,p0))
    return f

# ---------------------------------------------------------------- writer
def write_stl(name, faces):
    path = os.path.join(OUT, name)
    with open(path, "wb") as fh:
        fh.write(name.encode()[:80].ljust(80, b" "))
        fh.write(struct.pack("<I", len(faces)))
        for a, b, c in faces:
            a, b, c = map(np.asarray, (a, b, c))
            n = np.cross(b-a, c-a); L = np.linalg.norm(n); n = n/L if L else n
            fh.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    print(f"{name:22s} {len(faces):7d} triangles")
    return faces

models = {}

# 1 elbow pipe
models["elbow_pipe.stl"] = write_stl("elbow_pipe.stl", elbow())

# 2 gasket: ring lying in XY, centred at origin, z 0..20
models["gasket.stl"] = write_stl("gasket.stl", tube_z(0, 0, 0, 20, 92.5, 80.5, 72))

# 3 interim station (origin = centre of table top at floor level; top surface z = 600)
st = []
st += box(-300, -250, 560, 300, 250, 600)                         # table top
for x in (-280, 260):
    for y in (-230, 210):
        st += box(x, y, 0, x+20, y+20, 560)                        # legs
st += box(-300, -250, 100, 300, -230, 130) + box(-300, 230, 100, 300, 250, 130)  # rails
# cradle: two blocks supporting the elbow lying flat (elbow origin placed at (-75,-75,630))
st += box(-60, -110, 600, 120, -40, 630)                           # support under leg A
st += box(-110, -60, 600, -40, 120, 630)                           # support under leg B
st += box(-20, -20, 600, 20, 20, 630)                              # centre locating block
# gasket insertion unit facing end A (end A face at y = -75, opening towards -y)
st += box(-40, -250, 600, 190, -215, 760)                          # back plate
st += transform(tube_z(0, 0, 0, 60, 30), rot_x(-np.pi/2), (75, -215, 705))  # press cylinder
st += box(-40, -250, 760, 190, -100, 780)                          # gasket magazine shelf
models["interim_station.stl"] = write_stl("interim_station.stl", st)

# 4 packing box (origin = centre of the box floor, outer 572 x 572 x 466)
w, h, t = 286, 466, 6
pb = []
pb += box(-w, -w, 0, w, w, t)
pb += box(-w, -w, t, -w+t, w, h) + box(w-t, -w, t, w, w, h)
pb += box(-w+t, -w, t, w-t, -w+t, h) + box(-w+t, w-t, t, w-t, w, h)
pb += transform(box(0, -w, 0, 4, w, 180), rot_y(np.radians(-30)), (-w, 0, h))   # open flaps
pb += transform(box(-4, -w, 0, 0, w, 180), rot_y(np.radians(30)), (w, 0, h))
models["packing_box.stl"] = write_stl("packing_box.stl", pb)

# 5 vacuum gripper (origin = robot flange, +z = tool direction), TCP at z = 175
g = []
g += tube_z(0, 0, 0, 12, 40)                                       # flange adapter
g += box(-30, -30, 12, 30, 30, 110)                                # vacuum generator body
g += tube_z(0, 0, 110, 140, 14)                                    # stem
g += tube_z(0, 0, 140, 150, 22)                                    # cup holder
for k, (r0, r1) in enumerate([(24, 30), (30, 26), (26, 33)]):      # bellows (3 folds)
    g += tube_z(0, 0, 150+k*8, 158+k*8, max(r0, r1), min(r0, r1)-3)
g += tube_z(0, 0, 174, 175, 33, 28)                                # sealing lip = TCP plane
g += transform(box(0, -8, 0, 40, 8, 16), np.eye(3), (30, 0, 60))   # air fitting
models["vacuum_gripper.stl"] = write_stl("vacuum_gripper.stl", g)

# 6 roller conveyor for cartons (origin = centre, top of rollers z = 400, length along X)
L, W = 1400, 700
bc = []
bc += box(-L/2, -W/2, 360, L/2, -W/2+30, 400) + box(-L/2, W/2-30, 360, L/2, W/2, 400)
for x in np.arange(-L/2+50, L/2, 100):
    bc += transform(tube_z(0, 0, -W/2+30, W/2-30, 25, 0, 24), rot_x(np.pi/2), (x, 0, 375))
for x in (-L/2, L/2-40):
    for y in (-W/2, W/2-40):
        bc += box(x, y, 0, x+40, y+40, 360)
models["box_conveyor.stl"] = write_stl("box_conveyor.stl", bc)

# 7 robot stand (origin floor centre, top z = 400)
rs = box(-200, -200, 0, 200, 200, 20) + box(-150, -150, 20, 150, 150, 380) + box(-200, -200, 380, 200, 200, 400)
models["robot_stand.stl"] = write_stl("robot_stand.stl", rs)

# mass check for the elbow
R, ro, ri = 150, 107.5, 92.5
vol = np.pi*(ro**2-ri**2) * R*np.pi/2           # mm^3 (Pappus)
print(f"elbow volume {vol/1e6:.3f} L  -> density for 2.5 kg = {2.5/(vol/1e6):.2f} g/cm3")
