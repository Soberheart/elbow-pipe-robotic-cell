"""Generate a CATIA V5 VBScript macro (.catvbs) that builds every cell part natively
(Part Design pads / shaft), saves them as CATPart + STEP, and assembles a CATProduct.

Robustness choices (macro can't be test-run here):
  * every sketch gets an explicit frame via SetAbsoluteAxisData (origin, H, V)
  * every pad is symmetric about its mid-plane, so pad direction never matters
  * the elbow shaft is symmetric (+/-45 deg) and rotated +45 deg about Z in the product
Geometry is identical to make_models.py (units mm)."""
import sys, numpy as np

OUT = sys.argv[1]

# ---------------- part definitions: primitives in each part's own frame
# ("box", x0,y0,z0,x1,y1,z1) | ("cylz", cx,cy,z0,z1,ro,ri) | ("cyly", cx,cz,y0,y1,r) | ("elbow",)
P = {}
P["elbow_pipe"] = [("elbow",)]
P["gasket"] = [("cylz", 0, 0, 0, 20, 92.5, 80.5)]
st = [("box", -300, -250, 560, 300, 250, 600)]
for x in (-280, 260):
    for y in (-230, 210):
        st.append(("box", x, y, 0, x+20, y+20, 560))
st += [("box", -300, -250, 100, 300, -230, 130), ("box", -300, 230, 100, 300, 250, 130),
       ("box", -60, -110, 600, 120, -40, 630), ("box", -110, -60, 600, -40, 120, 630),
       ("box", -20, -20, 600, 20, 20, 630), ("box", -40, -250, 600, 190, -215, 760),
       ("cyly", 75, 737.5, -215, -155, 30), ("box", -40, -250, 760, 190, -100, 780)]
P["interim_station"] = st
w, h, t = 286, 466, 6
P["packing_box"] = [("box", -w, -w, 0, w, w, t), ("box", -w, -w, t, -w+t, w, h), ("box", w-t, -w, t, w, w, h),
                    ("box", -w+t, -w, t, w-t, -w+t, h), ("box", -w+t, w-t, t, w-t, w, h)]
P["vacuum_gripper"] = [("cylz", 0, 0, 0, 12, 40, 0), ("box", -30, -30, 12, 30, 30, 110), ("cylz", 0, 0, 110, 140, 14, 0),
                       ("cylz", 0, 0, 140, 150, 22, 0), ("cylz", 0, 0, 150, 158, 30, 21), ("cylz", 0, 0, 158, 166, 30, 23),
                       ("cylz", 0, 0, 166, 175, 33, 23), ("box", 30, -8, 60, 70, 8, 76)]
L, W = 1400, 700
bc = [("box", -L/2, -W/2, 360, L/2, -W/2+30, 400), ("box", -L/2, W/2-30, 360, L/2, W/2, 400)]
for x in np.arange(-L/2+50, L/2, 100):
    bc.append(("cyly", float(x), 375, -W/2+30, W/2-30, 25))
for x in (-L/2, L/2-40):
    for y in (-W/2, W/2-40):
        bc.append(("box", x, y, 0, x+40, y+40, 360))
P["box_conveyor"] = bc
P["robot_stand"] = [("box", -200, -200, 0, 200, 200, 20), ("box", -150, -150, 20, 150, 150, 380), ("box", -200, -200, 380, 200, 200, 400)]
P["infeed_conveyor"] = [("box", -300, 450, 560, 1700, 850, 600), ("box", -300, 440, 560, 1700, 450, 620),
                        ("box", -300, 850, 560, 1700, 860, 620)] + \
                       [("box", x, y, 0, x+40, y+40, 560) for x in (-280, 1640) for y in (460, 800)]
P["robot_marker"] = [("cylz", 0, 0, 400, 1100, 110, 0)]

# ---------------- assembly: (instance name, part, rotation 3x3, translation)
I3 = np.eye(3)
c, s = np.cos(np.pi/4), np.sin(np.pi/4)
RZ45 = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])           # elbow part frame -> STL frame
RXm90 = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])          # gasket axis Z -> +Y
A = [("Robot_Stand", "robot_stand", I3, (0, 0, 0)),
     ("Robot_IRB1300_Marker", "robot_marker", I3, (0, 0, 0)),
     ("Infeed_Conveyor", "infeed_conveyor", I3, (0, 0, 0)),
     ("Interim_Station", "interim_station", I3, (700, -200, 0)),
     ("Box_Conveyor", "box_conveyor", I3, (-150, -750, 0)),
     ("Packing_Box", "packing_box", I3, (-150, -750, 400)),
     ("Elbow_OnConveyor_1", "elbow_pipe", RZ45, (400, 540, 600)),
     ("Elbow_OnConveyor_2", "elbow_pipe", RZ45, (1000, 540, 600)),
     ("Elbow_AtInterim", "elbow_pipe", RZ45, (625, -275, 630)),
     ("Gasket_AtInterim", "gasket", RXm90, (775, -275, 737.5))]
for n, (i, j) in enumerate([(0, 0), (1, 0), (0, 1)]):
    A.append((f"Elbow_InBox_{n+1}", "elbow_pipe", RZ45, (-150-272+i*280, -750-272+j*280, 406)))

# ---------------- VBScript emitter
f = lambda v: f"{float(v):.10f}".rstrip("0").rstrip(".") if abs(float(v)) > 1e-9 else "0"
L_ = []
w_ = L_.append
w_("' ==========================================================================")
w_("' Elbow-pipe robotic cell - CATIA V5 builder macro (VBScript, .catvbs)")
w_("' Tools > Macro > Macros... > Macro libraries: add the folder of this file,")
w_("' select build_cell_catia.catvbs > Run.  Builds parts as CATPart + STEP and")
w_("' the assembly cell_assembly.CATProduct (+ STEP) in the chosen folder.")
w_("' Units: mm.  World frame = robot base centre on the floor.")
w_("' ==========================================================================")
w_("Dim gPart, gBody, gSF, gHSF, gHB, gN")
w_("")
w_("Sub NewSketch(a, b, c, d, ox, oy, oz, hx, hy, hz, vx, vy, vz, sk)")
w_("    Dim pl, ref")
w_("    Set pl = gHSF.AddNewPlaneEquation(a, b, c, d)")
w_("    gHB.AppendHybridShape pl")
w_("    pl.Name = \"Plane_\" & gN")
w_("    gPart.InWorkObject = gBody")
w_("    Set ref = gPart.CreateReferenceFromObject(pl)")
w_("    Set sk = gBody.Sketches.Add(ref)")
w_("    sk.SetAbsoluteAxisData Array(ox, oy, oz, hx, hy, hz, vx, vy, vz)")
w_("    gN = gN + 1")
w_("End Sub")
w_("")
w_("Sub Rect(f2d, x0, y0, x1, y1)")
w_("    Dim p1, p2, p3, p4, l1, l2, l3, l4")
w_("    Set p1 = f2d.CreatePoint(x0, y0): Set p2 = f2d.CreatePoint(x1, y0)")
w_("    Set p3 = f2d.CreatePoint(x1, y1): Set p4 = f2d.CreatePoint(x0, y1)")
w_("    Set l1 = f2d.CreateLine(x0, y0, x1, y0): l1.StartPoint = p1: l1.EndPoint = p2")
w_("    Set l2 = f2d.CreateLine(x1, y0, x1, y1): l2.StartPoint = p2: l2.EndPoint = p3")
w_("    Set l3 = f2d.CreateLine(x1, y1, x0, y1): l3.StartPoint = p3: l3.EndPoint = p4")
w_("    Set l4 = f2d.CreateLine(x0, y1, x0, y0): l4.StartPoint = p4: l4.EndPoint = p1")
w_("End Sub")
w_("")
w_("Sub SymPad(sk, length)")
w_("    Dim pad")
w_("    gPart.InWorkObject = gBody")
w_("    Set pad = gSF.AddNewPad(sk, length)")
w_("    pad.IsSymmetric = True")
w_("    gPart.Update")
w_("End Sub")
w_("")
w_("' box between (x0,y0,z0) and (x1,y1,z1): XY sketch at mid height, symmetric pad")
w_("Sub BoxP(x0, y0, z0, x1, y1, z1)")
w_("    Dim sk, f2d, zm")
w_("    zm = (z0 + z1) / 2")
w_("    NewSketch 0, 0, 1, zm, 0, 0, zm, 1, 0, 0, 0, 1, 0, sk")
w_("    Set f2d = sk.OpenEdition()")
w_("    Rect f2d, x0, y0, x1, y1")
w_("    sk.CloseEdition")
w_("    SymPad sk, z1 - z0")
w_("End Sub")
w_("")
w_("' cylinder / tube along Z")
w_("Sub CylZ(cx, cy, z0, z1, ro, ri)")
w_("    Dim sk, f2d, zm, c1, c2")
w_("    zm = (z0 + z1) / 2")
w_("    NewSketch 0, 0, 1, zm, 0, 0, zm, 1, 0, 0, 0, 1, 0, sk")
w_("    Set f2d = sk.OpenEdition()")
w_("    Set c1 = f2d.CreateClosedCircle(cx, cy, ro)")
w_("    If ri > 0 Then Set c2 = f2d.CreateClosedCircle(cx, cy, ri)")
w_("    sk.CloseEdition")
w_("    SymPad sk, z1 - z0")
w_("End Sub")
w_("")
w_("' cylinder along Y (sketch in plane y = ym, H = X, V = Z)")
w_("Sub CylY(cx, cz, y0, y1, r)")
w_("    Dim sk, f2d, ym, c1")
w_("    ym = (y0 + y1) / 2")
w_("    NewSketch 0, 1, 0, ym, 0, ym, 0, 1, 0, 0, 0, 0, 1, sk")
w_("    Set f2d = sk.OpenEdition()")
w_("    Set c1 = f2d.CreateClosedCircle(cx, cz, r)")
w_("    sk.CloseEdition")
w_("    SymPad sk, y1 - y0")
w_("End Sub")
w_("")
w_("' 90 deg elbow: section OD 215 / ID 185 centred at (150, 0, 107.5), revolved")
w_("' about the Z axis +/-45 deg. (Rotated +45 deg about Z in the assembly.)")
w_("Sub Elbow()")
w_("    Dim sk, f2d, c1, c2, ax, sh")
w_("    NewSketch 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, sk")
w_("    Set f2d = sk.OpenEdition()")
w_("    Set c1 = f2d.CreateClosedCircle(150, 107.5, 107.5)")
w_("    Set c2 = f2d.CreateClosedCircle(150, 107.5, 92.5)")
w_("    Set ax = f2d.CreateLine(0, -50, 0, 400)")
w_("    ax.Construction = True")
w_("    sk.CenterLine = ax")
w_("    sk.CloseEdition")
w_("    gPart.InWorkObject = gBody")
w_("    Set sh = gSF.AddNewShaft(sk)")
w_("    sh.FirstAngle.Value = 45")
w_("    sh.SecondAngle.Value = 45")
w_("    gPart.Update")
w_("End Sub")
w_("")
w_("Function StartPart(name)")
w_("    Dim doc")
w_("    Set doc = CATIA.Documents.Add(\"Part\")")
w_("    doc.Product.PartNumber = name")
w_("    Set gPart = doc.Part")
w_("    Set gBody = gPart.MainBody")
w_("    Set gSF = gPart.ShapeFactory")
w_("    Set gHSF = gPart.HybridShapeFactory")
w_("    Set gHB = gPart.HybridBodies.Add()")
w_("    gHB.Name = \"Construction_Planes\"")
w_("    gN = 1")
w_("    Set StartPart = doc")
w_("End Function")
w_("")
w_("Sub FinishPart(doc, folder, name)")
w_("    gPart.Update")
w_("    ' hide construction planes")
w_("    Dim sel: Set sel = doc.Selection")
w_("    sel.Clear: sel.Add gHB: sel.VisProperties.SetShow 1: sel.Clear")
w_("    doc.SaveAs folder & \"\\\" & name & \".CATPart\"")
w_("    On Error Resume Next")
w_("    doc.ExportData folder & \"\\\" & name & \".stp\", \"stp\"")
w_("    If Err.Number <> 0 Then gStepFail = gStepFail & \" \" & name: Err.Clear")
w_("    On Error GoTo 0")
w_("End Sub")
w_("")
w_("Dim gStepFail")
w_("")
w_("Sub CATMain()")
w_("    Dim folder, fso, docs, d, prodDoc, prods, comp")
w_("    folder = InputBox(\"Folder to save the parts and assembly:\", \"Elbow cell builder\", \"C:\\ElbowCell_CATIA\")")
w_("    If folder = \"\" Then Exit Sub")
w_("    Set fso = CreateObject(\"Scripting.FileSystemObject\")")
w_("    If Not fso.FolderExists(folder) Then fso.CreateFolder folder")
w_("    CATIA.DisplayFileAlerts = False")
w_("    Set docs = CreateObject(\"Scripting.Dictionary\")")
w_("    gStepFail = \"\"")
for name, prims in P.items():
    w_("")
    w_(f"    ' ---- {name} ({len(prims)} features)")
    w_(f"    Set d = StartPart(\"{name}\")")
    for p in prims:
        k = p[0]
        if k == "box":
            w_("    BoxP " + ", ".join(f(v) for v in p[1:]))
        elif k == "cylz":
            w_("    CylZ " + ", ".join(f(v) for v in p[1:]))
        elif k == "cyly":
            w_("    CylY " + ", ".join(f(v) for v in p[1:]))
        elif k == "elbow":
            w_("    Elbow")
    w_(f"    FinishPart d, folder, \"{name}\"")
    w_(f"    docs.Add \"{name}\", d")
w_("")
w_("    ' ---- assembly")
w_("    Set prodDoc = CATIA.Documents.Add(\"Product\")")
w_("    prodDoc.Product.PartNumber = \"cell_assembly\"")
w_("    Set prods = prodDoc.Product.Products")
for inst, part, R, t in A:
    arr = list(R[:, 0]) + list(R[:, 1]) + list(R[:, 2]) + list(t)
    w_(f"    Set comp = prods.AddExternalComponent(docs.Item(\"{part}\"))")
    w_(f"    comp.Name = \"{inst}\"")
    w_("    comp.Move.Apply Array(" + ", ".join(f(v) for v in arr) + ")")
w_("    prodDoc.Product.Update")
w_("    prodDoc.SaveAs folder & \"\\cell_assembly.CATProduct\"")
w_("    On Error Resume Next")
w_("    prodDoc.ExportData folder & \"\\cell_assembly.stp\", \"stp\"")
w_("    If Err.Number <> 0 Then gStepFail = gStepFail & \" cell_assembly\": Err.Clear")
w_("    On Error GoTo 0")
w_("    CATIA.DisplayFileAlerts = True")
w_("    If gStepFail = \"\" Then")
w_("        MsgBox \"Done. CATPart, CATProduct and STEP files saved in \" & folder")
w_("    Else")
w_("        MsgBox \"Done. CATPart / CATProduct saved in \" & folder & vbCrLf & \"STEP export failed for:\" & gStepFail & vbCrLf & \"(use File > Save As > .stp manually)\"")
w_("    End If")
w_("End Sub")

open(OUT, "w", encoding="utf-8", newline="\r\n").write("\n".join(L_) + "\n")
print(OUT, len(L_), "lines;", sum(len(v) for v in P.values()), "features;", len(A), "instances")
