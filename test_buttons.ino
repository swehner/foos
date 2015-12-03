#include <IRremote.h>

#define BTN_INTERVAL 10

IRsend irsend;

void setup() {
  //analog pins - button leds
  DDRC=0xFF;
  PORTC=0;
  
  //8-12 button inputs
  DDRB=0x00;
  //enable pullups
  PORTB |= 0b01111111;
  Serial.begin(115200);

  //set pin 4,5 to input
  //DDRD&=0b11001111;
  pinMode(4, INPUT);
  pinMode(5, INPUT);

  irsend.enableIROut(38);
  irsend.mark(0);
}


// check for pressed buttons
byte prev_btns = 0xFF;
char* events[5][2]={{"A0", "A1"}, {"B0", "B1"}, {"C0", "C1"}, {"D0", "D1"}, {"E0", "E1"}};

void processButtons(byte state) {
  // TODO: use bits connected to buttons exclusively
  char changed = prev_btns ^ state;

  if (changed) {
    // save new state
    prev_btns = state; 
    // check which button has changed
    for(byte idx = 0; idx < 5; idx++) { 
      if (changed & 0x01) {
        Serial.println(events[idx][state & 0x01]);
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
    Serial.println(data);
    if (data != '\n') {
      data = (data & 0xFF) - 32;
      PORTC = data;
      Serial.println(data);
    }
  }
}

byte prevGoals = 0;
void processGoals(byte state) {
  if (((prevGoals & _BV(4)) == 0) && (state & _BV(4))) {
    Serial.println("G4");
  }
  if (((prevGoals & _BV(5)) == 0) && (state &_BV(5))) {
    Serial.println("G5");
  }
  prevGoals = state;
}

unsigned long next_check = 0;
void loop() {
  processGoals(PIND);
  processLeds();
  unsigned long now = millis();
  // TODO: handle millis overflow
  if (now > next_check) {
    next_check = now + BTN_INTERVAL;
    processButtons(PINB);
  }
}
