MODULE ElbowPickPlace
    !***********************************************************************
    ! MA6212 Group Project - Elbow pipe pick-and-place with gasket station
    ! Robot      : ABB IRB 1300-7/1.4  (base on 400 mm stand)
    ! End effector: vacuum suction gripper, TCP 175 mm from flange
    ! Cycle      : (1) pick elbow from infeed conveyor at contact point CP1
    !              (2) place on interim station, gasket is inserted
    !              (3) re-grip at contact point CP2
    !              (4) place at indexed slot in packing box (2 x 2 x 2 = 8)
    ! Vision     : simulated - each new part arrives in one of four poses;
    !              its offset (dx, dy, dRz) is written into the object
    !              frame of wobjVision, as a camera would report it.
    ! Units      : mm, deg. All user frames are given in the world frame.
    !***********************************************************************

    !------------------------------------------------------------- tool & load
    ! Gripper 1.2 kg, centre of gravity 70 mm from flange, TCP at cup lip.
    PERS tooldata tVacuum:=[TRUE,[[0,0,175],[1,0,0,0]],[1.2,[0,0,70],[1,0,0,0],0,0,0]];
    ! Elbow pipe 2.5 kg. CoG expressed in the flange frame (tool0).
    ! Centroid of the 90 deg bend lies at r = R*sin45/(pi/4) = 135 mm on the
    ! 45 deg bisector, i.e. part coords (95.5, 95.5, 107.5).
    ! Gripped at CP1: CoG - CP1 = (-10.6,-10.6,-107.5) part -> (-10.6,10.6,107.5) tool
    ! Gripped at CP2: CoG - CP2 = (56.7,-49.4,-107.5) part -> (56.7,49.4,107.5) tool
    ! plus 175 mm TCP offset along flange Z.
    PERS loaddata ldElbowCP1:=[2.5,[-10.6,10.6,282.5],[1,0,0,0],0,0,0];
    PERS loaddata ldElbowCP2:=[2.5,[56.7,49.4,282.5],[1,0,0,0],0,0,0];

    !------------------------------------------------------------- work objects
    ! Infeed conveyor: uframe = nominal part origin (bend centre, belt surface)
    ! oframe = vision correction, rewritten for every part.
    PERS wobjdata wobjVision:=[FALSE,TRUE,"",[[400,540,600],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    ! Interim gasket station: frame at the part origin on the cradle
    PERS wobjdata wobjInterim:=[FALSE,TRUE,"",[[625,-275,630],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];
    ! Packing box: frame at centre of the inner floor
    PERS wobjdata wobjBox:=[FALSE,TRUE,"",[[-150,-750,406],[1,0,0,0]],[[0,0,0],[1,0,0,0]]];

    !------------------------------------------------------------- targets
    ! Contact points on the elbow (part frame, tool pointing down = q[0,1,0,0])
    !   CP1 : top of tube at 45 deg of the bend  -> used for conveyor pick
    !   CP2 : top of tube at 75 deg of the bend  -> used for re-grip at station
    CONST robtarget pCP1:=[[106.07,106.07,215],[0,1,0,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST robtarget pCP2:=[[38.82,144.89,215],[0,1,0,0],[0,0,0,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST jointtarget jHome:=[[0,-10,20,0,60,0],[9E9,9E9,9E9,9E9,9E9,9E9]];
    ! Reference joint poses (front, elbow-up, wrist-down) for each station.
    ! Their arm configuration is copied into the targets so that ConfJ\On
    ! forces the same, compact configuration every cycle (no over-head flips).
    CONST jointtarget jPickRef:=[[52,14,27,0,49,-130],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST jointtarget jInterRef:=[[-12,2,38,0,50,-192],[9E9,9E9,9E9,9E9,9E9,9E9]];
    CONST jointtarget jBoxRef:=[[-98,20,35,0,40,-278],[9E9,9E9,9E9,9E9,9E9,9E9]];
    VAR confdata cfPick; VAR confdata cfInter; VAR confdata cfBox;
    VAR robtarget pRef; VAR robtarget pT;

    !------------------------------------------------------------- parameters
    CONST num nRows:=2;            ! slots along box X
    CONST num nCols:=2;            ! slots along box Y
    CONST num nLayers:=2;          ! layers
    CONST num nPitch:=280;         ! slot pitch [mm]
    CONST num nLayerH:=215;        ! layer height = pipe OD [mm]
    CONST num nSlot0:=-272;        ! first slot part-origin offset from box centre
    CONST num nBatch:=8;           ! parts to run (one full box)
    CONST num nApproach:=150;      ! approach / retract height [mm]
    CONST num tGasket:=1.5;        ! gasket insertion dwell [s]
    CONST num tVac:=0.2;           ! vacuum build-up / release [s]

    VAR speeddata vFast:=[2000,500,5000,1000];
    VAR speeddata vApp:=[600,200,5000,1000];
    VAR speeddata vGrip:=[150,100,5000,1000];

    !------------------------------------------------------------- I/O (virtual)
    ! diPartReady : from infeed volume sensor (Smart Component)
    ! doFeed1..4  : to infeed Smart Component, spawn a part in pose 1..4
    ! doVacuum    : to gripper Smart Component (Attacher / Detacher)
    ! doGasket    : to interim station (gasket press animation)
    ! doBoxFull   : to carton conveyor (index full box out, new box in)
    ! doConvStop  : stop infeed conveyor while robot picks

    !------------------------------------------------------------- variables
    VAR num nCount:=0;             ! parts placed in current box
    VAR num nTotal:=0;             ! parts placed in batch
    VAR num nSeed:=1234;           ! pseudo-random seed (simulated vision)
    VAR num nPose;                 ! selected part pose 1..4
    ! Four part poses on the conveyor as reported by the (simulated) camera:
    ! [dx mm, dy mm, dRz deg]. The infeed Smart Component spawns the part in
    ! the same pose (doFeed1..4), so camera result and part pose agree.
    CONST num POSE{4,3}:=[[15,-10,6],[-12,14,-8],[8,18,-3],[-18,-6,9]];
    VAR num dX; VAR num dY; VAR num dRz;
    VAR clock clkCycle; VAR clock clkBatch;
    VAR num tCycle; VAR num tSum:=0; VAR num tMin:=999; VAR num tMax:=0;
    VAR iodev logFile;
    VAR iodev jLog;
    VAR jointtarget jNow;

    !=======================================================================
    PROC main()
        Init;
        WHILE nTotal < nBatch DO
            ClkReset clkCycle; ClkStart clkCycle;
            GetVisionOffset;
            PickConveyor;
            PlaceInterim;
            InsertGasket;
            RegripInterim;
            PlaceBox;
            ClkStop clkCycle; tCycle:=ClkRead(clkCycle);
            LogCycle;
            IF nCount >= nRows*nCols*nLayers ChangeBox;
        ENDWHILE
        MoveAbsJ jHome, vFast, fine, tVacuum;
        ClkStop clkBatch;
        Report;
    ENDPROC

    !-----------------------------------------------------------------------
    PROC Init()
        AccSet 100, 100;
        VelSet 100, 2000;
        ConfJ \On;
        ConfL \On;
        pRef:=CalcRobT(jPickRef, tVacuum \WObj:=wobj0);  cfPick:=pRef.robconf;
        pRef:=CalcRobT(jInterRef, tVacuum \WObj:=wobj0); cfInter:=pRef.robconf;
        pRef:=CalcRobT(jBoxRef, tVacuum \WObj:=wobj0);   cfBox:=pRef.robconf;
        SetDO doVacuum, 0; SetDO doGasket, 0; SetDO doBoxFull, 0; SetDO doConvStop, 0;
        GripLoad load0;
        nCount:=0; nTotal:=0; tSum:=0; tMin:=999; tMax:=0;
        MoveAbsJ jHome, vFast, fine, tVacuum;
        Open "HOME:" \File:="cycle_log.csv", logFile \Write;
        Write logFile, "part,box_slot,layer,dx_mm,dy_mm,drz_deg,cycle_s";
        Open "HOME:" \File:="joint_log.csv", jLog \Write;
        ClkReset clkBatch; ClkStart clkBatch;
    ENDPROC

    !-----------------------------------------------------------------------
    ! Simulated vision: multiplicative congruential generator, exact in num.
    FUNC num Rnd()
        nSeed:=(171*nSeed) MOD 30269;
        RETURN nSeed/30269;
    ENDFUNC

    PROC GetVisionOffset()
        ! pick one of the four poses at random and feed a part in that pose
        nPose:=Trunc(Rnd()*4)+1;
        IF nPose>4 nPose:=4;
        dX:=POSE{nPose,1};
        dY:=POSE{nPose,2};
        dRz:=POSE{nPose,3};
        TEST nPose
        CASE 1: PulseDO \PLength:=0.2, doFeed1;
        CASE 2: PulseDO \PLength:=0.2, doFeed2;
        CASE 3: PulseDO \PLength:=0.2, doFeed3;
        CASE 4: PulseDO \PLength:=0.2, doFeed4;
        ENDTEST
        ! camera result -> object frame of the vision work object
        wobjVision.oframe.trans:=[dX,dY,0];
        wobjVision.oframe.rot:=OrientZYX(dRz,0,0);
    ENDPROC

    !-----------------------------------------------------------------------
    PROC PickConveyor()
        pT:=pCP1; pT.robconf:=cfPick;
        MoveJ Offs(pT,0,0,nApproach), vFast, z50, tVacuum\WObj:=wobjVision;
        WaitDI diPartReady, 1 \MaxTime:=30;
        SetDO doConvStop, 1;
        MoveL Offs(pT,0,0,20), vApp, z5, tVacuum\WObj:=wobjVision;
        MoveL pT, vGrip, fine, tVacuum\WObj:=wobjVision;
        SetDO doVacuum, 1;
        LogJ "pick";
        WaitTime tVac;
        GripLoad ldElbowCP1;
        MoveL Offs(pT,0,0,nApproach), vApp, z20, tVacuum\WObj:=wobjVision;
        SetDO doConvStop, 0;
    ENDPROC

    PROC PlaceInterim()
        ! Part is placed square to the fixture: target uses nominal orientation,
        ! so the vision rotation dRz is removed during the transfer.
        pT:=pCP1; pT.robconf:=cfInter;
        MoveJ Offs(pT,0,0,nApproach), vFast, z50, tVacuum\WObj:=wobjInterim;
        MoveL Offs(pT,0,0,10), vApp, z5, tVacuum\WObj:=wobjInterim;
        MoveL pT, vGrip, fine, tVacuum\WObj:=wobjInterim;
        SetDO doVacuum, 0;
        LogJ "interim_place";
        WaitTime tVac;
        GripLoad load0;
        MoveL Offs(pT,0,0,60), vApp, z10, tVacuum\WObj:=wobjInterim;
    ENDPROC

    PROC InsertGasket()
        pT:=pCP2; pT.robconf:=cfInter;
        ! Robot moves over CP2 while the press inserts the gasket in end A.
        PulseDO \PLength:=tGasket, doGasket;
        MoveL Offs(pT,0,0,60), vApp, fine, tVacuum\WObj:=wobjInterim;
        WaitTime tGasket;
    ENDPROC

    PROC RegripInterim()
        pT:=pCP2; pT.robconf:=cfInter;
        MoveL Offs(pT,0,0,20), vApp, z5, tVacuum\WObj:=wobjInterim;
        MoveL pT, vGrip, fine, tVacuum\WObj:=wobjInterim;
        SetDO doVacuum, 1;
        LogJ "regrip";
        WaitTime tVac;
        GripLoad ldElbowCP2;
        MoveL Offs(pT,0,0,nApproach), vApp, z20, tVacuum\WObj:=wobjInterim;
    ENDPROC

    !-----------------------------------------------------------------------
    ! Box index: slot = nCount MOD 4 (row-major), layer = nCount DIV 4
    PROC PlaceBox()
        VAR num nInLayer; VAR num nLayer; VAR num nRow; VAR num nCol;
        VAR num ox; VAR num oy; VAR num oz;
        VAR robtarget pPlace;
        nLayer:=nCount DIV (nRows*nCols);
        nInLayer:=nCount MOD (nRows*nCols);
        nRow:=nInLayer MOD nRows;
        nCol:=nInLayer DIV nRows;
        ox:=nSlot0+nRow*nPitch;
        oy:=nSlot0+nCol*nPitch;
        oz:=nLayer*nLayerH;
        pPlace:=Offs(pCP2, ox, oy, oz);
        pPlace.robconf:=cfBox;
        MoveJ Offs(pPlace,0,0,nApproach+200), vFast, z100, tVacuum\WObj:=wobjBox;
        MoveL Offs(pPlace,0,0,30), vApp, z10, tVacuum\WObj:=wobjBox;
        MoveL pPlace, vGrip, fine, tVacuum\WObj:=wobjBox;
        SetDO doVacuum, 0;
        LogJ "box_place";
        WaitTime tVac;
        GripLoad load0;
        MoveL Offs(pPlace,0,0,nApproach+200), vApp, z50, tVacuum\WObj:=wobjBox;
        Incr nCount;
        Incr nTotal;
    ENDPROC

    PROC ChangeBox()
        TPWrite "Box full - indexing carton conveyor";
        PulseDO \PLength:=1, doBoxFull;
        nCount:=0;
    ENDPROC

    !-----------------------------------------------------------------------
    PROC LogJ(string tag)
        jNow:=CJointT();
        Write jLog, tag+","+NumToStr(jNow.robax.rax_1,1)+","+NumToStr(jNow.robax.rax_2,1)+","+NumToStr(jNow.robax.rax_3,1)+","+NumToStr(jNow.robax.rax_4,1)+","+NumToStr(jNow.robax.rax_5,1)+","+NumToStr(jNow.robax.rax_6,1);
    ENDPROC

    PROC LogCycle()
        tSum:=tSum+tCycle;
        IF tCycle < tMin tMin:=tCycle;
        IF tCycle > tMax tMax:=tCycle;
        TPWrite "Part "\Num:=nTotal;
        TPWrite "  cycle time [s] = "\Num:=tCycle;
        Write logFile, NumToStr(nTotal,0)+","+NumToStr(((nCount-1) MOD 4)+1,0)+","
            +NumToStr(((nCount-1) DIV 4)+1,0)+","+NumToStr(dX,2)+","+NumToStr(dY,2)+","
            +NumToStr(dRz,2)+","+NumToStr(tCycle,3);
    ENDPROC

    PROC Report()
        VAR num tAvg; VAR num tBatch;
        tAvg:=tSum/nTotal;
        tBatch:=ClkRead(clkBatch);
        TPWrite "==== Batch finished ====";
        TPWrite "Parts             = "\Num:=nTotal;
        TPWrite "Avg cycle [s]     = "\Num:=tAvg;
        TPWrite "Min cycle [s]     = "\Num:=tMin;
        TPWrite "Max cycle [s]     = "\Num:=tMax;
        TPWrite "Batch time [s]    = "\Num:=tBatch;
        TPWrite "Throughput [pcs/h]= "\Num:=3600/tAvg;
        Write logFile, "avg,"+NumToStr(tAvg,3)+",min,"+NumToStr(tMin,3)+",max,"+NumToStr(tMax,3)
            +",throughput_pph,"+NumToStr(3600/tAvg,0);
        Close logFile;
        Close jLog;
    ENDPROC

ENDMODULE
