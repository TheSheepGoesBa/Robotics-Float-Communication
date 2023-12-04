import glob
import sys
import tkinter as tk
from tkinter import *

import serial

from Config import Config, SettingsListener


class SerialManager(SettingsListener):
    ser: serial.Serial
    isOpen: bool = False
    serLabel: Label
    console: Text

    def __init__(self, config: Config, label: Label, console: Text):
        self.serLabel = label
        self.console = console
        self.connectSerial(config.get("serialport"))
        config.addListener("serialport", self)

    def valueChanged(self, param, oldValue, newValue) -> None:
        print("SerialListener: " + param + " changed from " + oldValue + " to " + newValue)
        self.ser.close()
        self.connectSerial(newValue)

    def connectSerial(self, port: str):
        try:
            self.consoleInsert("Connecting to serial port: \'" + port + "\'", "yellow")
            self.ser = serial.Serial(port, 9600, timeout=1)
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
            entry.delete(0, END)
            self.consoleInsert("Sent: " + text, "green")
        else:
            self.consoleInsert("Serial port not open", "red")

    def consoleInsert(self, data: str, color: str = "white"):
        self.console.config(state=NORMAL)
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

        serLabel = Label(buttonFrame, text="Serial Closed", foreground="red")
        self.ser = SerialManager(self.config, serLabel, self.console)
        serReconnect = Button(buttonFrame, text="Reconnect", command=lambda: self.ser.connectSerial(self.config.get("serialport")), width=10)

        self.console.after_idle(self.ser.updateConsole, 500)

        serReconnect.pack(side=RIGHT, padx=5, pady=5)
        serLabel.pack(side=RIGHT, padx=5, pady=5)

        self.config.serPort.trace_add("write", callback=lambda *args: self.config.set("serialport", self.config.serPort.get()))

        refreshPorts = Button(buttonFrame, text="Refresh Ports", command=self.refreshPorts, width=10)
        refreshPorts.pack(side=LEFT, padx=5, pady=5)

        self.ports = serial_ports(self.config)
        self.serPorts = OptionMenu(buttonFrame, self.config.serPort, self.config.serPort.get(), *self.ports)
        self.serPorts.pack(side=LEFT, padx=5, pady=5)

        self.input = Entry(inputFrame, width=80)
        self.input.pack(side=LEFT, padx=5, pady=5)
        self.input.bind("<Return>", lambda event: self.ser.send(self.input))
        self.input.focus_set()

        self.inputSend = Button(inputFrame, text="Send", command=lambda: self.ser.send(self.input), width=10)
        self.inputSend.pack(side=LEFT, padx=5, pady=5)

        self.btn = Button(topFrame, text="Test Console", command=self.consoleTest, width=10)
        self.btn.pack(side=LEFT, padx=5, pady=5)

    def consoleTest(self):
        for i in range(20):
            self.master.update()
            self.master.after(100, self.ser.consoleInsert("Test " + str(i)))
            self.console.see(END)

    def onClose(self):
        self.master.destroy()
        self.config.writeConfig()

    def refreshPorts(self):
        new_ports = serial_ports(self.config)
        if self.config.serPort.get() not in new_ports:
            self.config.serPort.set("")
        self.ports = new_ports
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
    # TODO test this
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
    return result


window = tk.Tk()
b = Buttons(window)
window.mainloop()
