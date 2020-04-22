import os
import threading
from paraview_postprocessing import *

def neck_measure_single(path, timeScale, cValueThreshold, lineResolution, isNeckFromPF):

    arCurves = []

    for fcase in arCases:

        print("")
        print("Working on case " + fcase + " ...")

        # source data
        inputFolder = os.path.join(resultsPath, fcase)

        if not(os.path.isdir(inputFolder)):
            print("ERROR: the data folder for this case does not exist")
            continue

        exodusFileName = detect_file(inputFolder, ".e")

        if exodusFileName:

            reader = open_exodus(exodusFileName)
            particleDiameter, gbWidth = domain_dimensions(reader, 'c', cValueThreshold, lineResolution)

            if not(isNeckFromPF):
                arTime, arNeck = neck_from_vtk(reader, particleDiameter, 'c', cValueThreshold, lineResolution)
            else:
                csvFileName = detect_file(inputFolder, ".csv")

                if csvFileName:
                    arTime, arNeck = neck_from_pf(csvFileName, particleDiameter, gbWidth)

            arTime = [t*timeScale for t in arTime]

            curve = { 't': arTime, 'neck': arNeck, 'label': fcase }
            arCurves.append(curve)

    return arCurves

def neck_measure_serial(resultsPath, arCases, timeScale, cValueThreshold, lineResolution, isNeckFromPF):

    arCurves = []

    for fcase in arCases:

        print("")
        print("Working on case " + fcase + " ...")

        # source data
        inputFolder = os.path.join(resultsPath, fcase)

        if not(os.path.isdir(inputFolder)):
            print("ERROR: the data folder for this case does not exist")
            continue

        exodusFileName = detect_file(inputFolder, ".e")

        if exodusFileName:

            reader = open_exodus(exodusFileName)
            particleDiameter, gbWidth = domain_dimensions(reader, 'c', cValueThreshold, lineResolution)

            if not(isNeckFromPF):
                arTime, arNeck = neck_from_vtk(reader, particleDiameter, 'c', cValueThreshold, lineResolution)
            else:
                csvFileName = detect_file(inputFolder, ".csv")

                if csvFileName:
                    arTime, arNeck = neck_from_pf(csvFileName, particleDiameter, gbWidth)

            arTime = [t*timeScale for t in arTime]

            curve = { 't': arTime, 'neck': arNeck, 'label': fcase }
            arCurves.append(curve)

    return arCurves

def neck_measure_parallel(resultsPath, arCases, timeScale, cValueThreshold, lineResolution, isNeckFromPF):

    arCurves = []

    class PlotStack:
        def __init__(self):
            self._lock = threading.Lock()

        def addCurve(self, x, y, title):
            with self._lock:
                curve = { 't': x, 'neck': y, 'label': title }
                arCurves.append(curve)

    plotStack = PlotStack()

    def thread_parse(fcase):
        print("")
        print("Working on case " + fcase + " ...")

        # source data
        inputFolder = os.path.join(resultsPath, fcase)

        if not(os.path.isdir(inputFolder)):
            print("ERROR: the data folder for this case does not exist")
            return        


        exodusFileName = detect_file(inputFolder, ".e")

        if exodusFileName:

            reader = open_exodus(exodusFileName)
            particleDiameter, gbWidth = domain_dimensions(reader, 'c', cValueThreshold, lineResolution)

            if not(isNeckFromPF):
                arTime, arNeck = neck_from_vtk(reader, particleDiameter, 'c', cValueThreshold, lineResolution)
            else:
                csvFileName = detect_file(inputFolder, ".csv")

                if csvFileName:
                    arTime, arNeck = neck_from_pf(csvFileName, particleDiameter, gbWidth)

            arTime = [t*timeScale for t in arTime]

            plotStack.addCurve(arTime, arNeck, fcase)

    threads = list()
    for fcase in arCases:
        x = threading.Thread(target=thread_parse, args=(fcase,))
        threads.append(x)
        x.start()

    for thread in threads:
        thread.join()

    return arCurves