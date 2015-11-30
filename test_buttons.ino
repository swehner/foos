#define BTN_INTERVAL 50

void setup() {
  //analog pins - button leds
  DDRC=0xFF;
  PORTC=0;
  
  //8-12 button inputs
  DDRB &= 0b01111111;
  //enable pullups
  PORTB |= 0b01111111;
  Serial.begin(115200);
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

unsigned long next_check = 0;
void loop() {
  processLeds();
  unsigned long now = millis();
  // TODO: handle millis overflow
  if (now > next_check) {
    next_check = now + BTN_INTERVAL;
    processButtons(PINB);
  }
}
