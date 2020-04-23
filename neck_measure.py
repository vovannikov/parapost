import os
import threading
from paraview_postprocessing import *

def parse_case(resultsPath, fcase, timeScale, cValueThreshold, lineResolution, isNeckFromPF):

    print("")
    print("Working on case " + fcase + " ...")

    # source data
    inputFolder = os.path.join(resultsPath, fcase)

    if not(os.path.isdir(inputFolder)):
        print("ERROR: the data folder for this case does not exist")
        return None

    exodusFileName = detect_file(inputFolder, ".e")

    if exodusFileName:

        reader = open_exodus(exodusFileName)
        particleDiameter, gbWidth = domain_dimensions(reader, 'c', cValueThreshold, lineResolution)

        if not(isNeckFromPF):
            arTime, arNeck = neck_from_vtk(reader, particleDiameter, 'c', cValueThreshold, lineResolution)
            _, arShrinkage = shrinkage_from_vtk(reader, particleDiameter, 'c', cValueThreshold, lineResolution)
        else:
            csvFileName = detect_file(inputFolder, ".csv")

            if csvFileName:
                arTime, arNeck = neck_from_pf(csvFileName, particleDiameter, gbWidth)
                arShrinkage = [0] * len(arNeck)

        arTime = [t*timeScale for t in arTime]

        curve = { 't': arTime, 'neck': arNeck, 'shrinkage': arShrinkage, 'label': fcase }

        return curve
    
    else:

        return None

def neck_measure_serial(resultsPath, arCases, timeScale, cValueThreshold, lineResolution, isNeckFromPF):

    arCurves = []

    for fcase in arCases:

        curve = parse_case(resultsPath, fcase, timeScale, cValueThreshold, lineResolution, isNeckFromPF)
        if curve:
            arCurves.append(curve)

    return arCurves

def neck_measure_parallel(resultsPath, arCases, timeScale, cValueThreshold, lineResolution, isNeckFromPF):

    arCurves = []

    class PlotStack:
        def __init__(self):
            self._lock = threading.Lock()

        def addCurve(self, curve):
            with self._lock:
                arCurves.append(curve)

    plotStack = PlotStack()

    def thread_parse(fcase):
        curve = parse_case(resultsPath, fcase, timeScale, cValueThreshold, lineResolution, isNeckFromPF)

        if curve:
            plotStack.addCurve(curve)

    threads = list()
    for fcase in arCases:
        x = threading.Thread(target=thread_parse, args=(fcase,))
        threads.append(x)
        x.start()

    for thread in threads:
        thread.join()

    return arCurves