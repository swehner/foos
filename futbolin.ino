#include <IRremote.h>

#define PIN_IR_1_IN 4
#define PIN_IR_2_IN 5
#define PIN_STATUS 13

//#define PRINT 1


class DetectRising {
  public:
    DetectRising(int p) {
      pin = p;
      prev = 1;
      pinMode(pin, INPUT);
    }
    int isRising() {
      int isRising = 0;
      int now = digitalRead(pin);
      if (prev == 0 && now == 1) {
        isRising = 1;
      }
      prev = now;
      return isRising;
    }

    int prev, pin;
};

IRsend irsend;
DetectRising ir1(PIN_IR_1_IN);
DetectRising ir2(PIN_IR_2_IN);

void setup()
{
  Serial.begin(115200);
  pinMode(PIN_STATUS, OUTPUT);
  irsend.enableIROut(38);
  irsend.mark(0);
}


void loop() {
  if (ir1.isRising()) {
    Serial.println("BLACK");
  }  
  if (ir2.isRising()) {
    Serial.println("WHITE");
  }
#ifdef PRINT
  Serial.print(!ir1.prev); Serial.print(" "); Serial.println(!ir2.prev);
#endif

  digitalWrite(PIN_STATUS, (!ir1.prev) | (!ir2.prev));
}


