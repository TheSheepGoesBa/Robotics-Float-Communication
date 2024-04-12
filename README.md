# Robotics-Float-Communication



### Pre-requisites:
* [Python](https://www.python.org/downloads/)

### Setup:
To get to the project's directory(the folder that you installed the code into), run the following in terminal/command prompt:
```bash
cd [path to the folder]
```

Then, run the following command to install the required packages:
```bash
pip install -r requirements.txt
```

### Run:
In the directory of the project, run the following command in terminal/command prompt:\
```python FloatUI.py```


### Usage:
* Select the COM port of the XBee from the drop-down list.
    * If the COM port is not listed, click on the ```Refresh``` button to refresh the list.
    * If the COM port is still not listed, make sure the XBee is connected to the computer.
* Click on the ```Connect``` button to establish a connection with the XBee.
    * If the connection is successful, there will be green text displaying ```Serial Open```.
    * If the connection is unsuccessful, an error message will be displayed in the console.
* Clicking the ```Start``` button will start the float, the actuator will move
all the way out and then back in. The sensor will print an array of its values in the console.
    * Do not click the ```Start``` button until the sensor values are returned, as it will cause the float to start again after it's finished.
* Clicking the ```Move Actuator(%)``` button will move the actuator to the specified percentage from the text box on the right of the button.
* Clicking the button in the top right named ```Send Ping``` will send a ping to the float and the float will respond with a pong if it's still connected.


