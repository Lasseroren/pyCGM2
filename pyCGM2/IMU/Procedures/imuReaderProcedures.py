import pandas as pd
import numpy as np
import btk
import re

import pyCGM2; LOGGER = pyCGM2.LOGGER  
from pyCGM2.IMU import imu
from pyCGM2.IMU import imuFilters
from pyCGM2.IMU.Procedures import imuMotionProcedure
from pyCGM2.Tools import btkTools
from pyCGM2.Signal import signal_processing


def synchroniseNotAlignedCsv(fullfilenames,timeColumn = "time_s"):

    def find_nearest(array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx,array[idx]

    datasets= list()
    for fullfilename in fullfilenames:
        datasets.append( pd.read_csv(fullfilename))

    times0 = list()
    for dataset in datasets:
        times0.append(dataset[timeColumn].values[0])
    time_0 =  max(times0)

    datasets_0 = list()
    numberOfFrames = list()
    for dataset in datasets:
        idx0,value0 = find_nearest(dataset[timeColumn].values,time_0)
        numberOfFrames.append(dataset.iloc[idx0:].shape[0])
        datasets_0.append(dataset.iloc[idx0:])
    nFrames =  min(numberOfFrames)

    datasets_equal = list()
    for dataset in datasets_0:
        datasets_equal.append(dataset[0:nFrames])

    return datasets_equal

class ImuReaderProcedures(object):
    def __init__(self):
        self.m_downsampleFreq = None

    def downsample(self,freq):
        self.m_downsampleFreq = freq

class CsvProcedure(ImuReaderProcedures):
    def __init__(self,fullfilename,translators,freq = "Auto" , timeColumn = "time_s"):
        super(CsvProcedure, self).__init__()
        
        self.m_data = pd.read_csv(fullfilename)
        self.m_translators = translators

        self.m_freq = freq
        self.__freq = self.m_freq
        self.m_timeColumn = timeColumn


    def read(self):
    
        if self.m_freq == "Auto":
            self.m_freq = int(1/(self.m_data[self.m_timeColumn].to_numpy()[1] - 
                        self.m_data[self.m_timeColumn].to_numpy()[0]))
            self.__freq = self.m_freq

         
        acceleration = np.zeros((self.m_data.shape[0],3))
        try:
            acceleration = np.array([self.m_data[self.m_translators["Accel.X"]].to_numpy(), 
                                    self.m_data[self.m_translators["Accel.Y"]].to_numpy(), 
                                    self.m_data[self.m_translators["Accel.Z"]].to_numpy()]).T
        except:
            LOGGER.logger.warning("[pyCGM2] - no accelerometer detected in your data ")


        angularVelocity = np.zeros((self.m_data.shape[0],3))
        try:
            angularVelocity = np.array([self.m_data[self.m_translators["AngularVelocity.X"]].to_numpy(), 
                                self.m_data[self.m_translators["AngularVelocity.Y"]].to_numpy(), 
                                self.m_data[self.m_translators["AngularVelocity.Z"]].to_numpy()]).T
        except:
            LOGGER.logger.warning("[pyCGM2] - no goniometer detected in your data ")

        magnetometer = np.zeros((self.m_data.shape[0],3))
        try:
            magnetometer = np.array([self.m_data[self.m_translators["Magneto.X"]].to_numpy(), 
                                    self.m_data[self.m_translators["Magneto.Y"]].to_numpy(), 
                                    self.m_data[self.m_translators["Magneto.Z"]].to_numpy()]).T
        except:
            LOGGER.logger.warning("[pyCGM2] - no magnetometer detected in your data ")

        if self.m_downsampleFreq is not None:
            acceleration = signal_processing.downsample(acceleration,self.m_freq,self.m_downsampleFreq)
            angularVelocity = signal_processing.downsample(angularVelocity,self.m_freq,self.m_downsampleFreq)
            magnetometer = signal_processing.downsample(magnetometer,self.m_freq,self.m_downsampleFreq)
            self.m_freq = self.m_downsampleFreq    

        imuInstance =  imu.Imu(self.m_freq,acceleration,angularVelocity,magnetometer)

        
        requiredCols = [self.m_translators["Quaternion.X"],self.m_translators["Quaternion.Y"], self.m_translators["Quaternion.Z"], self.m_translators["Quaternion.R"]]
        if all(column in self.m_data.columns for column in requiredCols):
            LOGGER.logger.info("[pyCGM2] - your csv contains quaternions- - the reader compute the imu Motion")

            quaternions =  np.array([self.m_data[self.m_translators["Quaternion.X"]].to_numpy(),
                                    self.m_data[self.m_translators["Quaternion.Y"]].to_numpy(),
                                    self.m_data[self.m_translators["Quaternion.Z"]].to_numpy(), 
                                    self.m_data[self.m_translators["Quaternion.R"]].to_numpy()]).T
            
            if self.m_downsampleFreq is not None:
                quaternions = signal_processing.downsample(quaternions,self.__freq,self.m_downsampleFreq)

            motProc = imuMotionProcedure.QuaternionMotionProcedure(quaternions)

            motFilter = imuFilters.ImuMotionFilter(imuInstance,motProc)
            motFilter.run()
    
        return imuInstance
        
class DataframeProcedure(ImuReaderProcedures):
    def __init__(self,dataframe,translators,freq = "Auto" , timeColumn = "time_s"):
        super(DataframeProcedure, self).__init__()
        
        self.m_data = dataframe
        self.m_translators = translators

        self.m_freq = freq
        self.__freq = self.m_freq
        self.m_timeColumn = timeColumn


    def read(self):
    
        if self.m_freq == "Auto":
            self.m_freq = int(1/(self.m_data[self.m_timeColumn].to_numpy()[1] - 
                        self.m_data[self.m_timeColumn].to_numpy()[0]))
            self.__freq = self.m_freq

            print(self.__freq)

        acceleration = np.zeros((self.m_data.shape[0],3))
        try:
            acceleration = np.array([self.m_data[self.m_translators["Accel.X"]].to_numpy(), 
                                    self.m_data[self.m_translators["Accel.Y"]].to_numpy(), 
                                    self.m_data[self.m_translators["Accel.Z"]].to_numpy()]).T
        except:
            LOGGER.logger.warning("[pyCGM2] - no accelerometer detected in your data ")


        angularVelocity = np.zeros((self.m_data.shape[0],3))
        try:
            angularVelocity = np.array([self.m_data[self.m_translators["AngularVelocity.X"]].to_numpy(), 
                                self.m_data[self.m_translators["AngularVelocity.Y"]].to_numpy(), 
                                self.m_data[self.m_translators["AngularVelocity.Z"]].to_numpy()]).T
        except:
            LOGGER.logger.warning("[pyCGM2] - no goniometer detected in your data ")

        magnetometer = np.zeros((self.m_data.shape[0],3))
        try:
            magnetometer = np.array([self.m_data[self.m_translators["Magneto.X"]].to_numpy(), 
                                    self.m_data[self.m_translators["Magneto.Y"]].to_numpy(), 
                                    self.m_data[self.m_translators["Magneto.Z"]].to_numpy()]).T
        except:
            LOGGER.logger.warning("[pyCGM2] - no magnetometer detected in your data ")

        
        if self.m_downsampleFreq is not None:
            acceleration = signal_processing.downsample(acceleration,self.m_freq,self.m_downsampleFreq)
            angularVelocity = signal_processing.downsample(angularVelocity,self.m_freq,self.m_downsampleFreq)
            magnetometer = signal_processing.downsample(magnetometer,self.m_freq,self.m_downsampleFreq)
            self.m_freq = self.m_downsampleFreq 


        imuInstance =  imu.Imu(self.m_freq,acceleration,angularVelocity,magnetometer)

        
        requiredCols = [self.m_translators["Quaternion.X"],self.m_translators["Quaternion.Y"], self.m_translators["Quaternion.Z"], self.m_translators["Quaternion.R"]]
        if all(column in self.m_data.columns for column in requiredCols):
            LOGGER.logger.info("[pyCGM2] - your csv contains quaternions- - the reader compute the imu Motion")

            quaternions =  np.array([self.m_data[self.m_translators["Quaternion.X"]].to_numpy(),
                                    self.m_data[self.m_translators["Quaternion.Y"]].to_numpy(),
                                    self.m_data[self.m_translators["Quaternion.Z"]].to_numpy(), 
                                    self.m_data[self.m_translators["Quaternion.R"]].to_numpy()]).T

            if self.m_downsampleFreq is not None:
                quaternions = signal_processing.downsample(quaternions,self.__freq,self.m_downsampleFreq)
                

            motProc = imuMotionProcedure.QuaternionMotionProcedure(quaternions)

            motFilter = imuFilters.ImuMotionFilter(imuInstance,motProc)
            motFilter.run()
    
        return imuInstance

class C3dBlueTridentProcedure(ImuReaderProcedures):
    def __init__(self,fullfilename,viconDeviceId):
        super(C3dBlueTridentProcedure, self).__init__()
        
        self.m_acq = btkTools.smartReader(fullfilename)
        self.m_id = viconDeviceId


    def read(self):

        freq = self.m_acq.GetAnalogFrequency()
    
        channels = []
        for it in btk.Iterate(self.m_acq.GetAnalogs()):
            desc = it.GetDescription()
            label = it.GetLabel()
            values= it.GetValues()
            nAnalogframes = values.shape[0]

            if "Vicon BlueTrident" in desc:
                deviceId = re.findall( "\[(.*?)\]", desc)[0].split(",")[0]
                if deviceId ==  self.m_id:
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

        angularVelocity = np.zeros((nAnalogframes,3))
        for it in ["gyro.x","gyro.y","gyro.z"]:
            for channel in channels:
                if it in channel.GetLabel():
                    if ".x" in it:
                        angularVelocity[:,0] = channel.GetValues().reshape(nAnalogframes)
                    if ".y" in it:
                        angularVelocity[:,1] = channel.GetValues().reshape(nAnalogframes)
                    if ".z" in it:
                        angularVelocity[:,2] = channel.GetValues().reshape(nAnalogframes)
    
        magnetometer = np.zeros((nAnalogframes,3))
        for it in ["mag.x","mag.y","mag.z"]:
            for channel in channels:
                if it in channel.GetLabel():
                    if ".x" in it:
                        magnetometer[:,0] = channel.GetValues().reshape(nAnalogframes)
                    if ".y" in it:
                        magnetometer[:,1] = channel.GetValues().reshape(nAnalogframes)
                    if ".z" in it:
                        magnetometer[:,2] = channel.GetValues().reshape(nAnalogframes)


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
        
        if self.m_downsampleFreq is not None:
            acceleration = signal_processing.downsample(acceleration,freq,self.m_downsampleFreq)
            highAccel = signal_processing.downsample(highAccel,freq,self.m_downsampleFreq)
            angularVelocity = signal_processing.downsample(angularVelocity,freq,self.m_downsampleFreq)
            magnetometer = signal_processing.downsample(magnetometer,freq,self.m_downsampleFreq)
            globalAngle = signal_processing.downsample(globalAngle,freq,self.m_downsampleFreq)

            freq = self.m_downsampleFreq
            
        imuInstance =  imu.Imu(freq,acceleration,angularVelocity,magnetometer)

        if np.all(globalAngle!=0):
            LOGGER.logger.info("[pyCGM2] - your c3d contains global Angle - the reader computes the imu Motion")

            motProc = imuMotionProcedure.GlobalAngleMotionProcedure(globalAngle)
            motFilter = imuFilters.ImuMotionFilter(imuInstance,motProc)
            motFilter.run()


        return imuInstance 
            
        

# def readmultipleBlueTridentCsv(fullfilenames,freq):

#     def find_nearest(array, value):
#         array = np.asarray(array)
#         idx = (np.abs(array - value)).argmin()
#         return idx,array[idx]

#     datasets= list()
#     for fullfilename in fullfilenames:
#         datasets.append( pd.read_csv(fullfilename))

#     times0 = list()
#     for dataset in datasets:
#         times0.append(dataset["time_s"].values[0])
#     time_0 =  max(times0)

#     datasets_0 = list()
#     numberOfFrames = list()
#     for dataset in datasets:
#         idx0,value0 = find_nearest(dataset["time_s"].values,time_0)
#         numberOfFrames.append(dataset.iloc[idx0:].shape[0])
#         datasets_0.append(dataset.iloc[idx0:])
#     nFrames =  min(numberOfFrames)

#     datasets_equal = list()
#     for dataset in datasets_0:
#         datasets_equal.append(dataset[0:nFrames])