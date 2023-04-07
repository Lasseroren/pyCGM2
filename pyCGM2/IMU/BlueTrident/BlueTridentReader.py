# coding: utf-8
import re
import numpy as np
import pandas as pd


import pyCGM2
LOGGER = pyCGM2.LOGGER
from pyCGM2.IMU.BlueTrident import BlueTrident
try:
    import btk
except:
    try:
        from pyCGM2 import btk
    except:
        LOGGER.logger.error("[pyCGM2] btk not found on your system")

def readmultipleBlueTridentCsv(fullfilenames,freq):

    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx,array[idx]

    datasets= list()
    for fullfilename in fullfilenames:
        datasets.append( pd.read_csv(fullfilename))

    times0 = list()
    for dataset in datasets:
        times0.append(dataset["time_s"].values[0])
    time_0 =  max(times0)

    datasets_0 = list()
    numberOfFrames = list()
    for dataset in datasets:
        idx0,value0 = find_nearest(dataset["time_s"].values,time_0)
        numberOfFrames.append(dataset.iloc[idx0:].shape[0])
        datasets_0.append(dataset.iloc[idx0:])
    nFrames =  min(numberOfFrames)

    datasets_equal = list()
    for dataset in datasets_0:
        datasets_equal.append(dataset[0:nFrames])

    imuInstances = list()
    for data in datasets_equal:

        acceleration = np.array([data["ax_m/s/s"].to_numpy(), 
                                 data["ay_m/s/s"].to_numpy(), 
                                 data["az_m/s/s"].to_numpy()]).T
        
        angularVelocity = np.array([data["gx_deg/s"].to_numpy(), 
                            data["gy_deg/s"].to_numpy(), 
                            data["gz_deg/s"].to_numpy()]).T

        imuInstance = BlueTrident.BlueTrident(freq,
                              acceleration,
                              angularVelocity,None,None,None)

        imuInstances.append(imuInstance)


    return imuInstances



def readBlueTridentCsv(fullfilename,freq):
    data = pd.read_csv(fullfilename)
    
    acceleration = np.array([data["ax_m/s/s"].to_numpy(), 
                             data["ay_m/s/s"].to_numpy(), 
                             data["az_m/s/s"].to_numpy()]).T

    angularVelocity = np.array([data["gx_deg/s"].to_numpy(), 
                             data["gy_deg/s"].to_numpy(), 
                             data["gz_deg/s"].to_numpy()]).T

    imuInstance = BlueTrident.BlueTrident(freq,
                              acceleration,
                              angularVelocity,None,None,None)

    return imuInstance


# def correctBlueTridentIds(acq):
#     correctFlag = False

#     # extract id from description
#     ids = list()
#     for it in btk.Iterate(acq.GetAnalogs()):
#         desc = it.GetDescription()
#         analoglabel = it.GetLabel()
#         if "Vicon BlueTrident" in desc:
#             id = re.findall( "\[(.*?)\]", desc)[0].split(",")

#             if id[0] not in ids:  ids.append(id[0])

#     if ids[0] !=1:
#         correctFlag = True
#         LOGGER.logger.warning("Blue trident ids do not start from 1 ")

#     # correct description
#     if correctFlag:
#         newIds = list(np.arange(1,len(ids)+1))

#         for it in btk.Iterate(acq.GetAnalogs()):
#             desc = it.GetDescription()
#             analoglabel = it.GetLabel()
#             if "Vicon BlueTrident" in desc:
#                 id = re.findall( "\[(.*?)\]", desc)[0].split(",")[0]
#                 index = ids.index(id)
#                 newdesc = desc.replace("["+id, "["+str(newIds[index]))
#                 it.SetDescription(newdesc)

#     return acq



def btkGetBlueTrident(acq, id):

    

    channels = []
    for it in btk.Iterate(acq.GetAnalogs()):
        desc = it.GetDescription()
        label = it.GetLabel()
        values= it.GetValues()
        nAnalogframes = values.shape[0]

        if "Vicon BlueTrident" in desc:
            deviceId = re.findall( "\[(.*?)\]", desc)[0].split(",")[0]
            if deviceId == id:
                channels.append(it)

    acceleration = np.zeros((nAnalogframes,3))
    for it in ["accel.x","accel.y","accel.z"]:
        for channel in channels:
            if it in channel.GetLabel():
                if ".x" in it:
                     acceleration[:,0] = channel.GetValues().reshape(nAnalogframes)
                if ".y" in it:
                    acceleration[:,1] = channel.GetValues().reshape(nAnalogframes)
                if ".z" in it:
                   acceleration[:,2] = channel.GetValues().reshape(nAnalogframes)

    omega = np.zeros((nAnalogframes,3))
    for it in ["gyro.x","gyro.y","gyro.z"]:
        for channel in channels:
            if it in channel.GetLabel():
                if ".x" in it:
                    omega[:,0] = channel.GetValues().reshape(nAnalogframes)
                if ".y" in it:
                    omega[:,1] = channel.GetValues().reshape(nAnalogframes)
                if ".z" in it:
                   omega[:,2] = channel.GetValues().reshape(nAnalogframes)
 
    mag = np.zeros((nAnalogframes,3))
    for it in ["mag.x","mag.y","mag.z"]:
        for channel in channels:
            if it in channel.GetLabel():
                if ".x" in it:
                     mag[:,0] = channel.GetValues().reshape(nAnalogframes)
                if ".y" in it:
                    mag[:,1] = channel.GetValues().reshape(nAnalogframes)
                if ".z" in it:
                   mag[:,2] = channel.GetValues().reshape(nAnalogframes)


    globalAngle = np.zeros((nAnalogframes,3))
    for it in ["Global Angle.x","Global Angle.y","Global Angle.z"]:
        for channel in channels:
            if it in channel.GetLabel():
                if ".x" in it:
                    globalAngle[:,0] = channel.GetValues().reshape(nAnalogframes)
                if ".y" in it:
                    globalAngle[:,1] = channel.GetValues().reshape(nAnalogframes)
                if ".z" in it:
                   globalAngle[:,2] = channel.GetValues().reshape(nAnalogframes)

    highAccel = np.zeros((nAnalogframes,3))
    for it in ["HighG.x","HighG.y","HighG.z"]:
        for channel in channels:
            if it in channel.GetLabel():
                if ".x" in it:
                    highAccel[:,0] = channel.GetValues().reshape(nAnalogframes)
                if ".y" in it:
                    highAccel[:,1] = channel.GetValues().reshape(nAnalogframes)
                if ".z" in it:
                   highAccel[:,2] = channel.GetValues().reshape(nAnalogframes)
    
    imuInstance = BlueTrident.BlueTrident(acq.GetAnalogFrequency(),
                              acceleration,omega,mag,globalAngle,highAccel)
    return imuInstance 
