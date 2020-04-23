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
parser.add_argument("-c", "--cases", type=str, nargs='+', help="List of cases to handle")

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
        curve = { 't': data["t"], 'neck': data["neck"], 'shrinkage': data["shrinkage"], 'label': label }
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

    # cases
    if args.cases:
        casesToLoad = args.cases

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

    fig, axes = plt.subplots(nrows=1, ncols=2)
    fig.suptitle('Neck growth and shrinkage')

    for curve in arCurves:
        axes[0].plot(curve['t'], curve['neck'], marker='', linestyle='-', label=curve['label'])
        axes[1].plot(curve['t'], curve['shrinkage'], marker='', linestyle='-', label=curve['label'])

    axes[0].set_xlabel('time')
    axes[0].set_ylabel('x / r')
    axes[0].grid(True)

    axes[1].set_xlabel('time')
    axes[1].set_ylabel('dL / L0')
    axes[1].grid(True)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.02))

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
        np.savetxt(fullPath, np.column_stack((curve['t'], curve['neck'], curve['shrinkage'])), delimiter=',', comments='', header="t,neck,shrinkage")

    print("The CSV files have been saved")