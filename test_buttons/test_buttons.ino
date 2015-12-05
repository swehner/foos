#include <IRremote.h>
IRsend irsend;

//check buttons every X ms
#define BTN_INTERVAL 10
#define GOAL_DEBOUNCE_TIME 500
#define PING_INTERVAL 5000

#define PIN_GOAL_BLACK 4
#define PIN_GOAL_YELLOW 5
#define GOAL_BLACK_STR "BG"
#define GOAL_YELLOW_STR "YG"

#define TEST_LED_BLACK A0
#define TEST_LED_YELLOW A2

char* btnEvents[5][2] = {{"BD_D", "BD_U"}, {"BI_D", "BI_U"}, {"YD_D", "YD_U"}, {"YI_D", "YI_U"}, {"OK_D", "OK_U"}};

void setup() {
  //analog pins - button leds
  DDRC = 0xFF;
  PORTC = 0;
  
  //8-12 button inputs
  DDRB = 0x00;
  //enable pullups
  PORTB |= 0b01111111;
  Serial.begin(115200);

  //set pin 4,5 to input
  pinMode(PIN_GOAL_BLACK, INPUT);
  pinMode(PIN_GOAL_YELLOW, INPUT);

  irsend.enableIROut(38);
  irsend.mark(0);
}

// check for pressed buttons
byte prevBtns = 0xFF;
void processButtons(byte state) {
  byte changed = prevBtns ^ (state & 0b00011111);

  if (changed) {
    // save new state
    prevBtns = state; 
    // check which button has changed
    for(byte idx = 0; idx < 5; idx++) { 
      if (changed & 0x01) {
        Serial.println(btnEvents[idx][state & 0x01]);
      }
      changed >>= 1;
      state >>= 1;
    }
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


#define RISING_EDGE(prev, now, pin) (((prev & _BV(pin)) == 0) && ((now & _BV(pin))))
//process goal ir barriers
byte prevGoals = 0;
byte processGoals(byte state) {
  char* goal = NULL;
  // check for rising edge
  if (RISING_EDGE(prevGoals, state, PIN_GOAL_BLACK)) {
    goal = GOAL_BLACK_STR;
  }
  if (RISING_EDGE(prevGoals, state, PIN_GOAL_YELLOW)) {
    goal = GOAL_YELLOW_STR;
  }
  
  if (goal) {
    Serial.println(goal);
  }
  
  prevGoals = state;
  return goal != NULL;
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
    if (soonestNextGoalCheck == 0 || ((long)(now - soonestNextGoalCheck) >= 0)) {
      if (processGoals(PIND)) {
        soonestNextGoalCheck = now + GOAL_DEBOUNCE_TIME;
      }
    }
    if ((long)(now - nextBtnCheck) >= 0) {
      nextBtnCheck = now + BTN_INTERVAL;
      processButtons(PINB);
    }
    if ((long)(now - nextPing) >= 0) {
      nextPing = now + PING_INTERVAL;
      Serial.println("P");
    }
  }
}
