import sys
sys.path.append('/usr/lib/paraview')
sys.path.append('/usr/lib/paraview/site-packages')

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

def analyze_neck(inputFile, scalar, threshold):

    reader = ExodusIIReader(FileName=inputFile)

    #print(reader.PointVariables)
    object_methods = [method_name for method_name in dir(reader)
                    if callable(getattr(reader, method_name))]
    #print(object_methods)

    tsteps = reader.TimestepValues
    nst = len(tsteps)

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
    lineDia.UpdatePipeline()

    psz = measure_over_line(lineDia, scalar, threshold, domainLength)
    particleDiameter = round(psz/2, 0)

    print("Particle diameter = {}".format(particleDiameter))

    # Line for neck size
    lineStartX = (xMax + xMin) / 2
    lineStartY = yMin
    lineEndX = lineStartX
    lineEndY = yMax

    line = PlotOverLine(reader)
    line.Source.Point1 = [lineStartX, lineStartY, 0.0]
    line.Source.Point2 = [lineEndX, lineEndY, 0.0]
    line.UpdatePipeline()

    arNeck = []
    for timestep in tsteps:
        print("Measuring neck size for time = {}".format(timestep))

        line.UpdatePipeline(timestep)

        neckDiameter = measure_over_line(line, scalar, threshold, domainWidth)
        neckGrowth = neckDiameter / particleDiameter
        arNeck.append(neckGrowth)

    return tsteps, arNeck