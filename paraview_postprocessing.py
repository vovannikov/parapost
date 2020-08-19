import sys
import os
import csv

from settings import paraviewLib
sys.path.append(paraviewLib)
sys.path.append(os.path.join(paraviewLib, 'site-packages'))

from paraview.simple import *
import paraview.vtk as vtk

# Measure certain value along the line
def measure_over_line(pline, scalar, threshold, length):
    nbp = pline.GetDataInformation().GetNumberOfPoints()
    sizeStep = length/nbp

    activePointsCount = 0

    fullData = servermanager.Fetch(pline)
    #vals = pdi.GetPointDataInformation().GetArrayInformation("c")
    vals = fullData.GetPointData().GetScalars(scalar)

    for jpoint in range(0, nbp):
        aValue = vals.GetValue(jpoint)
        if (aValue > threshold):
            activePointsCount += 1

    magnitude = sizeStep * activePointsCount
    
    return magnitude

def open_exodus(inputFile):

    reader = ExodusIIReader(FileName=inputFile)

    #print(reader.PointVariables)
    object_methods = [method_name for method_name in dir(reader)
                    if callable(getattr(reader, method_name))]
    #print(object_methods)

    return reader

def domain_dimensions(reader, scalar, threshold, resolution):

    bounds = reader.GetDataInformation().GetBounds()
    xMin = bounds[0]
    xMax = bounds[1]
    yMin = bounds[2]
    yMax = bounds[3]

    domainWidth = yMax-yMin
    domainLength = xMax-xMin

    print("Domain size = {} x {}".format(domainLength, domainWidth))

    # Determine the particle diameter
    lineStartX = xMin
    lineStartY = (yMax + yMin) / 2
    lineEndX = xMax
    lineEndY = (yMax + yMin) / 2

    lineDia = PlotOverLine(reader)
    lineDia.Source.Point1 = [lineStartX, lineStartY, 0.0]
    lineDia.Source.Point2 = [lineEndX, lineEndY, 0.0]
    lineDia.Source.Resolution = resolution
    lineDia.UpdatePipeline()

    psz = measure_over_line(lineDia, scalar, threshold, domainLength)
    particleDiameter = round(psz/2, 0)

    szMin = measure_over_line(lineDia, scalar, 0.998, domainLength)
    szMax = measure_over_line(lineDia, scalar, 0.001, domainLength)
    gbWidth = (szMax - szMin) / 4.

    print("Particle diameter = {}".format(particleDiameter))
    print("GB width = {}".format(gbWidth))

    return particleDiameter, gbWidth

def diameter_from_pf(fname):

    with open(fname, 'r') as theFile:
        reader = csv.DictReader(theFile)

        for line in reader:

            time = float(line['time'])
            
            if "centroids_distance" in line:
                if time > 1e-11:
                    diameter = float(line['centroids_distance'])
                    break

            else:
                diameter = 0
                break
            
    return diameter

def field_from_pf(fname, field):

    timeList = []
    fieldList = []

    with open(fname, 'r') as theFile:
        reader = csv.DictReader(theFile)
        
        for line in reader:

            time = float(line['time'])
            if field in line:
                value = float(line[field])
            else:
                value = 0
            
            timeList.append(time)
            fieldList.append(value)
            
    return timeList, fieldList

def neck_from_vtk(reader, particleDiameter, scalar, threshold, resolution):

    tsteps = reader.TimestepValues

    bounds = reader.GetDataInformation().GetBounds()
    xMin = bounds[0]
    xMax = bounds[1]
    yMin = bounds[2]
    yMax = bounds[3]

    domainWidth = yMax-yMin

    # Line for neck size
    lineStartX = (xMax + xMin) / 2
    lineStartY = yMin
    lineEndX = lineStartX
    lineEndY = yMax

    line = PlotOverLine(reader)
    line.Source.Point1 = [lineStartX, lineStartY, 0.0]
    line.Source.Point2 = [lineEndX, lineEndY, 0.0]
    line.Source.Resolution = resolution
    line.UpdatePipeline()

    arNeck = []
    for timestep in tsteps:
        print("Measuring neck size for time = {}".format(timestep))

        line.UpdatePipeline(timestep)

        neckDiameter = measure_over_line(line, scalar, threshold, domainWidth)
        neckGrowth = neckDiameter / particleDiameter
        arNeck.append(neckGrowth)

    return tsteps, arNeck

def shrinkage_from_vtk(reader, particleDiameter, scalar, threshold, resolution):

    tsteps = reader.TimestepValues

    bounds = reader.GetDataInformation().GetBounds()
    xMin = bounds[0]
    xMax = bounds[1]
    yMin = bounds[2]
    yMax = bounds[3]

    domainLength = xMax-xMin

    # Line for shrinkage
    lineStartX = xMin
    lineStartY = (yMax + yMin) / 2
    lineEndX = xMax
    lineEndY = (yMax + yMin) / 2

    lineDia = PlotOverLine(reader)
    lineDia.Source.Point1 = [lineStartX, lineStartY, 0.0]
    lineDia.Source.Point2 = [lineEndX, lineEndY, 0.0]
    lineDia.Source.Resolution = resolution
    lineDia.UpdatePipeline()

    L0 = 2*particleDiameter
    arShrinkage = []
    for timestep in tsteps:
        print("Measuring shrinkage for time = {}".format(timestep))

        lineDia.UpdatePipeline(timestep)

        L = measure_over_line(lineDia, scalar, threshold, domainLength)
        dL = L0 - L
        if dL > 0:
            shrinkage = dL / L0
        else:
            shrinkage = arShrinkage[-1] if len(arShrinkage) > 0 else 0

        arShrinkage.append(shrinkage)

    return tsteps, arShrinkage

def neck_from_pf_area(fname, diameter, width):

    timeList, neckAreaList = field_from_pf(fname, 'neck')
    neckGrowthList = [neckArea / width / diameter for neckArea in neckAreaList]

    return timeList, neckGrowthList

def neck_from_pf(fname, diameter):

    timeList, neckWidthList = field_from_pf(fname, 'neck_width')
    neckGrowthList = [neckWidth / diameter for neckWidth in neckWidthList]

    return timeList, neckGrowthList

def shrinkage_from_pf(fname, diameter):

    timeList = []
    shrinkageList = []

    # first defined L0
    L0 = -1

    with open(fname, 'r') as theFile:
        reader = csv.DictReader(theFile)

        for line in reader:            
            if "shrinkage" in line:
                L = float(line["shrinkage"])

                if (L0 < 0 and L > 1.0) or L0 < L:
                    L0 = L

    with open(fname, 'r') as theFile:
        reader = csv.DictReader(theFile)

        for line in reader:

            time = float(line['time'])
            
            if "shrinkage" in line:
                L = float(line["shrinkage"])

                if L > 0 and  L0 > 0 and L0 > L:
                    dL = L0 - L
                    shrinkage = dL / L0
                else:
                    shrinkage = 0

                print("L0 = {}, L = {}, shr = {}".format(L0, L, shrinkage))
            else:
                shrinkage = 0
            
            timeList.append(time)

            if len(shrinkageList) and shrinkageList[-1] > 0 and shrinkage == 0:
                shrinkageList[-1] = 0

            shrinkageList.append(shrinkage)
            
    return timeList, shrinkageList

def shrinkage_from_pf_OLD(fname, diameter):

    timeList = []
    shrinkageList = []

    with open(fname, 'r') as theFile:
        reader = csv.DictReader(theFile)
        
        L0 = diameter

        for line in reader:

            time = float(line['time'])
            
            if "centroids_distance" in line:
                L = float(line["centroids_distance"])

                if time < 1e-11:
                    L = L0

                dL = L0 - L
                shrinkage = dL / L0
            else:
                shrinkage = 0
            
            timeList.append(time)
            shrinkageList.append(shrinkage)
            
    return timeList, shrinkageList

def detect_file(inputFolder, ext):
    fNames = [fn for fn in os.listdir(inputFolder) if fn.endswith(ext)]
    fCount = len(fNames)

    if (fCount == 0):
        print("ERROR: unable to detect '" + ext + "' file for this case, check input folder")
        return None

    fileName = fNames[0]
    if (fCount > 1):
        print("NOTICE: several '" + ext + "' files found, the first is used: " + fileName)

    return os.path.join(inputFolder, fileName)
