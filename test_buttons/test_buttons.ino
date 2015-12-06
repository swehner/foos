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

#define BTN_MASK_B 0b00011101
#define BTN_MASK_D 0b10000000


char* btnEvents[5][2] = {{"BD_D", "BD_U"}, {"BI_D", "BI_U"}, {"YD_D", "YD_U"}, {"YI_D", "YI_U"}, {"OK_D", "OK_U"}};

void setup() {
  //analog pins - button leds
  DDRC = 0xFF;
  PORTC = 0;

  //8-12 button inputs, except 9 (PWM) and 13 because it has a led 
  DDRB = 0b00100010;
  //enable pullups, except pin 9
  PORTB |= BTN_MASK_B;
  pinMode(7, INPUT_PULLUP);
  Serial.begin(115200);

  //set pin 2,3 to input
  pinMode(PIN_GOAL_BLACK, INPUT);
  pinMode(PIN_GOAL_YELLOW, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_GOAL_BLACK), goalBlack, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_GOAL_YELLOW), goalYellow, RISING);

  // setup signal for IR Led
  Timer1.initialize(26);  // 26 us = 38 kHz
  Timer1.pwm(9, 512);
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

inline void checkButton(byte changed, byte state, byte bit, byte idx) {
  if (changed & _BV(bit)) {
    Serial.println(btnEvents[idx][((state & _BV(bit)) != 0)]);
  }
}

// check for pressed buttons
byte prevBtnsB = BTN_MASK_B;
byte prevBtnsD = BTN_MASK_D;
void processButtons(byte stateB, byte stateD) {
  byte changedB = prevBtnsB ^ (stateB & BTN_MASK_B);
  byte changedD = prevBtnsD ^ (stateD & BTN_MASK_D);

  if (changedB) {
    // save new state
    prevBtnsB = stateB;
    // check which button has changed
    checkButton(changedB, stateB, 0, 0);
    checkButton(changedB, stateB, 2, 1);
    checkButton(changedB, stateB, 3, 2);
    checkButton(changedB, stateB, 4, 3);
  }
  if (changedD) {
    // save new state
    prevBtnsD = stateD;
    // check which button has changed
    checkButton(changedD, stateD, 7, 4);
  }
}

byte testMode = 0;
// read from serial port and set led status
void processInstructions() {
  if (Serial.available()) {
    int data = Serial.read();
    // from A -> a 5 bits for LEDS
    if (data >= 'A' && data <= ('A' + 32)) {
      // take printables ASCII character and shift down
      data = (data & 0xFF) - 'A';
      PORTC = data;
    } else  if (data == 't') {
      testMode = 1;
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
      processButtons(PINB, PIND);
    }
    if ((long)(now - nextPing) >= 0) {
      nextPing = now + PING_INTERVAL;
      Serial.println("P");
    }
  }
}
