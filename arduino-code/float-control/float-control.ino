#include <SoftwareSerial.h>
#include <Servo.h>
#include <Wire.h>
#include "MS5837.h"

MS5837 sensor;
float Btemperature;
float pressure;

Servo myservo;
#define servoPin 11

#define rxPin A0
#define txPin A1

int current = 0;
float dataArr[50] = {};
String dataString = "";

int actuatorDelay = 250;

long recordTime;

// Set up a new SoftwareSerial object
SoftwareSerial XBee(rxPin, txPin);

void getPressure() {
  sensor.setModel(MS5837::MS5837_02BA);
  if (!sensor.init()) {
    Serial.println("bad pressure Sensor");
  }
  sensor.read();
  pressure = sensor.pressure();
  Btemperature = sensor.temperature();

}

void printPressure() {
  Serial.print("Pressure: ");
  Serial.print(pressure / 10.0, 3);
  Serial.println(" mbar");

  Serial.print("Temperature: ");
  Serial.print(Btemperature);
  Serial.println(" deg C");

  Serial.println("");
}

void setPercentage(float strokePercentage){
  if ( strokePercentage >= 1.0 && strokePercentage <= 99.0 ) {
    int usec = 1000 + strokePercentage * ( 2000 - 1000 ) / 100.0 ;
    myservo.writeMicroseconds(usec);
  }
}


void startFloat() {
  int dataIndex = 1;
  long lastData = millis();
  memset(dataArr, 0, sizeof(dataArr));
  dataString = "";
  Serial.println("Getting Pressure");
  Serial.println("Done");
  
  dataArr[0] = pressure;


  // section  ACTUATOR
  digitalWrite(13, HIGH);
  // i < 1000
  for (int i = 99; i >= 1; i--) {
    if (millis() - lastData > 5000) {
      lastData = millis();
      getPressure();
      dataArr[dataIndex] = pressure;
      dataIndex++;
    }
    setPercentage(i);
    delay(actuatorDelay);
  }

  digitalWrite(13, LOW);
  // i = 1000
  for (int i = 1; i <= 99; i++) {
    if (millis() - lastData > 5000) {
      lastData = millis();
      getPressure();
      dataArr[dataIndex] = pressure;
      dataIndex++;
      Serial.println(pressure);
    }

    setPercentage(i);
    delay(actuatorDelay);
  }

  // end  ACTUATOR

  for (int j = 0; j < dataIndex; j++) {
    dataString += String(dataArr[j]);
    if (j < dataIndex - 1) {
      dataString += ",";
    }
  }
  
  dataString = "sensor" + dataString;
  sendConfirmData();
}

void sendConfirmData() {
  XBee.print(dataString.c_str());
  Serial.println("Sent: " + dataString);
}

void setup()  {
  // Define pin modes for TX and RX
//    pinMode(rxPin, INPUT);
//    pinMode(txPin, OUTPUT);
  myservo.attach(servoPin);
  pinMode(13, OUTPUT);

  // Set the baud rate for the SoftwareSerial object
  XBee.begin(9600);
  Serial.begin(9600);
  Serial.println("Company Name\n\n");


  pinMode(5, OUTPUT);
  digitalWrite(5, HIGH);

  Serial.println("Starting Sensor");

  Wire.begin();

  sensor.setModel(MS5837::MS5837_02BA);
  //sensor.setFluidDensity(1029);  // kg/m^3 (997 freshwater, 1029 for seawater)
  sensor.setFluidDensity(997);  // kg/m^3 (997 freshwater, 1029 for seawater) 1204 for air
  sensor.init();

  setPercentage(99);
}

void loop() {
  if (Serial.available()) { // If data comes in from serial monitor, send it out to XBee
    XBee.write(Serial.read());
  }

  if (XBee.available()) { // If data comes in from XBee, send it out to serial monitor
    String data = XBee.readString();
    Serial.println("Recieved: [" + data + "]");
    if (data.length() >= 4 && data.substring(0, 4).equals("ping")) {
      getPressure();
      String text = "packetRN07, " + String((int)((millis() - recordTime)/1000.0)) + "s, " + String(pressure * 0.1) + "kpa, " + String(((pressure-1002) * 0.01) + 0.87) + "m";
      XBee.print(text.c_str());
    } else if (data.length() >= 13 && data.substring(0, 13).equals("command.start")) {
      String text = "Starting Float, UTC Time: " + data.substring(13);
      XBee.print(text.c_str());
      Serial.println(text);
      Serial.println("UTC Time: " + data.substring(13));
      startFloat();
    } else if (data.length() >= 16 && data.substring(0, 16).equals("command.actuator")) {
      String percentage = data.substring(16);
      String text = "Moving actuator to: " + percentage;
      Serial.println(text);
      XBee.print(text.c_str());
      setPercentage(percentage.toFloat());
    } else if (data.length() >= 8 && data.substring(0, 8).equals("setdelay")) {
      String textDelay = data.substring(8);
      String text = "Setting delay to: " + textDelay + "ms";
      Serial.println(text);
      XBee.print(text.c_str());
      actuatorDelay = textDelay.toInt();
    } else if (data.length() >= 6 && data.substring(0, 6).equals("resend")) {
      sendConfirmData();
    } else if (data.length() >= 6 && data.substring(0, 6).equals("record")) {
      recordTime = millis();
      String text = "Started Recording Time";
      XBee.print(text.c_str());
    }
  }
}
