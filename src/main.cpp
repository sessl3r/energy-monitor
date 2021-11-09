#include <Arduino.h>

void setup() {
	Serial.begin(115200);
}

void loop() {
	int x = analogRead(A7);
	Serial.println(x);
	delay(1);
}
