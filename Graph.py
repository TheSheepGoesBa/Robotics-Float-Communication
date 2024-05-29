from datetime import datetime, timedelta

import matplotlib.pyplot as plt

def createPressureGraph(sensorData, startTime, floatTime):
    sensorData = [-6, -6, -6, -6, -6, -87, -175, -268, -351, -396, -396, -317, -248, -178, -98, -32, -6, -6, -6, -6, -6]
    times = [str(5 * i) for i in range(len(sensorData))]
    # newData = [((float(data)-1001) * 0.01) + 0.87 for data in sensorData]
    newData = sensorData

    # Create a list of times
    # Data for plotting

    fig, ax = plt.subplots()
    ax.plot(newData)
    ax.ticklabel_format(useOffset=False)
    plt.xticks(range(len(newData)), times)

    ax.set(xlabel='Float Time (s)', ylabel='Depth (cm)',
        title='Depth over time (' + ')')
    ax.grid()
    plt.show()

def addSecs(date: datetime, secs: float):
    date = date + timedelta(seconds=secs)
    return date