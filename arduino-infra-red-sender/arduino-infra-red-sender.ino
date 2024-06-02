#include <vector>
#include <map>
#include <string>
#include <Arduino.h>

// ........................................................ //
//  BASED ON CODE FROM LIBRARY EXAMPLES from: 
//  https://www.arduino.cc/reference/en/libraries/irremote/ //
// ........................................................ //

// pull in IR library and activate pin 3
#define IR_SEND_PIN 3
#include "TinyIRSender.hpp"

// prepare to use C++
using namespace std;

// setup pins
int pin_upButton = 18;    // d18
int pin_stopButton = 14;  // d14
int pin_downButton = 20;  // d14

// setup buttons
vector<int> buttonPins = { pin_upButton, pin_stopButton, pin_downButton };
std::map<int, string> buttonNames = {
  { pin_upButton, "up button" },
  { pin_stopButton, "stop button" },
  { pin_downButton, "down button" }
};

// value when button is being pressed
const int beingPressed = 0;

// setup infra red remote codes
uint8_t upCommand = 0x32;    // decimal 50
uint8_t stopCommand = 0x28;  // decimal 40
uint8_t downCommand = 0x1E;  // decimal 30

std::map<int, uint8_t> buttonCommands = {
  { pin_upButton, upCommand },
  { pin_stopButton, stopCommand },
  { pin_downButton, downCommand }
};

// identify this remote as "210"
uint8_t remoteIdentifier = 0xD2;  // 210
uint8_t numberOfTimesToSendSignal = 1;

// prepare pins
void setup() {
  Serial.begin(115200);

  // use internal pull up resistors to keep signal steady
  for (unsigned int i = 0; i < buttonPins.size(); i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
}

void loop() {
  // helper for serial monitor
  bool openerPrinted = false;
  
  // prepare to send IR signal
  for (unsigned int buttonIndex = 0; buttonIndex < buttonPins.size(); buttonIndex++) {
    int pin = buttonPins[buttonIndex];
    int buttonStatus = digitalRead(pin);

    // check if a button is being pressed
    if (buttonStatus == beingPressed) {

      // print button action
      if (!openerPrinted) {
        Serial.println("------");
        openerPrinted = true;
      }
      const char* buttonName = buttonNames[pin].c_str();
      Serial.println(String(buttonName) + ": " + String(buttonStatus));

      // print infra red setup
      Serial.println("Send NEC with 8 bit address and command: " + String(buttonCommands[pin]));

      // send IR signal in NEC format
      Serial.flush();
      sendNEC(IR_SEND_PIN, remoteIdentifier, buttonCommands[pin], numberOfTimesToSendSignal);
    }
  }

  // prepare for next loop's serial
  if (openerPrinted) {
    Serial.println("");
  }
}
