#include <IRremote.h>

//check buttons every X ms
#define BTN_INTERVAL 10

IRsend irsend;

#define PIN_GOAL_BLACK 4
#define PIN_GOAL_YELLOW 5
#define GOAL_BLACK_STR "GB"
#define GOAL_YELLOW_STR "GY"

char* btnEvents[5][2] = {{"A0", "A1"}, {"B0", "B1"}, {"C0", "C1"}, {"D0", "D1"}, {"E0", "E1"}};

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

// read from serial port and set led status
void processLeds() {
  if (Serial.available()) {
    int data = Serial.read();
    if (data != '\n' && data > 0) {
      // take printables ASCII character and shift down
      data = (data & 0xFF) - 32;
      PORTC = data;
    }
  }
}

//process goal ir barriers
byte prevGoals = 0;
void processGoals(byte state) {
  // check for falling edge
  if ((prevGoals & _BV(PIN_GOAL_BLACK)) && ((state & _BV(PIN_GOAL_BLACK)) == 0)) {
    Serial.println(GOAL_BLACK_STR);
  }
  if ((prevGoals & _BV(PIN_GOAL_YELLOW)) && ((state &_BV(PIN_GOAL_YELLOW)) == 0)) {
    Serial.println(GOAL_YELLOW_STR);
  }
  
  prevGoals = state;
}

unsigned long nextBtnCheck = 0;
void loop() {
  processGoals(PIND);
  processLeds();
  unsigned long now = millis();
  if ((long)(now - nextBtnCheck) >= 0) {
    nextBtnCheck = now + BTN_INTERVAL;
    processButtons(PINB);
  }
}
