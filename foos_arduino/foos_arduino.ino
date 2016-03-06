#include <TimerOne.h>

//check buttons every X ms
#define BTN_INTERVAL 10
//time to ignore GOAL interrupts after the first one has occurred (ms)
#define GOAL_DEBOUNCE_TIME 500
// Send Pings 'P' every X ms
#define PING_INTERVAL 5000

// Pin for goals (interrupt pins)
#define PIN_GOAL_YELLOW 2
#define PIN_GOAL_BLACK 3

#define TEST_LED_BLACK A0
#define TEST_LED_YELLOW A2

//input buttons, part on PORTD and one (OK) button on PORTB
#define BTN_MASK_D 0b11110000
#define BTN_MASK_B 0b00000001
//mask for all button data together
#define BTN_MASK   0b00011111

// btn events
char* btnEvents[5][2] = {{"YD_D", "YD_U"}, {"YI_D", "YI_U"}, {"BD_D", "BD_U"}, {"BI_D", "BI_U"}, {"OK_D", "OK_U"}};
#define GOAL_BLACK_STR "BG "
#define GOAL_YELLOW_STR "YG "

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

  // setup signal for IR Led
  Timer1.initialize(26);  // 26 us = 38 kHz
  // 50% DUTY CYCLE
  Timer1.pwm(9, 512);

  // setup serial
  Serial.begin(115200);

}

// goal event processing
bool goalsEnabled = false;
// enable goals a bit after startup to avoid false events
unsigned long reenableGoalsAt = 1000;


//button processing
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
    for (byte idx=0; idx < 5; idx++) {
      checkButton(changed, state, idx);
    }
  }
}

// process instructions from serial port
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
      //disable all leds
      PORTC=0;
      Serial.println("NORM_MODE");
    }
  }
}

inline bool processGoal(byte state, byte mask, unsigned long *counter, unsigned long *counterOff, char *goalString) {
  if ((state & mask) > 0) {
    (*counter)++;
    return true;
  } else {
    (*counterOff)++;
    if (*counter > 0) {
      Serial.print(goalString);
      Serial.print(*counter);
      Serial.print(" ");
      Serial.println(*counterOff);
      *counter = 0;
      *counterOff = 0;      
    }
    return false;
  }
}

unsigned long nextBtnCheck = 0;
unsigned long nextPing = 0;
unsigned long loops = 0;
unsigned long counterY = 0;
unsigned long counterB = 0;
unsigned long counterYOff = 0;
unsigned long counterBOff = 0;
unsigned long start = 0;
byte prev_goals = 0;
#define TIME_ELAPSED(now, ts) ((long)(now - ts) >= 0)
void loop() {
  if (testMode) {
    digitalWrite(TEST_LED_BLACK, digitalRead(PIN_GOAL_BLACK));
    digitalWrite(TEST_LED_YELLOW, digitalRead(PIN_GOAL_YELLOW));
  } else {
    bool processingGoal = 0;
    byte d = PIND;
    if (goalsEnabled) {
      processingGoal |= processGoal(d, 1 << PIN_GOAL_YELLOW, &counterY, &counterYOff, GOAL_YELLOW_STR);
      processingGoal |= processGoal(d, 1 << PIN_GOAL_BLACK, &counterB, &counterBOff, GOAL_BLACK_STR);
    }
    // don't process buttons or instructions during goal checking
    if (processingGoal) {
      return;
    }

    unsigned long now = millis();
    if (goalsEnabled == 0 && TIME_ELAPSED(now, reenableGoalsAt)) {
      goalsEnabled = 1;
      reenableGoalsAt = 0;
    }

    if (TIME_ELAPSED(now, nextBtnCheck)) {
      nextBtnCheck = now + BTN_INTERVAL;
      processButtons(PIND >> 4 | ((PINB & 0x01)<< 4));
    }
    if (TIME_ELAPSED(now, nextPing)) {
      nextPing = now + PING_INTERVAL;
      Serial.println("P");
    }
  }
  processInstructions();
}
