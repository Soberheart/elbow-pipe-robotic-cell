"""Assemble all parts into one STL in the world frame (mm). Robot itself is not included
(it comes from the ABB library in RobotStudio); a simple cylinder marks its position."""
import numpy as np, struct, os, sys
CAD, OUT = sys.argv[1], sys.argv[2]
def load(n):
    with open(os.path.join(CAD, n), "rb") as f:
        f.read(80); k = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(k*50), dtype=np.dtype([("n","<3f4"),("v","<9f4"),("a","<u2")]))
    return d["v"].reshape(-1,3,3).astype(float)
def rx(a):
    c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def put(t, p, R=np.eye(3)): return t @ R.T + np.asarray(p, float)
def slab(x0,y0,z0,x1,y1,z1):
    p=np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],float)
    f=[]
    for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        f+=[(p[a],p[b],p[c]),(p[a],p[c],p[d])]
    return np.array(f)
def cyl(cx,cy,z0,z1,r,n=48):
    t=np.linspace(0,2*np.pi,n+1); f=[]
    for i in range(n):
        a=(cx+r*np.cos(t[i]),cy+r*np.sin(t[i])); b=(cx+r*np.cos(t[i+1]),cy+r*np.sin(t[i+1]))
        f+=[((*a,z0),(*b,z0),(*b,z1)),((*a,z0),(*b,z1),(*a,z1)),((cx,cy,z1),(*a,z1),(*b,z1)),((cx,cy,z0),(*b,z0),(*a,z0))]
    return np.array(f)
E, G = load("elbow_pipe.stl"), load("gasket.stl")
parts = [
  put(load("robot_stand.stl"), (0,0,0)),
  cyl(0,0,400,1100,110),                                   # robot placeholder (IRB 1300 envelope marker)
  put(load("interim_station.stl"), (700,-200,0)),
  put(load("box_conveyor.stl"), (-150,-750,0)),
  put(load("packing_box.stl"), (-150,-750,400)),
  slab(-300,450,560,1700,850,600),                         # infeed belt conveyor
  slab(-300,440,560,1700,450,620), slab(-300,850,560,1700,860,620),
  *[slab(x,y,0,x+40,y+40,560) for x in (-280,1640) for y in (460,800)],
  put(E,(400,540,600)), put(E,(1000,540,600)),             # parts on conveyor
  put(E,(625,-275,630)), put(G,(775,-275,737.5),rx(-np.pi/2)),   # part + gasket at interim
  *[put(E,(-150-272+i*280,-750-272+j*280,406)) for i,j in [(0,0),(1,0),(0,1)]],  # packed parts
]
tris = np.concatenate(parts)
with open(OUT,"wb") as fh:
    fh.write(b"cell_assembly".ljust(80,b" ")); fh.write(struct.pack("<I",len(tris)))
    for a,b,c in tris:
        n=np.cross(b-a,c-a); L=np.linalg.norm(n); n=n/L if L else n
        fh.write(struct.pack("<12fH",*n,*a,*b,*c,0))
print(len(tris),"triangles ->",OUT)
