import sys
import glob
import re
import os


# CONSTANTS
cased_path = glob.glob(re.sub(r'([^:])(?=[/\\]|$)', r'[\1]', __file__))[0]
MAIN_PYCGM2_PATH = os.path.abspath(os.path.join(os.path.dirname(cased_path), os.pardir)) + "\\"

#  [Optional] setting folder
PYCGM2_SETTINGS_FOLDER = MAIN_PYCGM2_PATH+"pyCGM2\Settings\\"


#  [Optional]programData
if os.path.isfile( MAIN_PYCGM2_PATH + "localSettings") or os.path.isfile( MAIN_PYCGM2_PATH + "developMode"):
    PYCGM2_APPDATA_PATH = PYCGM2_SETTINGS_FOLDER
else:
    PYCGM2_APPDATA_PATH = os.getenv("PROGRAMDATA")+"\\pyCGM2\\"


# [Optional]: Apps path
MAIN_PYCGM2_APPS_PATH = MAIN_PYCGM2_PATH+"Apps\\"

# [Optional] path to embbbed Normative data base.
NORMATIVE_DATABASE_PATH = MAIN_PYCGM2_PATH +"pyCGM2\\Data\\normativeData\\"  # By default, use pyCGM2-embedded normative data ( Schartz - Pinzone )

# [Optional] main folder containing osim model
OPENSIM_PREBUILD_MODEL_PATH = PYCGM2_APPDATA_PATH + "opensim\\"


# [Optional] path pointing at Data Folders used for Tests
TEST_DATA_PATH = "C:\\Users\\HLS501\\Documents\\VICON DATA\\pyCGM2-Data\\"
MAIN_BENCHMARK_PATH = "C:\\Users\\HLS501\\Documents\\VICON DATA\\pyCGM2-benchmarks\\Gait patterns\\"

# [optional] path pointing pyCGM2-Nexus tools
NEXUS_PYCGM2_TOOLS_PATH = MAIN_PYCGM2_PATH + "pyCGM2\\Nexus\\"
