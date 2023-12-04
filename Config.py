import json
from abc import ABC, abstractmethod
from tkinter import StringVar
from typing import List


class SettingsListener(ABC):
    @abstractmethod
    def valueChanged(self, param, oldValue, newValue) -> None:
        pass


class Config:
    _settings = {
        "windowwidth": 800,
        "windowheight": 600,
        "serialport": ""
    }

    _listeners = {}

    serPort: StringVar

    def __init__(self):
        pass

    def addListener(self, param, listener: SettingsListener):
        if param not in self._listeners:
            inner_list: List[SettingsListener] = []
            self._listeners[param] = inner_list
        else:
            inner_list = self._listeners[param]

        inner_list.append(listener)

    def removeListener(self, param, listener: SettingsListener):
        if param in self._listeners:
            self._listeners[param].remove(listener)

    def get(self, param):
        return self._settings[param]

    def set(self, param, value):
        if param in self._settings:
            old_value = self._settings[param]
            if value != old_value:
                self._settings[param] = value
                if param in self._listeners:
                    for listener in self._listeners[param]:
                        listener.valueChanged(param, old_value, value)
        else:
            raise Exception("Unknown parameter: " + param)

    def writeConfig(self):
        with open("config.json", "w") as file:
            json.dump(self._settings, file, indent=4, sort_keys=True)

    def readConfig(self):
        try:
            with open("config.json", "r") as file:
                self._settings.update(json.load(file))
        except FileNotFoundError:
            self.writeConfig()
            print("Created config.json")
        self.serPort = StringVar()
        self.serPort.set(self._settings["serialport"])

    def getSerialPort(self) -> StringVar:
        return self.serPort
            