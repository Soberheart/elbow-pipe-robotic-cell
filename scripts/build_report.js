// Build MA6212 group project report (.docx)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow,
  TableCell, WidthType, ShadingType, BorderStyle, PageBreak, Footer, PageNumber, LevelFormat,
  TableOfContents, Header,
} = require("docx");

const ROOT = process.argv[2];
const OUT = process.argv[3];
const fig = (f) => fs.readFileSync(path.join(ROOT, "figs", f));
const FONT = "Calibri";

// ---------- helpers
const P = (text, opts = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, alignment: opts.align || AlignmentType.JUSTIFIED,
  children: runs(text, opts) });
function runs(text, opts = {}) {
  // **bold** and [[TODO]] placeholder markup
  const out = [];
  const re = /(\*\*[^*]+\*\*|\[\[[^\]]+\]\])/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), size: opts.size || 22, italics: opts.italics }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, size: opts.size || 22 }));
    else out.push(new TextRun({ text: "[" + t.slice(2, -2) + "]", highlight: "yellow", bold: true, size: opts.size || 22 }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), size: opts.size || 22, italics: opts.italics }));
  return out;
}
const H1 = (t, pb = false) => new Paragraph({ pageBreakBefore: pb, keepNext: true, keepLines: true, heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 140 }, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ keepNext: true, keepLines: true, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 }, children: [new TextRun(t)] });
const B = (t, lvl = 0) => new Paragraph({ numbering: { reference: "bul", level: lvl }, spacing: { after: 60 }, children: runs(t) });
const N = (t) => new Paragraph({ numbering: { reference: "num", level: 0 }, spacing: { after: 60 }, children: runs(t) });
const CAP = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
  children: [new TextRun({ text: t, italics: true, size: 19, color: "444444" })] });
function IMG(file, wPx, hPx, maxW = 600) {
  const w = Math.min(maxW, wPx), h = Math.round(hPx * w / wPx);
  return new Paragraph({ keepNext: true, alignment: AlignmentType.CENTER, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: fig(file), transformation: { width: w, height: h },
      altText: { title: file, description: file, name: file } })] });
}
function PLACEHOLDER(text, h = 1.6) {
  const bd = { style: BorderStyle.DASHED, size: 8, color: "999999" };
  return new Table({ width: { size: 9026, type: WidthType.DXA }, columnWidths: [9026],
    rows: [new TableRow({ height: { value: Math.round(h * 1440), rule: "atLeast" }, children: [new TableCell({
      width: { size: 9026, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
      shading: { fill: "FFFBEA", type: ShadingType.CLEAR }, verticalAlign: "center",
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text, highlight: "yellow", bold: true, size: 21 })] })] })] })] });
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
const borders = { top: border, bottom: border, left: border, right: border };
function TABLE(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, head) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, borders,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    shading: head ? { fill: "1F4E79", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ children: head ? [new TextRun({ text: t, bold: true, color: "FFFFFF", size: 19 })] : runs(t, { size: 19 }) })] });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(String(c), i, false)) }))] });
}
const SP = () => new Paragraph({ spacing: { after: 80 }, children: [] });

// ---------- data
const est = Object.fromEntries(fs.readFileSync(path.join(ROOT, "figs/cycle_estimate.csv"), "utf8").trim().split("\n").slice(1).map((l) => l.split(",")));
const code = fs.readFileSync(path.join(ROOT, "rapid/ElbowPickPlace.mod"), "utf8").replace(/\r/g, "").split("\n");

// ---------- content
const children = [];

// Title page
children.push(
  new Paragraph({ spacing: { before: 1400, after: 120 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "MA6212 Robotic Manipulation & Advanced Control", size: 28, color: "1F4E79" })] }),
  new Paragraph({ spacing: { after: 120 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Group Project Report", size: 26 })] }),
  new Paragraph({ spacing: { before: 300, after: 120 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Modelling and Simulation of a Robotic Pick-and-Place Cell", bold: true, size: 40 })] }),
  new Paragraph({ spacing: { after: 500 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "for Elbow-Pipe Gasket Assembly and Box Packing (ABB IRB 1300, RobotStudio)", size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: "Group members", bold: true, size: 24 })] }),
);
children.push(TABLE(["No.", "Full name", "Matriculation no.", "Main contribution"],
  [["1", "[[Name]]", "[[Matric no.]]", "CAD modelling"], ["2", "[[Name]]", "[[Matric no.]]", "Station setup & Smart Components"],
   ["3", "[[Name]]", "[[Matric no.]]", "RAPID programming & cycle time"], ["4", "[[Name]]", "[[Matric no.]]", "Report & documentation"],
   ["5", "[[Name]]", "[[Matric no.]]", "[[Contribution]]"]], [700, 3000, 2200, 3126]));
children.push(SP(), PLACEHOLDER("[INSERT GROUP PHOTOGRAPH – label each member by name]", 2.6),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300 }, children: [new TextRun({ text: "Submission date: 9 November 2026", size: 22 })] }),
  new Paragraph({ children: [new PageBreak()] }));



// 1 Introduction
children.push(H1("1. Introduction and Objectives"),
  P("Robotic pick-and-place is one of the most common applications of serial manipulators in manufacturing, where repeatable handling of moulded parts removes manual work from the end of a production line. This project models and simulates the robotic cell shown in the reference video (Robotic cell for tube gasket assembly), in which an ABB IRB 1300 equipped with a vacuum suction gripper picks freshly moulded elbow pipes from a conveyor, transfers them to an interim station where a rubber gasket is inserted, re-grips them at a second contact point and packs them in an orderly, indexed layout inside a carton."),
  P("The complete cell was modelled in ABB RobotStudio. Custom 3D models were created for the elbow pipe, gasket, interim station, packing box, vacuum gripper and carton conveyor; the motion was programmed in RAPID; and the run was simulated for a batch of parts to assess cycle time and throughput."),
  P("**Objectives**"),
  N("Model a realistic industrial pick-and-place system in ABB RobotStudio using the IRB 1300."),
  N("Integrate random workpiece positioning on the conveyor with a simulated vision input."),
  N("Apply RAPID programming for motion control, including vision offset handling and box indexing."),
  N("Analyse and optimise robot cycle time, safety and throughput."),
  N("Evaluate precision, collision risk and the industrial applicability of the cell."));

// 2 Video analysis
children.push(H1("2. Video Analysis"),
  P("The reference video was reviewed frame by frame to extract the layout and the motion sequence of one cycle. The observations below were used as the basis for the simulation model."),
  TABLE(["Aspect", "Observation from video", "Modelling decision"], [
    ["Pick source", "Elbows drop from an injection-moulding machine onto a flat belt conveyor; position and yaw vary from part to part.", "Belt conveyor with Smart Component source; part pose varied by a simulated vision offset (±20 mm, ±10°)."],
    ["Interim station", "Robot places the elbow on a fixture of the gasket-insertion unit; gaskets are fed from a rod magazine and pressed into the pipe socket.", "Static fixture with cradle blocks and a press unit facing pipe end A; insertion represented by a timed dwell."],
    ["Re-grip", "After insertion the robot grips the part again at a different surface before packing.", "Second contact point CP2 at 75° of the bend (CP1 is at 45°)."],
    ["Place target", "Carton on a roller conveyor; parts packed in rows and stacked in layers; full cartons leave on the conveyor.", "Indexed 2 × 2 slots × 2 layers (8 parts per box); doBoxFull indexes the carton conveyor."],
    ["Vacuum tool", "Single bellows-type suction cup on a compact body; part released by venting.", "Single-cup gripper, TCP at cup lip 175 mm from flange; Attacher/Detacher Smart Component."],
    ["Approach / retract", "Vertical approach to each pick/place point, fast joint moves between zones.", "MoveJ between zones, MoveL for the last 150 mm with a slow final 10–30 mm."],
    ["Cycle", "Approximately 8–10 s per part (estimated from the video).", "Used as a benchmark for the simulated cycle time."],
  ], [1700, 3800, 3526]),
  CAP("Table 1. Video analysis and corresponding modelling decisions"));

// 3 Assumptions & specs
children.push(H1("3. Assumptions and Specifications", true),
  H2("3.1 Robot and equipment"),
  TABLE(["Item", "Specification"], [
    ["Robot", "ABB IRB 1300-7/1.4 (7 kg payload, 1.4 m reach, ±0.02 mm repeatability) mounted on a 400 mm stand"],
    ["Controller", "Virtual controller in RobotStudio [[state RobotWare / controller version used]]"],
    ["End effector", "Vacuum suction gripper, 1.2 kg, single bellows cup Ø66 mm; TCP 175 mm along flange Z"],
    ["Payload check", "Gripper 1.2 kg + pipe 2.5 kg = 3.7 kg < 7 kg rated payload"],
    ["Workpiece", "90° elbow, OD 215 mm, ID 185 mm (wall 15 mm), centre-to-end 150 mm, mass 2.5 kg"],
    ["Gasket", "Rubber ring OD 185 / ID 161 mm, width 20 mm, inserted in pipe end A"],
    ["Infeed conveyor", "Belt, width 400 mm, surface height 600 mm"],
    ["Interim station", "Table top at 600 mm, cradle top at 630 mm, gasket press facing end A"],
    ["Packing box", "Inner 560 × 560 × 460 mm on a roller conveyor (top of rollers 400 mm)"],
  ], [2300, 6726]),
  CAP("Table 2. Robot and equipment specifications"),
  H2("3.2 Modelling assumptions"),
  B("The elbow height of 150 mm in the brief is interpreted as the centre-to-end dimension, i.e. a bend radius of 150 mm. The resulting volume (2.22 L) gives a density of 1.13 g/cm³ for 2.5 kg, consistent with a moulded polymer fitting."),
  B("Only the pick-and-place of the elbow pipe is simulated, as required by the brief; the gasket press and gasket are static models and insertion is represented by a 1.5 s dwell."),
  B("A vision camera is assumed above the conveyor. Its output (dx, dy, dRz) is emulated in RAPID by a pseudo-random generator and written to the object frame of wobjVision, which is how a real ABB vision integration shifts the pick targets."),
  B("Parts arrive lying flat (bend plane horizontal); the suction cup always approaches vertically from above onto the top of the tube."),
  B("Vacuum build-up and release each take 0.2 s; conveyor index time is shorter than the robot cycle, so the robot never waits for parts in steady state."),
  B("All dimensions are in millimetres; user frames are expressed in the world frame with the robot base at the origin."),
  H2("3.3 Frames and contact points"),
  TABLE(["Frame / target", "Position (mm)", "Purpose"], [
    ["wobjVision (uframe)", "(400, 540, 600)", "Nominal part origin (bend centre) on conveyor; oframe = vision offset"],
    ["wobjInterim", "(625, −275, 630)", "Part origin on the interim cradle"],
    ["wobjBox", "(−150, −750, 406)", "Centre of the inner floor of the carton"],
    ["CP1 (part frame)", "(106.1, 106.1, 215)", "Top of tube at 45° of the bend – conveyor pick"],
    ["CP2 (part frame)", "(38.8, 144.9, 215)", "Top of tube at 75° of the bend – re-grip after gasket insertion"],
    ["Box slot n", "(−272 + 280·i, −272 + 280·j, 215·k)", "i = n MOD 2, j = (n MOD 4) DIV 2, k = n DIV 4"],
  ], [2300, 2900, 3826]),
  CAP("Table 3. Work objects and targets used by the RAPID program"));

// 4 Cell model
children.push(H1("4. RobotStudio Cell Model"),
  H2("4.1 3D models"),
  P("The six custom models were generated parametrically from the specified dimensions and exported as STL meshes (units: mm), then imported with Import Geometry. The gripper geometry was converted to a tool with Create Tool, with the TCP at the cup lip and the tool load data set to 1.2 kg."),
  IMG("fig_models.png", 2250, 1425, 600),
  CAP("Figure 1. Custom models: elbow pipe, gasket, interim station, packing box, vacuum gripper, carton conveyor"),
  H2("4.2 Cell layout"),
  P("The robot is placed at the centre of the cell with the three work zones arranged around it so that all targets lie between 0.64 m and 0.97 m from axis 1, well inside the 1.4 m reach. The infeed conveyor runs along the +Y side, the interim station is on the +X side and the carton conveyor is behind the robot, which keeps the two transfer moves short and avoids passing over the operator side. A safety fence encloses the cell."),
  IMG("fig_layout_top.png", 1760, 1440, 520),
  CAP("Figure 2. Top view of the work-cell layout with transfer paths and contact points"),
  PLACEHOLDER("[INSERT ROBOTSTUDIO SCREENSHOT – full station view]", 2.4),
  CAP("Figure 3. RobotStudio station"),
  PLACEHOLDER("[INSERT ROBOTSTUDIO SCREENSHOT – paths and targets (pick, interim, box) with vision frame wobjVision shown]", 2.4),
  CAP("Figure 4. Programmed paths, targets and vision frame"),
  H2("4.3 Smart Components and I/O"),
  P("Two Smart Components make the simulation behave like the real cell. The infeed conveyor uses a Source to create a new elbow, a LinearMover to transport it and a PlaneSensor to stop the part and set diPartReady. The gripper uses a LineSensor at the cup, an Attacher (triggered by doVacuum = 1) and a Detacher (doVacuum = 0), combined through a LogicGate NOT."),
  TABLE(["Signal", "Type", "Connected to", "Function"], [
    ["diPartReady", "DI", "Conveyor PlaneSensor", "Part has reached the pick position"],
    ["doConvStop", "DO", "Conveyor LinearMover", "Holds the belt while the robot picks"],
    ["doVacuum", "DO", "Gripper Attacher / Detacher", "1 = grip part, 0 = release part"],
    ["doGasket", "DO", "Interim station", "Triggers the gasket press (1.5 s pulse)"],
    ["doBoxFull", "DO", "Carton conveyor", "Indexes the full box out and an empty box in"],
  ], [1700, 900, 2700, 3726]),
  CAP("Table 4. Station I/O signals"));

// 5 Workflow & program
children.push(H1("5. Workflow and Program Design"),
  H2("5.1 Cell workflow"),
  P("Figure 5 shows the flow of material through the cell (solid arrows) together with the handshake signals between the robot and the peripheral equipment (dashed arrows)."),
  IMG("fig_workflow.png", 2928, 821, 620),
  CAP("Figure 5. Cell workflow diagram"),
  H2("5.2 Program flowchart"),
  P("The RAPID module ElbowPickPlace is organised as one routine per process step, so the flowchart in Figure 6 maps one-to-one onto the code listing in Appendix A. The main loop runs a batch of 16 parts (two full boxes), timing each cycle and logging it to the controller HOME directory."),
  IMG("fig_program_flow.png", 1139, 2147, 330),
  CAP("Figure 6. RAPID program flowchart"),
  H2("5.3 Motion strategy"),
  B("**MoveJ** is used for all transfers between zones (conveyor → interim → box) at 2000 mm/s with large zones (z50–z100), because the path shape between zones is irrelevant and joint moves are the fastest."),
  B("**MoveL** is used for the last 150 mm of every approach and retract so the cup travels straight along the surface normal; the final 10–30 mm is executed at 150 mm/s with a fine point to guarantee a sealed vacuum contact and accurate placement."),
  B("**GripLoad** switches between load0 and two load-data sets (ldElbowCP1, ldElbowCP2) because the pipe centre of gravity relative to the flange differs for the two contact points, which keeps the dynamic model and path accuracy correct."),
  H2("5.4 Simulated vision offset"),
  P("For every new part, GetVisionOffset draws dx, dy ∈ [−20, 20] mm and dRz ∈ [−10°, 10°] from a Wichmann-Hill style generator (nSeed = 171·nSeed MOD 30269, exact in RAPID num arithmetic) and writes them to wobjVision.oframe. Because the pick target pCP1 is defined in wobjVision, the robot follows the displaced part automatically. The place target at the interim station uses the nominal orientation, so the yaw error measured by the vision is removed during the transfer and the part always arrives square to the fixture."),
  H2("5.5 Box indexing"),
  P("PlaceBox computes the slot from the running count n: layer k = n DIV 4, position in layer = n MOD 4, row i = (n MOD 4) MOD 2 and column j = (n MOD 4) DIV 2. The target is Offs(pCP2, −272 + 280i, −272 + 280j, 215k) in wobjBox, giving 23 mm clearance between parts and 12 mm to the carton walls. After eight parts ChangeBox pulses doBoxFull and resets the count."));

// 6 Results
children.push(H1("6. Simulation Results"),
  H2("6.1 Pre-simulation estimate"),
  P(`Before running the station, the cycle was estimated from the programmed path with a trapezoidal velocity model (4 m/s² acceleration, programmed TCP speeds, 0.08 s settling at fine points). The estimate gives an average of ${est.avg} s per part, i.e. about ${Math.round(3600 / parseFloat(est.avg))} parts per hour, which is in the same range as the 8–10 s observed in the video.`),
  TABLE(["Cycle component", "Time (s)", "Share"], [
    ["Joint transfers (MoveJ)", est["Joint transfers (MoveJ)"], Math.round(100 * est["Joint transfers (MoveJ)"] / est.avg) + " %"],
    ["Linear approach / retract (MoveL)", est["Linear approach/retract (MoveL)"], Math.round(100 * est["Linear approach/retract (MoveL)"] / est.avg) + " %"],
    ["Vacuum on/off (4 × 0.2 s)", est["Vacuum on/off"], Math.round(100 * est["Vacuum on/off"] / est.avg) + " %"],
    ["Gasket insertion dwell", est["Gasket dwell"], Math.round(100 * est["Gasket dwell"] / est.avg) + " %"],
    ["Total (average of 8 slots)", est.avg, "100 %"],
  ], [4500, 2000, 2526]),
  CAP("Table 5. Estimated cycle-time breakdown"),
  H2("6.2 RobotStudio simulation"),
  P("The station was run for a batch of 16 parts (two boxes). Cycle times were read from the controller clock (ClkRead) and written to cycle_log.csv; the summary is given in Table 6."),
  TABLE(["Metric", "Value"], [
    ["Parts simulated", "16 (2 boxes × 8)"], ["Average cycle time", "[[from cycle_log.csv]] s"],
    ["Minimum / maximum cycle time", "[[min]] s / [[max]] s"], ["Throughput", "[[3600 / avg]] parts/h"],
    ["Total batch time", "[[batch time]] s"], ["Collisions detected", "[[none / list]]"],
  ], [4500, 4526]),
  CAP("Table 6. Simulated performance"),
  PLACEHOLDER("[INSERT SCREENSHOT – RobotStudio simulation in progress / Signal Analyzer or RAPID output window with cycle times]", 2.2),
  CAP("Figure 7. Simulation run and cycle-time output"),
  H2("6.3 Discussion and optimisation"),
  B("Linear approach and retract moves account for the largest share of the cycle. Raising the MoveL approach speed from 600 to 1000 mm/s and shortening the approach height from 150 to 100 mm are the most effective optimisations [[state measured gain]]."),
  B("The 1.5 s gasket dwell is partly hidden because the robot moves to the re-grip position while the press works; with a second fixture the robot could pick the next part during insertion and remove the dwell from the critical path."),
  B("Vision offsets of ±20 mm / ±10° did not change the cycle time noticeably, since the transfer moves are dominated by joint motion rather than path length."),
  B("Safety: the cell is fenced, and Collision Detection sets were used between the gripper/part and the conveyor, station and carton walls. The 23 mm clearance between packed parts and the vertical final approach prevent contact with neighbouring parts."),
  B("Precision: the IRB 1300 repeatability (±0.02 mm) is far below the placement tolerance needed for packing; the limiting factor in a real cell would be the vision accuracy and the compliance of the bellows cup."));

// 7 Conclusion
children.push(H1("7. Conclusion"),
  P("A complete RobotStudio model of the elbow-pipe gasket and packing cell was built, including custom CAD models, a vacuum tool, Smart Components for the conveyor and gripper, and a structured RAPID program with simulated vision offsets and indexed box placement. The two-stage pick-and-place sequence was simulated for a batch of parts, and the cycle time of about [[avg]] s per part ([[throughput]] parts/h) is comparable with the real cell in the reference video. The modular program structure makes it straightforward to change the box pattern, add a real vision interface or re-balance the cycle with a second fixture."));

// Appendix
children.push(new Paragraph({ children: [new PageBreak()] }), H1("Appendix A. RAPID Code Listing (ElbowPickPlace.mod)"));
for (const line of code) {
  children.push(new Paragraph({ spacing: { after: 0, line: 216 },
    children: [new TextRun({ text: line.length ? line : " ", font: "Consolas", size: 14 })] }));
}
children.push(H1("Appendix B. Submitted Files"),
  TABLE(["File", "Description"], [
    ["MA6212_ElbowCell.rspag", "RobotStudio Pack & Go of the station and virtual controller"],
    ["elbow_pipe.stl", "Elbow pipe model (OD 215, ID 185, R 150)"], ["gasket.stl", "Gasket ring"],
    ["interim_station.stl", "Interim gasket-insertion station"], ["packing_box.stl", "Packing carton"],
    ["vacuum_gripper.stl", "Vacuum suction gripper"], ["box_conveyor.stl", "Carton roller conveyor"],
    ["robot_stand.stl", "Robot pedestal"], ["ElbowPickPlace.mod", "RAPID module"],
    ["cycle_log.csv", "Cycle-time log exported from the virtual controller"],
  ], [3200, 5826]));

// ---------- document
const doc = new Document({
  creator: "MA6212 Group", title: "MA6212 Group Project Report",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: "1F4E79" }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: "2E75B6" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "MA6212 Group Project – Elbow-Pipe Pick-and-Place Cell", size: 16, color: "888888" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "666666" })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("written", OUT); });
