import os
import matplotlib.pyplot as plt
from paraview_postprocessing import *

# settings
isNeckFromPF = True
cValueThreshold = 0.52
timeScale = 1e3
resultsPath = "/mnt/x/results"

# input files
arCases = [
    #"T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=energy",
    #"T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=energy_reduced_mobs",
    "T=1223_time=1e3_length=1e-6_width=15_dia=145_mobfac=energy",
    "T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=energy",
    "T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=ideal_reduced_mobs",
    "T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=ideal_no_gbsurf"
]

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
        particleDiameter, gbWidth = domain_dimensions(reader, 'c', cValueThreshold)

        if not(isNeckFromPF):
            arTime, arNeck = neck_from_vtk(reader, particleDiameter, 'c', cValueThreshold)
        else:
            csvFileName = detect_file(inputFolder, ".csv")

            if csvFileName:
                arTime, arNeck = neck_from_pf(csvFileName, particleDiameter, gbWidth)

        arTime = [t*timeScale for t in arTime]

        plt.plot(arTime, arNeck, marker='', linestyle='-', label=fcase)


plt.xlabel('time')
plt.ylabel('x / r')
plt.legend(loc='lower right')
plt.grid(True)
plt.show()



