import os
import matplotlib.pyplot as plt
from paraview_postprocessing import *

# settings
cValueThreshold = 0.52
timeScale = 1e3
resultsPath = "/mnt/x/results"

# input files
arCases = [
    "T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=energy",
    "T=1223_time=1e3_length=1e-6_width=8_dia=145_mobfac=ideal"
]

for fcase in arCases:

    print("")
    print("Working on case " + fcase + " ...")

    # source data
    inputFolder = os.path.join(resultsPath, fcase)

    if not(os.path.isdir(inputFolder)):
        print("ERROR: the data folder for this case does not exist")
        continue        

    fNames = [fn for fn in os.listdir(inputFolder) if fn.endswith(".e")]
    fCount = len(fNames)

    if (fCount == 0):
        print("ERROR: unable to detect exodus file for this case, check input folder")
        continue

    fileName = fNames[0]
    if (fCount > 1):
        print("NOTICE: several exodus files found, the first is used: " + fileName)

    inputFile = os.path.join(inputFolder, fileName)
    arTime, arNeck = analyze_neck(inputFile, 'c', cValueThreshold)
    arTime = [t*timeScale for t in arTime]

    plt.plot(arTime, arNeck, marker='', linestyle='-', label=fcase)


plt.xlabel('time')
plt.ylabel('x / r')
plt.legend(loc='lower right')
plt.grid(True)
plt.show()



