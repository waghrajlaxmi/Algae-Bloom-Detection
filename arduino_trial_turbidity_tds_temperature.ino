#include <PubSubClient.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <time.h>
#include <OneWire.h>
#include <DallasTemperature.h>
int sensorPin = A0; //A0 FOR ARDUINO/ 36 FOR ESP

// Replace with your network credentials
const char* ssid = "NAIKS";
const char* password = "NAIKS@54321";

// Replace with your MQTT broker IP address
const char* mqttServer = "192.168.0.113";
const int mqttPort = 1883;
const char* mqttTopic = "sensors/data";

WiFiClient espClient;
PubSubClient client(espClient);

// Function to establish MQTT connection
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Function to reconnect to MQTT broker
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("arduinoClient")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

// // Function to generate random float values between min and max
// float randomFloat(float minVal, float maxVal) {
//   return minVal + (maxVal - minVal) * random(1000) / 1000.0;
// }

#define TdsSensorPin A3
#define VREF 3.3              // analog reference voltage(Volt) of the ADC
#define SCOUNT  30            // sum of sample point
#define ONE_WIRE_BUS 26

int analogBuffer[SCOUNT];     // store the analog value in the array, read from ADC
int analogBufferTemp[SCOUNT];
int analogBufferIndex = 0;
int copyIndex = 0;

float averageVoltage = 0;
float tdsValue = 0;
float temperature = 25;  
int getMedianNum(int bArray[], int iFilterLen){
  int bTab[iFilterLen];
  for (byte i = 0; i<iFilterLen; i++)
  bTab[i] = bArray[i];
  int i, j, bTemp;
  for (j = 0; j < iFilterLen - 1; j++) {
    for (i = 0; i < iFilterLen - j - 1; i++) {
      if (bTab[i] > bTab[i + 1]) {
        bTemp = bTab[i];
        bTab[i] = bTab[i + 1];
        bTab[i + 1] = bTemp;
      }
    }
  }
  if ((iFilterLen & 1) > 0){
    bTemp = bTab[(iFilterLen - 1) / 2];
  }
  else {
    bTemp = (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
  }
  return bTemp;
}

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(9600);
  sensors.begin();
  setup_wifi();
  client.setServer(mqttServer, mqttPort);
  configTime(0, 0, "pool.ntp.org");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
    static unsigned long analogSampleTimepoint = millis();
  if(millis()-analogSampleTimepoint > 40U){     //every 40 milliseconds,read the analog value from the ADC
    analogSampleTimepoint = millis();
    analogBuffer[analogBufferIndex] = analogRead(TdsSensorPin);    //read the analog value and store into the buffer
    analogBufferIndex++;
    if(analogBufferIndex == SCOUNT){ 
      analogBufferIndex = 0;
    }
  }   
  
  static unsigned long printTimepoint = millis();
  if(millis()-printTimepoint > 800U){
    printTimepoint = millis();
    for(copyIndex=0; copyIndex<SCOUNT; copyIndex++){
      analogBufferTemp[copyIndex] = analogBuffer[copyIndex];
      
      // read the analog value more stable by the median filtering algorithm, and convert to voltage value
      averageVoltage = getMedianNum(analogBufferTemp,SCOUNT) * (float)VREF / 4096.0;
      
      //temperature compensation formula: fFinalResult(25^C) = fFinalResult(current)/(1.0+0.02*(fTP-25.0)); 
      float compensationCoefficient = 1.0+0.02*(temperature-25.0);
      //temperature compensation
      float compensationVoltage=averageVoltage/compensationCoefficient;
      
      //convert voltage value to tds value
      tdsValue=(133.42*compensationVoltage*compensationVoltage*compensationVoltage - 255.86*compensationVoltage*compensationVoltage + 857.39*compensationVoltage)*0.5;
    }
  }
  int sensorValue = analogRead(sensorPin);
  float turbidity = map(sensorValue, 0, 750, 100, 0);
  sensors.requestTemperatures(); // Send the command to get temperatures
  
  float temperatureC = sensors.getTempCByIndex(0); // Read temperature in Celsius
  float tempc = temperatureC;
  float tds = tdsValue; // Example TDS range: 100-2000 ppm
  // float turbidity = randomFloat(0, 5); // Example turbidity range: 0-5 NTU
  float ph;

  if (tempc > 26 && tds > 280 && turbidity > 5) {
    // If temperature is greater than 26, TDS is greater than 280, and turbidity is greater than 5
    // Set pH between 8 and 9.5
    ph = randomFloat(8, 9.5);
  } else {
    // Otherwise, set pH between 6.5 and 7.5
    ph = randomFloat(6.5, 7.5);
  }  
  StaticJsonDocument<128> doc;
  doc["temperature"] = tempc;
  doc["tds"] = tds;
  doc["ph"] = ph;
  doc["turbidity"] = turbidity;

  time_t now = time(nullptr); // Get the current system time
  struct tm* timeinfo = localtime(&now);

  // Add offset for GMT+5:30
  timeinfo->tm_hour += 5;
  timeinfo->tm_min += 30;

  // Correct for overflow/underflow of minutes and hours
  if (timeinfo->tm_min >= 60) {
    timeinfo->tm_hour += 1;
    timeinfo->tm_min -= 60;
  }
  if (timeinfo->tm_hour >= 24) {
    timeinfo->tm_hour -= 24;
  }

  char timestamp[20];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", timeinfo);
  doc["timestamp"] = timestamp;

  char payload[128];
  serializeJson(doc, payload);

  client.publish(mqttTopic, payload);
  delay(1000); // Publish data every second
  Serial.println(payload);
}

