#include <TimerOne.h>
#include <stdio.h>

// Modified to work with Adafruit's breakbeam sensors. No longer need the PWM and 9 pin.  
// Hook up led directly to power/ground. and for sensors, connect yellow/white data wire to 10/11.

//check buttons every X ms
#define BTN_INTERVAL 10
// Send Pings 'P' every X ms
#define PING_INTERVAL 5000

#define TEST_LED_BLACK A0
#define TEST_LED_YELLOW A2

const char* btnEvents[5][2] = {{"YD_U", "YD_D"}, {"YI_U", "YI_D"}, {"BD_U", "BD_D"}, {"BI_U", "BI_D"}, {"OK_U", "OK_D"}};
#define GOAL_BLACK_STR "BG %lu %lu"
#define GOAL_YELLOW_STR "YG %lu %lu"

#define PIN_GOAL_YELLOW 10
#define PIN_MASK_YELLOW 0b00000001
#define PIN_GOAL_BLACK 11
#define PIN_MASK_BLACK 0b00000010

//input button mask (2-6) - CANNOT use PORTD on Micro
#define BTN_MASK   0b00011111
// On micro A0 = D 18
#define D_BTN_A0   18
// 2= YD, 3=YI, 4=BD, 5=BI, 6=OK
#define D2 2
#define D3 3
#define D4 4
#define D5 5
#define D6 6
#define D7 7
#define D8 8

void setup() {
	// set analog leds as output
	pinMode(A0, OUTPUT);
	pinMode(A1, OUTPUT);
	pinMode(A2, OUTPUT);
	pinMode(A3, OUTPUT);
	pinMode(A4, OUTPUT);
  // set button modes as input
  pinMode(D4, INPUT_PULLUP);
  pinMode(D5, INPUT_PULLUP);
  pinMode(D6, INPUT_PULLUP);
  pinMode(D7, INPUT_PULLUP);
  pinMode(D8, INPUT_PULLUP);

  //set pin for goals as input
  pinMode(PIN_GOAL_BLACK, INPUT_PULLUP);
  pinMode(PIN_GOAL_YELLOW, INPUT_PULLUP);

  // setup serial
  Serial.begin(115200);
}

//button processing
inline void checkButton(byte changed, byte state, byte idx) {
  if (changed & _BV(idx)) {
    int updown = ((state & _BV(idx)) != 0);
    String msg = btnEvents[idx][updown];
    Serial.println(msg);
  }
}

inline void disableLeds(){
	for(int x=0;x<5;x++) {
		digitalWrite( (D_BTN_A0 + x), LOW);
	}
}

/*
 * Read the button values and convert to binary mask.
 */
inline byte getButtonState() {
  byte state = 0;
  for (int i=0; i<5; i++) {
    if (digitalRead(D4+i) == LOW) {
      state = state + (1 << i);
    }
  }
  return state;
}

inline byte getGoalState() {
  byte state = 0;
  for (int i=0; i<2; i++) {
    if (digitalRead(PIN_GOAL_YELLOW + i) == LOW) {
      state = state + (1 << i);
    }
  }
  return state;
}

// check for pressed buttons
byte prevBtns = BTN_MASK;
void processButtons() {
  byte state = getButtonState();
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

unsigned long nextBtnCheck = 0;
unsigned long nextPing = 0;

byte testMode = 0;
// read from serial port and set led status
void processInstructions() {
  if (Serial.available()) {
    int data = Serial.read();
    // from A -> '`' inclusive 5 bits for LEDS - turns into 0 ->31 (for bits B00011111)
    if (data >= 'A' && data <= ('A' + 32)) {
      // take printables ASCII character and shift down
      data = (data & 0xFF) - 'A';
      for(int x=0;x<5;x++) {
        int p = 1 << x;
        if (data & p) {
          // 18 = A0, 19 = A1, etc
          digitalWrite( (D_BTN_A0 + x), HIGH);
        } else {
          digitalWrite( (D_BTN_A0 + x), LOW);
        }
      }
    } else  if (data == 't') {
      testMode = 1;
      //disable all leds
      disableLeds();
      Serial.println("TEST_MODE");
    } else if (data == 'u') {
			testMode = 0;
			//disable all leds
			disableLeds();
			Serial.println("NORM_MODE");
    }
  }
}

inline void processGoal(byte mask, byte goalState, bool *goal, unsigned long *goalTime, unsigned long *offTime, const char *goalString) {
  static char l[100];
  if ((goalState & mask) > 0) {
    if (!*goal) {
      *goal = true;
      *goalTime = micros();
    }
  } else {
    if (*goal) {
      unsigned long now = micros();
      *goal = false;
      sprintf(l, goalString, now - *goalTime, *goalTime - *offTime);
      Serial.println(l);
      *offTime = now;
    }
  }
}

unsigned long goalTimeY = 0;
unsigned long goalTimeB = 0;
unsigned long offTimeY = 0;
unsigned long offTimeB = 0;
bool goalY = false;
bool goalB = false;
unsigned long start = 0;
byte prev_goals = 0;
#define TIME_ELAPSED(now, ts) ((long)(now - ts) >= 0)
bool goalsEnabled = false;
// enable goals a bit after startup to avoid false events
unsigned long reenableGoalsAt = 1000;


void loop() {
  if (testMode) {
    //Serial.println( digitalRead(PIN_GOAL_BLACK) );
    //Serial.println( digitalRead(PIN_GOAL_YELLOW) );
    digitalWrite(TEST_LED_BLACK, !digitalRead(PIN_GOAL_BLACK));
    digitalWrite(TEST_LED_YELLOW, !digitalRead(PIN_GOAL_YELLOW));
    //delay(2000);
  } else {
    bool processingGoal = 0;
    if (goalsEnabled) {
      byte goalState = getGoalState();
      processGoal(PIN_MASK_YELLOW, goalState, &goalY, &goalTimeY, &offTimeY, GOAL_YELLOW_STR);
      processGoal(PIN_MASK_BLACK,  goalState, &goalB, &goalTimeB, &offTimeB, GOAL_BLACK_STR);
    }
    // don't process buttons or instructions during goal checking
    if (goalY | goalB) {
      return;
    }

    unsigned long now = millis();
    if (goalsEnabled == 0 && TIME_ELAPSED(now, reenableGoalsAt)) {
      goalsEnabled = 1;
      reenableGoalsAt = 0;
    }

    if (TIME_ELAPSED(now, nextBtnCheck)) {
      nextBtnCheck = now + BTN_INTERVAL;
      processButtons();
    }
    if (TIME_ELAPSED(now, nextPing)) {
      nextPing = now + PING_INTERVAL;
      Serial.println("P");
    }
  }
	processInstructions();
  delay(1);
}
