import numpy as np
def slab(x0,y0,z0,x1,y1,z1):
    p = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]], float)
    f = []
    for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        f += [(p[a],p[b],p[c]), (p[a],p[c],p[d])]
    return np.array(f)
