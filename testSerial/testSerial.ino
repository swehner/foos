void setup() {
  Serial.begin(115200);
  Serial.setTimeout(100);
}

int i=0;
void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    Serial.print("echo ");
    Serial.println(data);
  }
  Serial.print("Ping ");
  Serial.println(i++);
  delay(100);
}
