#include <Servo.h>  

Servo servo1;  
Servo servo2;
int alpha = 1;
int current1 = 90;
int current2 = 90;

void setup() {
  Serial.begin(9600);
  servo1.attach(8);  // Pin 8 pour le premier servo
  servo2.attach(9);  // Pin 9 pour le deuxième servo
  servo1.write(current1);
  servo2.write(current2);
}

void loop() {

  if (Serial.available()) {
    int inByte = Serial.read();

    if (inByte == '1') {
      current1 += alpha;
    } else if (inByte == '2') {
      current1 -= alpha;
    }
   
    if (inByte == '3') {
      current2 += alpha;
    } else if (inByte == '4') {
      current2 -= alpha;
    }

    if (inByte == '5') {
        servo1.write(90);
        servo2.write(90);
    }
   
    if (current1 > 180) current1 = 180;
    if (current1 < 0)   current1 = 0;
    if (current2 > 180) current2 = 180;
    if (current2 < 0)   current2 = 0;
   
    servo1.write(current1);
    servo2.write(current2);
  }
}

