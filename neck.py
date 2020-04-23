from neck_measure import *
from settings import *
from source_data import *
import argparse
import numpy as np
import glob, os, errno

parser = argparse.ArgumentParser(description='Process neck width')

parser.add_argument("-p", "--plot", help="Plot results", action="store_true")
parser.add_argument("-m", "--thread", help="run in parallel", action="store_true")
parser.add_argument("-t", "--time", type=float, help="Time scale")
parser.add_argument("-f", "--folder", type=str, help="A folder  results to")
parser.add_argument("-s", "--save", type=str, help="A folder to save results to")
parser.add_argument("-l", "--load", type=str, help="A folder to load previously saved csv from")

args = parser.parse_args()

if not(args.plot) and not(args.save):
    sys.exit("Choose an action: save or plot")

if args.load:

    if not(os.path.isdir(args.load)):
        exit("ERROR: the csv data folder " + args.load + " does not exist")

    onlyfiles = [f for f in os.listdir(args.load) if os.path.isfile(os.path.join(args.load, f))]

    arCurves = []
    for fileName in onlyfiles:
        fullPath = os.path.join(args.load, fileName)
        data = np.genfromtxt(fullPath, dtype=float, delimiter=',', names=True)

        label = os.path.splitext(fileName)[0]
        curve = { 't': data["t"], 'neck': data["neck"], 'label': label }
        arCurves.append(curve)

else:

    # folder to get results from
    if args.folder:
        if not(os.path.isdir(args.folder)):
            exit("ERROR: the exodus data folder " + args.folder + " does not exist")

        pathToLoad = args.folder
        casesToLoad = [ item for item in os.listdir(args.folder) if os.path.isdir(os.path.join(args.folder, item)) ]

    else:
        pathToLoad = resultsPath
        casesToLoad = arCases

    # time scale
    if args.time:
        tscale = args.time
    else:
        tscale = timeScale

    # sequential or parallel
    if args.thread:
        arCurves = neck_measure_parallel(pathToLoad, casesToLoad, tscale, cValueThreshold, lineResolution, isNeckFromPF)
    else:
        arCurves = neck_measure_serial(pathToLoad, casesToLoad, tscale, cValueThreshold, lineResolution, isNeckFromPF)

# Plot
if args.plot:
    import matplotlib.pyplot as plt

    for curve in arCurves:
        plt.plot(curve['t'], curve['neck'], marker='', linestyle='-', label=curve['label'])

    plt.xlabel('time')
    plt.ylabel('x / r')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.show()

if args.save:

    try:
        os.makedirs(args.save)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    for curve in arCurves:
        fileName = curve['label'] + '.csv'
        fullPath = os.path.join(args.save, fileName)
        np.savetxt(fullPath, np.column_stack((curve['t'], curve['neck'])), delimiter=',', comments='', header="t,neck")

    print("The CSV files have been saved")