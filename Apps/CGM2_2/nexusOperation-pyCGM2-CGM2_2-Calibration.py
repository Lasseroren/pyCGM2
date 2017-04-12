# -*- coding: utf-8 -*-
import os
import logging
import matplotlib.pyplot as plt
import json
import pdb
import cPickle
import json
from shutil import copyfile
from collections import OrderedDict
import argparse
import sys

# pyCGM2 settings
import pyCGM2
pyCGM2.CONFIG.setLoggingLevel(logging.INFO)


# vicon nexus
import ViconNexus

# openMA
#import ma.io
#import ma.body

#btk
import btk
import numpy as np



# pyCGM2 libraries
from pyCGM2.Tools import btkTools,nexusTools
import pyCGM2.enums as pyCGM2Enums
from pyCGM2.Model.CGM2 import cgm, modelFilters, modelDecorator
from pyCGM2.Model.Opensim import opensimFilters

from pyCGM2 import viconInterface


if __name__ == "__main__":

    plt.close("all")
    DEBUG = False

    parser = argparse.ArgumentParser(description='CGM2.2 Calibration')
    parser.add_argument('-l','--leftFlatFoot', type=int, help='left flat foot option')
    parser.add_argument('-r','--rightFlatFoot',type=int,  help='right flat foot option')
    parser.add_argument('-md','--markerDiameter', type=float, help='marker diameter')
    parser.add_argument('--check', action='store_true', help='force model output suffix')
    parser.add_argument('--ik', action='store_true', help='inverse kinematic',default=True)
    args = parser.parse_args()


    NEXUS = ViconNexus.ViconNexus()
    NEXUS_PYTHON_CONNECTED = NEXUS.Client.IsConnected()


    if NEXUS_PYTHON_CONNECTED: # run Operation

        # --------------------------INPUTS ------------------------------------

        # --- acquisition file and path----
        if DEBUG:
            DATA_PATH = pyCGM2.CONFIG.MAIN_BENCHMARK_PATH +"True equinus\\S01\\CGM2.2\\" 
            calibrateFilenameLabelledNoExt = "static" #"static Cal 01-noKAD-noAnkleMed" #
            NEXUS.OpenTrial( str(DATA_PATH+calibrateFilenameLabelledNoExt), 30 )

        else:
            DATA_PATH, calibrateFilenameLabelledNoExt = NEXUS.GetTrialName()

        calibrateFilenameLabelled = calibrateFilenameLabelledNoExt+".c3d"

        logging.info( "data Path: "+ DATA_PATH )
        logging.info( "calibration file: "+ calibrateFilenameLabelled)

        # ---btk acquisition---
        acqStatic = btkTools.smartReader(str(DATA_PATH+calibrateFilenameLabelled))

        # check if acq was saved with only one  activated subject
        if acqStatic.GetPoint(0).GetLabel().count(":"):
            raise Exception("[pyCGM2] Your input static c3d was saved with two activate subject. Re-save it with only one before pyCGM2 calculation") 

#        # ---relabel PIG output if processing previously---
#        n_angles,n_forces ,n_moments,  n_powers = btkTools.getNumberOfModelOutputs(acqStatic)
#        if any([n_angles,n_forces ,n_moments,  n_powers])==1:               
#            cgm.CGM.reLabelOldOutputs(acqStatic) 


        # --------------------------SUBJECT -----------------------------------
        # Notice : Work with ONE subject by session
        subjects = NEXUS.GetSubjectNames()
        subject = nexusTools.ckeckActivatedSubject(NEXUS,subjects,"LASI")        
        Parameters = NEXUS.GetSubjectParamNames(subject)


        # --------------------pyCGM2 INPUT FILES ------------------------------

        # global setting ( in user/AppData)
        inputs = json.loads(open(str(pyCGM2.CONFIG.PYCGM2_APPDATA_PATH+"CGM2_2-pyCGM2.inputs")).read(),object_pairs_hook=OrderedDict)

        # info file
        if not os.path.isfile( DATA_PATH + subject+"-pyCGM2.info"):
            copyfile(str(pyCGM2.CONFIG.PYCGM2_SETTINGS_FOLDER+"pyCGM2.info"), str(DATA_PATH + subject+"-pyCGM2.info"))
            logging.warning("Copy of pyCGM2.info from pyCGM2 Settings folder")
            infoSettings = json.loads(open(DATA_PATH +subject+'-pyCGM2.info').read(),object_pairs_hook=OrderedDict)
        else:
            infoSettings = json.loads(open(DATA_PATH +subject+'-pyCGM2.info').read(),object_pairs_hook=OrderedDict)


        # ---- configuration parameters ----


        hjcMethod = inputs["Calibration"]["HJC regression"] 

        if args.leftFlatFoot is not None:      
            flag_leftFlatFoot = bool(args.leftFlatFoot)
        else:
            flag_leftFlatFoot = bool(inputs["Calibration"]["Left flat foot"])
               
        if args.rightFlatFoot is not None:
            flag_rightFlatFoot = bool(args.rightFlatFoot)
        else:
            flag_rightFlatFoot =  bool(inputs["Calibration"]["Right flat foot"])


        if args.markerDiameter is not None: 
            markerDiameter = float(args.markerDiameter)
            logging.warning("marker diameter forced : %s", str(float(args.markerDiameter)))
        else:
            markerDiameter = float(inputs["Global"]["Marker diameter"])


        if args.check:
            pointSuffix="cgm2.2"
        else:
            pointSuffix = inputs["Global"]["Point suffix"]

        # --------------------------MP DATA -----------------------------------

        required_mp={
        'Bodymass'   : NEXUS.GetSubjectParamDetails( subject, "Bodymass")[0],#71.0,
        'LeftLegLength' : NEXUS.GetSubjectParamDetails( subject, "LeftLegLength")[0],#860.0,
        'RightLegLength' : NEXUS.GetSubjectParamDetails( subject, "RightLegLength")[0],#865.0 ,
        'LeftKneeWidth' : NEXUS.GetSubjectParamDetails( subject, "LeftKneeWidth")[0],#102.0,
        'RightKneeWidth' : NEXUS.GetSubjectParamDetails( subject, "RightKneeWidth")[0],#103.4,
        'LeftAnkleWidth' : NEXUS.GetSubjectParamDetails( subject, "LeftAnkleWidth")[0],#75.3,
        'RightAnkleWidth' : NEXUS.GetSubjectParamDetails( subject, "RightAnkleWidth")[0],#72.9,
        'LeftSoleDelta' : NEXUS.GetSubjectParamDetails( subject, "LeftSoleDelta")[0],#75.3,
        'RightSoleDelta' : NEXUS.GetSubjectParamDetails( subject, "RightSoleDelta")[0],#72.9,        
        }

        optional_mp={
        'InterAsisDistance'   : NEXUS.GetSubjectParamDetails( subject, "InterAsisDistance")[0],#0,
        'LeftAsisTrocanterDistance' : NEXUS.GetSubjectParamDetails( subject, "LeftAsisTrocanterDistance")[0],#0,
        'LeftTibialTorsion' : NEXUS.GetSubjectParamDetails( subject, "LeftTibialTorsion")[0],#0 ,
        'LeftThighRotation' : NEXUS.GetSubjectParamDetails( subject, "LeftThighRotation")[0],#0,
        'LeftShankRotation' : NEXUS.GetSubjectParamDetails( subject, "LeftShankRotation")[0],#0,
        'RightAsisTrocanterDistance' : NEXUS.GetSubjectParamDetails( subject, "RightAsisTrocanterDistance")[0],#0,
        'RightTibialTorsion' : NEXUS.GetSubjectParamDetails( subject, "RightTibialTorsion")[0],#0 ,
        'RightThighRotation' : NEXUS.GetSubjectParamDetails( subject, "RightThighRotation")[0],#0,
        'RightShankRotation' : NEXUS.GetSubjectParamDetails( subject, "RightShankRotation")[0],#0,
        }

        # --------------------------MODEL--------------------------------------
        # ---definition---
        model=cgm.CGM1LowerLimbs()
        model.setCGM1Version("1.1")
        model.configure()
        model.addAnthropoInputParameters(required_mp,optional=optional_mp)

        # ---check marker set used----
        staticMarkerConfiguration= cgm.CGM.checkCGM1_StaticMarkerConfig(acqStatic)


        # --------------------------STATIC CALBRATION--------------------------                
        scp=modelFilters.StaticCalibrationProcedure(model) # load calibration procedure
        
        # ---initial calibration filter----
        # use if all optional mp are zero    
        modelFilters.ModelCalibrationFilter(scp,acqStatic,model,
                                            leftFlatFoot = flag_leftFlatFoot, rightFlatFoot = flag_rightFlatFoot,
                                            markerDiameter=markerDiameter,
                                            ).compute()

        # ---- Decorators -----
        # Goal = modified calibration according the identified marker set or if offsets manually set   
 

        # hip joint centres ---
        useLeftHJCnodeLabel = "LHJC_cgm1"
        useRightHJCnodeLabel = "RHJC_cgm1" 
        if hjcMethod == "Hara":
            modelDecorator.HipJointCenterDecorator(model).hara()  
            useLeftHJCnodeLabel = "LHJC_Hara"
            useRightHJCnodeLabel = "RHJC_Hara" 
            
        
        # knee - ankle centres ---

        # initialisation of node label 
        useLeftKJCnodeLabel = "LKJC_chord"
        useLeftAJCnodeLabel = "LAJC_chord"
        useRightKJCnodeLabel = "RKJC_chord"
        useRightAJCnodeLabel = "RAJC_chord"

        # case 1 : NO kad, NO medial ankle BUT thighRotation different from zero ( mean manual modification or new calibration from a previous one )
        if not staticMarkerConfiguration["leftKadFlag"]  and not staticMarkerConfiguration["leftMedialAnkleFlag"] and not staticMarkerConfiguration["leftMedialKneeFlag"] and optional_mp["LeftThighRotation"] !=0:
            logging.warning("CASE FOUND ===> Left Side - CGM1 - Origine - manual offsets")            
            modelDecorator.Cgm1ManualOffsets(model).compute(acqStatic,"left",optional_mp["LeftThighRotation"],markerDiameter,optional_mp["LeftTibialTorsion"],optional_mp["LeftShankRotation"])
            useLeftKJCnodeLabel = "LKJC_mo"
            useLeftAJCnodeLabel = "LAJC_mo"
        if not staticMarkerConfiguration["rightKadFlag"]  and not staticMarkerConfiguration["rightMedialAnkleFlag"] and not staticMarkerConfiguration["rightMedialKneeFlag"] and optional_mp["RightThighRotation"] !=0:
            logging.warning("CASE FOUND ===> Right Side - CGM1 - Origine - manual offsets")            
            modelDecorator.Cgm1ManualOffsets(model).compute(acqStatic,"right",optional_mp["RightThighRotation"],markerDiameter,optional_mp["RightTibialTorsion"],optional_mp["RightShankRotation"])
            useRightKJCnodeLabel = "RKJC_mo"
            useRightAJCnodeLabel = "RAJC_mo"

        # case 2 : kad FOUND and NO medial Ankle 
        if staticMarkerConfiguration["leftKadFlag"]:
            logging.warning("CASE FOUND ===> Left Side - CGM1 - KAD variant")
            modelDecorator.Kad(model,acqStatic).compute(markerDiameter=markerDiameter, side="left")
            useLeftKJCnodeLabel = "LKJC_kad"
            useLeftAJCnodeLabel = "LAJC_kad"
        if staticMarkerConfiguration["rightKadFlag"]:
            logging.warning("CASE FOUND ===> Right Side - CGM1 - KAD variant")
            modelDecorator.Kad(model,acqStatic).compute(markerDiameter=markerDiameter, side="right")
            useRightKJCnodeLabel = "RKJC_kad"
            useRightAJCnodeLabel = "RAJC_kad"


        # case 3 : medial knee FOUND 
        # notice: cgm1Behaviour is enable mean effect on AJC location 
        if staticMarkerConfiguration["leftMedialKneeFlag"]:
            logging.warning("CASE FOUND ===> Left Side - CGM1 - medial knee ")
            modelDecorator.KneeCalibrationDecorator(model).midCondyles(acqStatic, markerDiameter=markerDiameter, side="left",cgm1Behaviour=True)
            useLeftKJCnodeLabel = "LKJC_mid"
            useLeftAJCnodeLabel = "LAJC_midKnee"
        if staticMarkerConfiguration["rightMedialKneeFlag"]:
            logging.warning("CASE FOUND ===> Right Side - CGM1 - medial knee ")
            modelDecorator.KneeCalibrationDecorator(model).midCondyles(acqStatic, markerDiameter=markerDiameter, side="right",cgm1Behaviour=True)
            useRightKJCnodeLabel = "RKJC_mid"
            useRightAJCnodeLabel = "RAJC_midKnee"


        # case 4 : medial ankle FOUND 
        if staticMarkerConfiguration["leftMedialAnkleFlag"]:
            logging.warning("CASE FOUND ===> Left Side - CGM1 - medial ankle ")
            modelDecorator.AnkleCalibrationDecorator(model).midMaleolus(acqStatic, markerDiameter=markerDiameter, side="left")
            useLeftAJCnodeLabel = "LAJC_mid"
        if staticMarkerConfiguration["rightMedialAnkleFlag"]:
            logging.warning("CASE FOUND ===> Right Side - CGM1 - medial ankle ")
            modelDecorator.AnkleCalibrationDecorator(model).midMaleolus(acqStatic, markerDiameter=markerDiameter, side="right")
            useRightAJCnodeLabel = "RAJC_mid"

        # ----Final Calibration filter if model previously decorated ----- 
        if model.decoratedModel:
            # initial static filter
            modelFilters.ModelCalibrationFilter(scp,acqStatic,model,
                               useLeftHJCnode=useLeftHJCnodeLabel, useRightHJCnode=useRightHJCnodeLabel,
                               useLeftKJCnode=useLeftKJCnodeLabel, useLeftAJCnode=useLeftAJCnodeLabel,
                               useRightKJCnode=useRightKJCnodeLabel, useRightAJCnode=useRightAJCnodeLabel,
                               markerDiameter=markerDiameter).compute()

        
        #----update subject mp----
        viconInterface.updateNexusSubjectMp(NEXUS,model,subject)


        # ----------------------CGM MODELLING----------------------------------
        # ----motion filter----
        modMotion=modelFilters.ModelMotionFilter(scp,acqStatic,model,pyCGM2Enums.motionMethod.Native,
                                                  markerDiameter=markerDiameter)

        modMotion.compute()


        if args.ik:
            #                        ---OPENSIM IK---
    
            # --- opensim calibration Filter ---
            osimfile = pyCGM2.CONFIG.OPENSIM_PREBUILD_MODEL_PATH + "models\\osim\\lowerLimb_ballsJoints.osim"    # osimfile        
            markersetFile = pyCGM2.CONFIG.OPENSIM_PREBUILD_MODEL_PATH + "models\\settings\\cgm1\\cgm1-markerset.xml" # markerset
            cgmCalibrationprocedure = opensimFilters.CgmOpensimCalibrationProcedures(model) # procedure
        
            oscf = opensimFilters.opensimCalibrationFilter(osimfile,
                                                    model,
                                                    cgmCalibrationprocedure)
            oscf.addMarkerSet(markersetFile)
            scalingOsim = oscf.build()
            
            
            # --- opensim Fitting Filter ---
            iksetupFile = pyCGM2.CONFIG.OPENSIM_PREBUILD_MODEL_PATH + "models\\settings\\cgm1\\cgm1-ikSetUp_template.xml" # ik tool file
    
            cgmFittingProcedure = opensimFilters.CgmOpensimFittingProcedure(model) # procedure
            cgmFittingProcedure.updateMarkerWeight("LASI",inputs["Fitting"]["Weight"]["LASI"]) 
            cgmFittingProcedure.updateMarkerWeight("RASI",inputs["Fitting"]["Weight"]["RASI"])
            cgmFittingProcedure.updateMarkerWeight("LPSI",inputs["Fitting"]["Weight"]["LPSI"])
            cgmFittingProcedure.updateMarkerWeight("RPSI",inputs["Fitting"]["Weight"]["RPSI"])
            cgmFittingProcedure.updateMarkerWeight("RTHI",inputs["Fitting"]["Weight"]["RTHI"])
            cgmFittingProcedure.updateMarkerWeight("RKNE",inputs["Fitting"]["Weight"]["RKNE"])
            cgmFittingProcedure.updateMarkerWeight("RTIB",inputs["Fitting"]["Weight"]["RTIB"])
            cgmFittingProcedure.updateMarkerWeight("RANK",inputs["Fitting"]["Weight"]["RANK"])
            cgmFittingProcedure.updateMarkerWeight("RHEE",inputs["Fitting"]["Weight"]["RHEE"])
            cgmFittingProcedure.updateMarkerWeight("RTOE",inputs["Fitting"]["Weight"]["RTOE"])
            cgmFittingProcedure.updateMarkerWeight("LTHI",inputs["Fitting"]["Weight"]["LTHI"])
            cgmFittingProcedure.updateMarkerWeight("LKNE",inputs["Fitting"]["Weight"]["LKNE"])
            cgmFittingProcedure.updateMarkerWeight("LTIB",inputs["Fitting"]["Weight"]["LTIB"])
            cgmFittingProcedure.updateMarkerWeight("LANK",inputs["Fitting"]["Weight"]["LANK"])
            cgmFittingProcedure.updateMarkerWeight("LHEE",inputs["Fitting"]["Weight"]["LHEE"])
            cgmFittingProcedure.updateMarkerWeight("LTOE",inputs["Fitting"]["Weight"]["LTOE"])
               
            
            osrf = opensimFilters.opensimFittingFilter(iksetupFile, 
                                                              scalingOsim,
                                                              cgmFittingProcedure,
                                                              str(DATA_PATH) )
            acqStaticIK = osrf.run(acqStatic,str(DATA_PATH + calibrateFilenameLabelled ))        
            
            
            
            # --- final pyCGM2 model motion Filter ---
            # use fitted markers             
            modMotionFitted=modelFilters.ModelMotionFilter(scp,acqStaticIK,model,pyCGM2Enums.motionMethod.Sodervisk)
    
            modMotionFitted.compute()


        # eventual static acquisition to consider for joint kinematics  
        finalAcqStatic = acqStaticIK if args.ik else acqStatic

        #---- Joint kinematics----
        # relative angles
        modelFilters.ModelJCSFilter(model,finalAcqStatic).compute(description="vectoriel", pointLabelSuffix=pointSuffix)

        # detection of traveling axis
        longitudinalAxis,forwardProgression,globalFrame = btkTools.findProgressionAxisFromPelvicMarkers(finalAcqStatic,["LASI","RASI","RPSI","LPSI"])

        # absolute angles
        modelFilters.ModelAbsoluteAnglesFilter(model,finalAcqStatic,
                                               segmentLabels=["Left Foot","Right Foot","Pelvis"],
                                                angleLabels=["LFootProgress", "RFootProgress","Pelvis"],
                                                eulerSequences=["TOR","TOR", "ROT"],
                                                globalFrameOrientation = globalFrame,
                                                forwardProgression = forwardProgression).compute(pointLabelSuffix=pointSuffix)

        

        # ----------------------SAVE-------------------------------------------
        modelFile = open(DATA_PATH + subject+"-CGM2_2-pyCGM2.model", "w")
        cPickle.dump(model, modelFile)
        modelFile.close()

        # ----------------------DISPLAY ON VICON-------------------------------
        viconInterface.ViconInterface(NEXUS,
                                      model,finalAcqStatic,subject,
                                      pointSuffix,
                                      staticProcessing=True).run()

        # ========END of the nexus OPERATION if run from Nexus  =========


        if DEBUG:
            NEXUS.SaveTrial(30)

    else:
        raise Exception("NO Nexus connection. Turn on Nexus")
