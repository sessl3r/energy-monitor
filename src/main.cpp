#include <Arduino.h>
#include <EmonLib.h>

#define SAMPLES 1000 
#define LOOPS 32

EnergyMonitor emonL1;
EnergyMonitor emonL2;
EnergyMonitor emonL3;

void print_phases(const char* opt, double l1, double l2, double l3) {
	Serial.print(opt);
	Serial.print(",");
	Serial.print(l1);
	Serial.print(",");
	Serial.print(l2);
	Serial.print(",");
	Serial.println(l3);
}

void setup() {
	Serial.begin(115200);
	emonL1.current(0, 26.4);
	emonL2.current(1, 26.4);
	emonL3.current(2, 26.4);
}

void loop() {
	double I[3] = { 0 };
	for (int i=0 ; i<LOOPS; i++) {
		I[0] += emonL1.calcIrms(SAMPLES);
		I[1] += emonL2.calcIrms(SAMPLES);
		I[2] += emonL3.calcIrms(SAMPLES);
		print_phases("DBG", I[0], I[1], I[2]);
	}
	I[0] /= LOOPS;
	I[1] /= LOOPS;
	I[2] /= LOOPS;
	print_phases("NOM", I[0]*234.0, I[1]*234.0, I[2]*234.0);
}
