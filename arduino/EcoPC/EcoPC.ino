// EcoPC classic Nano: PIR D2, green D9, red D10; D8 reserved.
// Connect each LED anode to its output through a separate 220-ohm resistor.
// Connect both LED cathodes to GND. The outputs are active HIGH.
// Unknown 5V buzzer current/type: leave disconnected. Code cannot limit
// an OUTPUT pin's current. Enable only after driver/current verification.
const bool BUZZER_HARDWARE_VERIFIED = false;
const byte PIR = 2, GREEN = 9, RED = 10, BUZZER = 8;
unsigned long bootTime, lastReport = 0, lastHost = 0;
bool haveHost = false;
String state = "UNKNOWN", command = "";

void setup() {
  pinMode(PIR, INPUT);
  digitalWrite(GREEN, LOW);
  pinMode(GREEN, OUTPUT);
  digitalWrite(RED, LOW);
  pinMode(RED, OUTPUT);
  pinMode(BUZZER, INPUT);
  if (BUZZER_HARDWARE_VERIFIED) {
    digitalWrite(BUZZER, LOW);
    pinMode(BUZZER, OUTPUT);
  }
  Serial.begin(9600);
  command.reserve(80);
  bootTime = millis();
  Serial.println("WARMUP");
}

void loop() {
  unsigned long now = millis();
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (command.startsWith("STATE:")) {
        String incoming = command.substring(6);
        if (incoming == "ACTIVE" || incoming == "BACKGROUND_WORK" ||
            incoming == "ENERGY_WASTE_SUSPECTED" || incoming == "UNKNOWN" ||
            incoming == "IDLE" || incoming == "TEMPORARILY_AWAY") {
          state = incoming;
          lastHost = now;
          haveHost = true;
        }
      }
      command = "";
    } else if (c != '\r') {
      command += c;
      if (command.length() > 79) command = "";
    }
  }
  if (!haveHost || now - lastHost > 5000UL) state = "UNKNOWN";
  bool warning = state == "ENERGY_WASTE_SUSPECTED";
  bool active = state == "ACTIVE";
  bool background = state == "BACKGROUND_WORK";
  digitalWrite(GREEN, (active || (background && now % 1600 < 800)) ? HIGH : LOW);
  digitalWrite(RED, (warning && now % 1000 < 500) ? HIGH : LOW);
  if (BUZZER_HARDWARE_VERIFIED)
    digitalWrite(BUZZER, warning && now % 2000 < 150 ? HIGH : LOW);
  if (now - bootTime >= 60000UL && now - lastReport >= 250UL) {
    lastReport = now;
    Serial.println(digitalRead(PIR) == HIGH ? "MOTION:1" : "MOTION:0");
  }
}
