import glob
import sys
import tkinter as tk
from datetime import datetime, timezone, timedelta
import time
from tkinter import *

import serial

import Graph
from Config import Config, SettingsListener


class SerialManager(SettingsListener):
    ser: serial.Serial
    isOpen: bool = False
    serLabel: Label
    console: Text
    config: Config

    def __init__(self, config: Config, label: Label, console: Text):
        self.serLabel = label
        self.console = console
        self.connectSerial(config.get("serialport"))
        config.addListener("serialport", self)
        self.config = config

    def valueChanged(self, param, oldValue, newValue) -> None:
        print("SerialListener: " + param + " changed from " + oldValue + " to " + newValue)
        self.ser.close()
        self.connectSerial(newValue)

    def connectSerial(self, port: str):
        try:
            self.consoleInsert("Connecting to serial port: \'" + port + "\'", "yellow")
            self.ser = serial.Serial(port, 9600, timeout=1)
            print(self.ser.isOpen())
            self.isOpen = True
            self.consoleInsert("Connection successful", "green")
            self.serLabel.config(text="Serial Open", foreground="green")
        except (OSError, serial.SerialException):
            self.ser = serial.Serial()
            self.isOpen = False
            self.consoleInsert("Connection failed, is the serial port correct?", "red")
            self.serLabel.config(text="Serial Closed", foreground="red")

    def getSerial(self) -> serial.Serial:
        return self.ser

    def send(self, entry: Entry):
        if self.isOpen:
            text = entry.get()
            self.ser.write(text.encode("utf-8"))
            if text == "record":
                self.config.set("recordTime", time.perf_counter())
            entry.delete(0, END)
            self.consoleInsert("Sent: " + text, "green")
        else:
            self.consoleInsert("Serial port not open", "red")

    def sendText(self, text: str):
        if self.isOpen:
            self.ser.write(text.encode("utf-8"))
            self.consoleInsert("Sent: " + text, "green")
        else:
            self.consoleInsert("Serial port not open", "red")

    def sendStart(self, config: Config):
        if self.isOpen:
            time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            text = "command.start" + time
            config.set("startingTime", time)
            self.ser.write(text.encode("utf-8"))
            self.consoleInsert(text, "green")
            # self.consoleInsert(addSecs(datetime.strptime(config.get("startingTime"), '%Y-%m-%d %H:%M:%S'), 5).strftime('%Y-%m-%d %H:%M:%S'), "green")
        else:
            self.consoleInsert("Serial port not open", "red")

    def sendActuator(self, entry: Entry):
        entry.insert(0, "command.actuator")
        self.send(entry)

    def sendDelay(self, entry: Entry):
        entry.insert(0, "setdelay")
        self.send(entry)

    def sendRecord(self, entry: Entry):
        entry.insert(0, "record")
        self.config.set("recordTime", time.perf_counter())
        self.send(entry)


    def sendResend(self):
        if self.isOpen:
            self.ser.write("resend".encode("utf-8"))
            self.consoleInsert("Sent: resend", "green")
        else:
            self.consoleInsert("Serial port not open", "red")


    def consoleInsert(self, data: str, color: str = "white"):
        self.console.config(state=NORMAL)
        if len(data) > 6 and data[:6] == "sensor":
            sensorData = data[6:].split(",")
            for (i, val) in enumerate(sensorData):
                self.consoleInsert("RN07, " + str(round(time.perf_counter() - self.config.get("recordTime") - len(sensorData) * 5 + 5 * i)) + "s, " + str(round(float(val) * 0.1, 2)) + "kpa, " + str(round(((float(val) - 1002) * 0.01) + 0.87, 3)) + "m", "blue")
            Graph.createPressureGraph(data[6:].split(","), self.config.get("startingTime"), round(time.perf_counter() - self.config.get("recordTime") - len(sensorData) * 5))
        elif len(data) > 6 and data[:6] == "packet":
            self.consoleInsert(data[6:], "blue")
        if color == "white":
            self.console.insert(tk.END, data + "\n")
        else:
            self.console.insert(tk.END, data + "\n", color)
        self.console.config(state=DISABLED)
        self.console.see(END)

    def updateConsole(self, rate: int):
        if self.isOpen:
            num_bytes = self.ser.in_waiting
            if num_bytes > 0:
                data = self.ser.read(num_bytes).decode("utf-8")
                self.consoleInsert(data)

        self.console.after(rate, self.updateConsole, rate)


class Buttons:
    config: Config
    master: Tk
    ser: SerialManager
    buttonFrame: Frame

    def __init__(self, master: Tk):
        self.config = Config()
        self.config.readConfig()
        self.master = master

        master.winfo_toplevel().title("Float Controller")
        master.protocol("WM_DELETE_WINDOW", self.onClose)
        master.geometry(str(self.config.get("windowwidth")) + "x" + str(self.config.get("windowheight")))

        topFrame = Frame(master)
        buttonFrame = Frame(master)
        self.buttonFrame = buttonFrame
        consoleFrame = Frame(master)
        inputFrame = Frame(master)

        topFrame.pack(side=TOP, fill=X)
        buttonFrame.pack(side=TOP, fill=X)
        inputFrame.pack(side=BOTTOM, fill=X)
        consoleFrame.pack(side=BOTTOM, fill=BOTH, expand=True)

        self.console = Text(consoleFrame, width=80, height=15)
        self.sb = Scrollbar(consoleFrame, orient=VERTICAL, command=self.console.yview)
        self.console.configure(yscrollcommand=self.sb.set, background="#BEBEBE")
        self.console.config(state=DISABLED)

        self.sb.pack(side=RIGHT, fill=Y)
        self.console.pack(side=LEFT, fill=BOTH, expand=True)

        self.console.tag_configure("red", foreground="red")
        self.console.tag_configure("green", foreground="green")
        self.console.tag_configure("yellow", foreground="yellow")
        self.console.tag_configure("blue", foreground="blue")

        serLabel = Label(buttonFrame, text="Serial Closed", foreground="red")
        self.ser = SerialManager(self.config, serLabel, self.console)
        serReconnect = Button(buttonFrame, text="Reconnect", command=lambda: self.ser.connectSerial(self.config.get("serialport")), width=10)

        self.console.after_idle(self.ser.updateConsole, 1000)

        serReconnect.pack(side=RIGHT, padx=5, pady=5)
        serLabel.pack(side=RIGHT, padx=5, pady=5)

        self.config.serPort.trace_add("write", callback=lambda *args: self.config.set("serialport", self.config.serPort.get()))

        refreshPorts = Button(buttonFrame, text="Refresh Ports", command=self.refreshPorts, width=10)
        refreshPorts.pack(side=LEFT, padx=5, pady=5)

        self.serPorts = None
        self.refreshPorts()

        self.input = Entry(inputFrame, width=80)
        self.input.pack(side=LEFT, padx=5, pady=5)
        self.input.bind("<Return>", lambda event: self.ser.send(self.input))
        self.input.focus_set()

        inputSend = Button(inputFrame, text="Send", command=lambda: self.ser.send(self.input), width=10)
        inputSend.pack(side=LEFT, padx=5, pady=5)

        btn = Button(topFrame, text="Test Graph", command=self.consoleTest, width=10)
        btn.pack(side=LEFT, padx=5, pady=5)

        startBtn = Button(topFrame, text="Start Float", command=lambda: self.ser.sendStart(self.config), width=10)
        startBtn.pack(side=LEFT, padx=5, pady=5)

        actuatorBtn = Button(topFrame, text="Move Actuator(%):", command=lambda: self.ser.sendActuator(self.actuatorInput), width=15)
        actuatorBtn.pack(side=LEFT, padx=5, pady=5)
        self.actuatorInput = Entry(topFrame, width=5)
        self.actuatorInput.pack(side=LEFT, padx=5, pady=5)

        delayBtn = Button(topFrame, text="Set Delay(ms):", command=lambda: self.ser.sendDelay(self.delayInput), width=10)
        delayBtn.pack(side=LEFT, padx=5, pady=5)
        self.delayInput = Entry(topFrame, width=5)
        self.delayInput.pack(side=LEFT, padx=5, pady=5)

        resendBtn = Button(topFrame, text="Resend Data", command=lambda: self.ser.sendResend()  , width=10)
        resendBtn.pack(side=LEFT, padx=5, pady=5)

        pingBtn = Button(topFrame, text="Send Ping", command=lambda: self.ser.sendText("ping"), width=10)
        pingBtn.pack(side=RIGHT, padx=5, pady=5)

    def consoleTest(self):
        self.config.set("startingTime", datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
        self.ser.consoleInsert("sensor100,200,300,400,500,600,700,800,900,1000")
        # for i in range(20):
        #     self.master.update()
        #     self.master.after(100, self.ser.consoleInsert("Test " + str(i)))
        #     self.console.see(END)

    def onClose(self):
        self.master.destroy()
        self.config.writeConfig()

    def refreshPorts(self):
        new_ports = serial_ports(self.config)
        if self.config.serPort.get() not in new_ports:
            self.config.serPort.set("")
        else:
            new_ports.remove(self.config.serPort.get())
        self.ports = new_ports
        if self.serPorts is not None:
            self.serPorts.destroy()
        self.serPorts = OptionMenu(self.buttonFrame, self.config.serPort, self.config.serPort.get(), *self.ports)
        self.serPorts.pack(side=LEFT, padx=5, pady=5)


def serial_ports(config: Config):
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            if port != config.get("serialport"):
                s = serial.Serial(port)
                s.close()
                result.append(port)
            else:
                result.append(port)
        except (OSError, serial.SerialException):
            pass
    result.sort()
    return result


window = tk.Tk()
b = Buttons(window)
window.mainloop()
