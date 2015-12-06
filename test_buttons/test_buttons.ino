#include <TimerOne.h>

//check buttons every X ms
#define BTN_INTERVAL 10
#define GOAL_DEBOUNCE_TIME 500
#define PING_INTERVAL 5000

#define PIN_GOAL_BLACK 2
#define PIN_GOAL_YELLOW 3
#define GOAL_BLACK_STR "BG"
#define GOAL_YELLOW_STR "YG"

#define TEST_LED_BLACK A0
#define TEST_LED_YELLOW A2

#define BTN_MASK_D 0b11110000
#define BTN_MASK_B 0b00000001
#define BTN_MASK   0b00011111

// btn events
char* btnEvents[5][2] = {{"BD_D", "BD_U"}, {"BI_D", "BI_U"}, {"YD_D", "YD_U"}, {"YI_D", "YI_U"}, {"OK_D", "OK_U"}};

void setup() {
  //analog pins for button leds as output
  DDRC = 0xFF;
  PORTC = 0;

  //Pin 8 button input 
  pinMode(8, INPUT_PULLUP);
  // 4,5,6,7 input and pullup
  DDRD &= !BTN_MASK_D;
  PORTD |= BTN_MASK_D;

  //set pin 2,3 to input
  pinMode(PIN_GOAL_BLACK, INPUT);
  pinMode(PIN_GOAL_YELLOW, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_GOAL_BLACK), goalBlack, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_GOAL_YELLOW), goalYellow, RISING);

  // setup signal for IR Led
  Timer1.initialize(26);  // 26 us = 38 kHz
  Timer1.pwm(9, 512);

  // setup serial
  Serial.begin(115200);
}

byte goalsEnabled = 1;
unsigned long reenableGoalsAt = 0;
inline void goal(char* str) {
  if (goalsEnabled) {
    Serial.println(str);
    goalsEnabled = 0;
    reenableGoalsAt = millis() + GOAL_DEBOUNCE_TIME;
  }
}

void goalBlack() {
  goal(GOAL_BLACK_STR);
}

void goalYellow() {
  goal(GOAL_YELLOW_STR);
}

inline void checkButton(byte changed, byte state, byte idx) {
  if (changed & _BV(idx)) {
    Serial.println(btnEvents[idx][((state & _BV(idx)) != 0)]);
  }
}

// check for pressed buttons
byte prevBtns = BTN_MASK;
void processButtons(byte state) {
  byte changed = prevBtns ^ (state & BTN_MASK);

  if (changed) {
    // save new state
    prevBtns = state;
    // check which button has changed
    for (byte idx=0; idx < 5; idx++)
      checkButton(changed, state, idx);
    }
}

byte testMode = 0;
// read from serial port and set led status
void processInstructions() {
  if (Serial.available()) {
    int data = Serial.read();
    // from A -> '`' inclusive 5 bits for LEDS
    if (data >= 'A' && data <= ('A' + 32)) {
      // take printables ASCII character and shift down
      data = (data & 0xFF) - 'A';
      PORTC = data;
    } else  if (data == 't') {
      testMode = 1;
      //disable all leds
      PORTC=0;
      Serial.println("TEST_MODE");
    } else if (data == 'u') {
      testMode = 0;
      Serial.println("NORM_MODE");
    }
  }
}

unsigned long nextBtnCheck = 0;
unsigned long soonestNextGoalCheck = 0;
unsigned long nextPing = 0;
void loop() {
  processInstructions();
  if (testMode) {
    digitalWrite(TEST_LED_BLACK, digitalRead(PIN_GOAL_BLACK));
    digitalWrite(TEST_LED_YELLOW, digitalRead(PIN_GOAL_YELLOW));
  } else {
    unsigned long now = millis();
    if (goalsEnabled == 0 && ((long)(now - reenableGoalsAt) >= 0)) {
      goalsEnabled = 1;
      reenableGoalsAt = 0;
    }
    if ((long)(now - nextBtnCheck) >= 0) {
      nextBtnCheck = now + BTN_INTERVAL;
      processButtons(PIND >> 4 | ((PINB & 0x01)<< 4));
    }
    if ((long)(now - nextPing) >= 0) {
      nextPing = now + PING_INTERVAL;
      Serial.println("P");
    }
  }
}
