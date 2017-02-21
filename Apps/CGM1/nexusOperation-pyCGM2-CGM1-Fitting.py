# -*- coding: utf-8 -*-

import os
import logging
import matplotlib.pyplot as plt
import json
import pdb
import cPickle
import json


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


# pyCGM2 libraries
from pyCGM2.Tools import btkTools
import pyCGM2.enums as pyCGM2Enums
from pyCGM2.Model.CGM2 import cgm, modelFilters, forceplates,bodySegmentParameters
#
from pyCGM2 import viconInterface



if __name__ == "__main__":


    DEBUG = False

    NEXUS = ViconNexus.ViconNexus()
    NEXUS_PYTHON_CONNECTED = NEXUS.Client.IsConnected()


    if NEXUS_PYTHON_CONNECTED: # run Operation

        # ----------------------INPUTS-------------------------------------------
        # --- acquisition file and path----
        if DEBUG:
            DATA_PATH = "C:\\Users\\AAA34169\\Documents\\VICON DATA\\pyCGM2-Data\\CGM1\\CGM1-NexusPlugin\\New Session 3\\"
            reconstructFilenameLabelledNoExt = "MRI-US-01, 2008-08-08, 3DGA 12"
            NEXUS.OpenTrial( str(DATA_PATH+reconstructFilenameLabelledNoExt), 10 )

        else:
            DATA_PATH, reconstructFilenameLabelledNoExt = NEXUS.GetTrialName()

        reconstructFilenameLabelled = reconstructFilenameLabelledNoExt+".c3d"

        logging.info( "data Path: "+ DATA_PATH )
        logging.info( "calibration file: "+ reconstructFilenameLabelled)

        # ---- pyCGM2 files ----
        if not os.path.isfile(DATA_PATH + "pyCGM2.model"):
            raise Exception ("pyCGM2.model file doesn't exist. Run Calibration operation")
        else:
            f = open(DATA_PATH + 'pyCGM2.model', 'r')
            model = cPickle.load(f)
            f.close()

        if not os.path.isfile(DATA_PATH + "pyCGM2.inputs"): #DATA_PATH + "pyCGM2.inputs"):
            raise Exception ("pyCGM2.inputs file doesn't exist")
        else:
            inputs = json.loads(open(DATA_PATH + 'pyCGM2.inputs').read())

        # ---- configuration parameters ----
        markerDiameter = float(inputs["Calibration"]["Marker diameter"])
        pointSuffix = inputs["Calibration"]["Point suffix"]

        # --------------------------SUBJECT -----------------------------------
        subjects = NEXUS.GetSubjectNames()
        subject =   subjects[0]
        logging.info(  "Subject name : " + subject  )
        Parameters = NEXUS.GetSubjectParamNames(subject)


        # --------------------------MODELLLING--------------------------
        # --- btk acquisition ----
        acqGait = btkTools.smartReader(str(DATA_PATH + reconstructFilenameLabelled))

        # --relabel PIG output if processing previously---
        cgm.CGM.reLabelPigOutputs(acqGait)


        scp=modelFilters.StaticCalibrationProcedure(model) # procedure
        
        # ---Motion filter----    
        modMotion=modelFilters.ModelMotionFilter(scp,acqGait,model,pyCGM2Enums.motionMethod.Native,
                                                  markerDiameter=markerDiameter,
                                                  viconCGM1compatible=True)

        modMotion.compute()


        #---- Joint kinematics----
        # relative angles
        modelFilters.ModelJCSFilter(model,acqGait).compute(description="vectoriel", pointLabelSuffix=pointSuffix)

        # detection of traveling axis
        longitudinalAxis,forwardProgression,globalFrame = btkTools.findProgressionFromPoints(acqGait,"SACR","midASIS","LPSI")
        # absolute angles        
        modelFilters.ModelAbsoluteAnglesFilter(model,acqGait,
                                               segmentLabels=["Left Foot","Right Foot","Pelvis"],
                                                angleLabels=["LFootProgress", "RFootProgress","Pelvis"],
                                                eulerSequences=["TOR","TOR", "TOR"],
                                                globalFrameOrientation = globalFrame,
                                                forwardProgression = forwardProgression).compute(pointLabelSuffix=pointSuffix)

        #---- Body segment parameters----
        bspModel = bodySegmentParameters.Bsp(model)
        bspModel.compute()

        # --- force plate handling----
        # find foot  in contact        
        mappedForcePlate = forceplates.matchingFootSideOnForceplate(acqGait)
        # assembly foot and force plate        
        modelFilters.ForcePlateAssemblyFilter(model,acqGait,mappedForcePlate,
                                 leftSegmentLabel="Left Foot",
                                 rightSegmentLabel="Right Foot").compute()

        #---- Joint kinetics----
        idp = modelFilters.CGMLowerlimbInverseDynamicProcedure()
        modelFilters.InverseDynamicFilter(model,
                             acqGait,
                             procedure = idp,
                             projection = pyCGM2Enums.MomentProjection.Distal
                             ).compute(pointLabelSuffix=pointSuffix)

        #---- Joint energetics----
        modelFilters.JointPowerFilter(model,acqGait).compute(pointLabelSuffix=pointSuffix)

        # ----------------------DISPLAY ON VICON-------------------------------
        viconInterface.ViconInterface(NEXUS,model,acqGait,subject).run()

        # ========END of the nexus OPERATION if run from Nexus  =========

        if DEBUG:

            NEXUS.SaveTrial(30)
    
            # code below is similar to operation "nexusOperation_pyCGM2-CGM1-metadata.py"        
            # add metadata
            acqGait2= btkTools.smartReader(str(DATA_PATH + reconstructFilenameLabelled))
            md_Model = btk.btkMetaData('MODEL') # create main metadata
            btk.btkMetaDataCreateChild(md_Model, "NAME", "CGM1")
            btk.btkMetaDataCreateChild(md_Model, "PROCESSOR", "pyCGM2")
            acqGait2.GetMetaData().AppendChild(md_Model)
    
            #writer
            btkTools.smartWriter(acqGait2,str(DATA_PATH + reconstructFilenameLabelled[:-4] + ".c3d"))


    else:
        raise Exception("NO Nexus connection. Turn on Nexus")
