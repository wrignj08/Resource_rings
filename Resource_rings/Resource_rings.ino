#include <FastLED.h>
#define NUM_LEDS_PER_STRIP 64
#define DATA_PIN 10
#define NUM_STRIPS 1
CRGB leds[NUM_LEDS_PER_STRIP * NUM_STRIPS];

const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars];        // temporary array for use when parsing

// variables to hold the parsed data
char messageFromPC[numChars] = {0};

int max_CPU_core = 0;
int total_CPU = 0;
int CPU_temp = 0;
int RAM = 0;
int GPU_RAM = 0;
int GPU_util = 0;
int GPU_temp = 0;

int old_ano1 = 0;
int old_ano2 = 0;
int old_ano3 = 0;

int old_r1 = 0;
int old_r2 = 0;
int old_r3 = 0;
int old_r4 = 0;


unsigned long timer = millis();

int spinner[] = {15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 28, 29, 30, 31, 16, 17, 18, 19, 43, 42, 41, 40, 39, 38, 37, 36, 60, 61, 62, 63, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 35, 34, 33, 32, 47, 46, 45, 44, 20, 21, 22, 23, 24, 25, 26, 27, 3, 2, 1, 0};


boolean newData = false;

//============

void setup() {
  Serial.begin(9600);
  Serial.println("This demo expects 3 pieces of data - text, an integer and a floating point value");
  Serial.println("Enter data in this style <HelloWorld, 12, 24.7>  ");
  Serial.println();
  FastLED.setBrightness(10);
  FastLED.addLeds<NUM_STRIPS, WS2812, 10, GRB>(leds, NUM_LEDS_PER_STRIP);
  rev_ano();
}

//============
//https://forum.arduino.cc/index.php?topic=396450.0
void loop() {
  recvWithStartEndMarkers();
  if (newData == true) {
    strcpy(tempChars, receivedChars);
    // this temporary copy is necessary to protect the original data
    //   because strtok() used in parseData() replaces the commas with \0
    parseData();
    //      showParsedData();
    newData = false;
  }

  if (millis() - timer > 4000) {
    //    all_off();
    spiner_ano ();

  }

  delay(10);
  for (int led_num = max_CPU_core; led_num <= 16;) {
    leds[led_num].fadeToBlackBy( 1 );
    //    leds[led_num] = CRGB::Black;
    led_num++;
  }

}


void rev_ano() {
  for (int LED = 0; LED < 16; LED++) {

    leds[LED] = CRGB::White;
    leds[LED + 16] = CRGB::White;
    leds[LED + 32] = CRGB::White;
    leds[LED + 48] = CRGB::White;
    delay(40);
    FastLED.show();

  }
  for (int LED = 16; LED > -1; LED--) {

    leds[LED] = CRGB::Black;
    leds[LED + 16] = CRGB::Black;
    leds[LED + 32] = CRGB::Black;
    leds[LED + 48] = CRGB::Black;

    delay(40);
    FastLED.show();

  }
}

void spiner_ano () {
  for (int LED = 0; LED < 64; LED++) {
    leds[spinner[old_ano3]] = CRGB::Black;

    leds[spinner[old_ano2]] = CRGB::Red;
    leds[spinner[old_ano1]] = CRGB::HotPink;
    leds[spinner[LED]] = CRGB::White;

    old_ano3 = old_ano2;
    old_ano2 = old_ano1;
    old_ano1 = LED;

    delay(30);
    FastLED.show();

  }
}


void all_off() {
  for (int LED = 0; LED < NUM_LEDS_PER_STRIP; LED++) {

    leds[LED] = CRGB::Black;
    FastLED.show();
  }
}

//============

void recvWithStartEndMarkers() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (recvInProgress == true) {
      if (rc != endMarker) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else {
        receivedChars[ndx] = '\0'; // terminate the string
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }

    else if (rc == startMarker) {
      recvInProgress = true;
    }
  }
}

//============

//int RAM = 0;
//int GPU_ram = 0;
//int GPU_util = 0;

//incoming data looks like <max_CPU_core,total_CPU,RAM,GPU_util,GPU_ram>

void parseData() {      // split the data into its parts

  char * strtokIndx; // this is used by strtok() as an index

  strtokIndx = strtok(tempChars, ","); // this continues where the previous call left off
  max_CPU_core = atoi(strtokIndx);     // convert this part to an integer

  strtokIndx = strtok(NULL, ",");
  total_CPU = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  RAM = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  GPU_util = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  GPU_RAM = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  GPU_temp = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  CPU_temp = atoi(strtokIndx);

  //green = 0x8AE729
  //purple = 0xe7298a
  //blue = 0x29E78A

  //set total CPU load (always lower than max CPU core)

  for (int led_num = 0; led_num < NUM_LEDS_PER_STRIP;) {
    if (led_num > total_CPU) {
      leds[led_num] = CRGB::Black;
    }
    if (led_num <= old_r1) {
      leds[led_num] = 0x8AE729;
    }
    if (led_num <= max_CPU_core) {
      leds[led_num] = 0xe7298a;
    }
    if (led_num <= total_CPU) {
      leds[led_num] = 0x29E78A;
    }
    leds[CPU_temp + 0] = 0xff0000;
    led_num++;
  }

  //set RAM
  for (int led_num = 16; led_num < NUM_LEDS_PER_STRIP;) {
    if (led_num > RAM + 16) {
      leds[led_num] = CRGB::Black;
    }
    if (led_num <= old_r2 + 16) {
      leds[led_num] = 0x8AE729;
    }
    if (led_num <= RAM + 16) {
      leds[led_num] = 0xe7298a;
    }

    led_num++;
  }

  //  //set GPU_util
  for (int led_num = 32; led_num < NUM_LEDS_PER_STRIP;) {
    if (led_num > GPU_util + 32) {
      leds[led_num] = CRGB::Black;
    }
    if (led_num <= old_r3 + 32) {
      leds[led_num] = 0x8AE729;
    }
    if (led_num <= GPU_util + 32) {
      leds[led_num] = 0xe7298a;
    }
    leds[GPU_temp + 32] = 0xff0000;
    led_num++;
  }

  //  //set off leds on ring 4
  for (int led_num = 48; led_num < NUM_LEDS_PER_STRIP;) {
    if (led_num > GPU_RAM + 48) {
      leds[led_num] = CRGB::Black;
    }
    if (led_num <= old_r4 + 48) {
      leds[led_num] = 0x8AE729;
    }
    if (led_num <= GPU_RAM + 48) {
      leds[led_num] = 0xe7298a;
    }

    led_num++;
  }

  FastLED.show();
  old_r1 = max_CPU_core;
  old_r2 = RAM;
  old_r3 = GPU_util;
  old_r4 = GPU_RAM;
  timer = millis();
}
