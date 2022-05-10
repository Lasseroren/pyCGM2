# coding: utf-8
# pytest -s --disable-pytest-warnings  test_gap.py::Test_gap::test_kalman



import logging
import matplotlib.pyplot as plt

import pyCGM2; LOGGER = pyCGM2.LOGGER

# pyCGM2
from pyCGM2.Tools import  btkTools
from pyCGM2.Gap import gapFilters, gapFillingProcedures

class Test_gap:
    def test_kalman(self):


        MAIN_PATH = pyCGM2.TEST_DATA_PATH + "LowLevel\\gapFilling\\gaitData\\"


        gaitFilename="gait Trial 01.c3d"
        acq = btkTools.smartReader(str(MAIN_PATH +  gaitFilename))

        gfp = gapFillingProcedures.LowDimensionalKalmanFilterProcedure()
        gff = gapFilters.GapFillingFilter(gfp, acq)
        gff.fill()

        filledAcq = gff.getFilledAcq()
        filledMarkers = gff.getFilledMarkers()

        #btkTools.smartWriter("testEvent0.c3d", acq)
