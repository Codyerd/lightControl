// Required Arduino library: ArduinoJson, Websokcets, ArduinoWebsockets
// Simulation: https://wokwi.com/projects/422240651036554241

#include <Arduino.h>

#include <WiFi.h>
#include <WiFiMulti.h>
#include <WiFiClientSecure.h>

#include <ArduinoJson.h>

#include <WebSocketsClient.h>
#include <SocketIOclient.h>

WiFiMulti WiFiMulti;
SocketIOclient socketIO;

#define USE_SERIAL Serial
const int relay = 26;
const char* ssid = "Wokwi-GUEST";
const char* password = "";

void registerDevice() {
    // register the current device
    Serial.println("Registering device...");
    // create JSON message for Socket.IO (event)
    DynamicJsonDocument docu(1024);
    JsonArray array = docu.to<JsonArray>();

    // add event name
    array.add("register");
    // add payload (parameters) for the event
    array.add("esp32_switch");

    // JSON to String (serialization)
    String out;
    serializeJson(docu, out);

    // Send event
    socketIO.sendEVENT(out);

    // Print JSON for debugging
    Serial.println(out);
}

void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case sIOtype_DISCONNECT:
            USE_SERIAL.printf("[IOc] Disconnected!\n");
            break;
        case sIOtype_CONNECT:
            USE_SERIAL.printf("[IOc] Connected to url: %s\n", payload);

            // join default namespace (no auto join in Socket.IO V3)
            socketIO.send(sIOtype_CONNECT, "/");
            registerDevice();
            break;
        case sIOtype_EVENT:
        {
            char * sptr = NULL;
            int id = strtol((char *)payload, &sptr, 10);
            USE_SERIAL.printf("[IOc] get event: %s id: %d\n", payload, id);
            if(id) {
                payload = (uint8_t *)sptr;
            }
            DynamicJsonDocument doc(1024);
            DeserializationError error = deserializeJson(doc, payload, length);
            if(error) {
                USE_SERIAL.print(F("deserializeJson() failed: "));
                USE_SERIAL.println(error.c_str());
                return;
            }

            String eventName = doc[0];
            USE_SERIAL.printf("[IOc] event name: %s\n", eventName.c_str());
            if (eventName == "light_status") {
                Serial.print("Received: ");
                Serial.println(doc[1].as<String>());
                if (doc[1]["state"] == "on") {
                    digitalWrite(relay, HIGH);  // Turn light ON
                } else {
                    digitalWrite(relay, LOW);   // Turn light OFF
                }
            }
            // Message Includes a ID for a ACK (callback)
            // if(id) {
            //     // create JSON message for Socket.IO (ack)
            //     DynamicJsonDocument docOut(1024);
            //     JsonArray array = docOut.to<JsonArray>();

            //     // add payload (parameters) for the ack (callback function)
            //     JsonObject param1 = array.createNestedObject();
            //     param1["now"] = millis();

            //     // JSON to String (serializion)
            //     String output;
            //     output += id;
            //     serializeJson(docOut, output);

            //     // Send event
            //     socketIO.send(sIOtype_ACK, output);
            // }
        }
            break;
    }
}

void setup() {
    //USE_SERIAL.begin(921600);
    USE_SERIAL.begin(115200);

    //Serial.setDebugOutput(true);
    USE_SERIAL.setDebugOutput(true);

    USE_SERIAL.println();
    USE_SERIAL.println();
    USE_SERIAL.println();

      for(uint8_t t = 4; t > 0; t--) {
          USE_SERIAL.printf("[SETUP] BOOT WAIT %d...\n", t);
          USE_SERIAL.flush();
          delay(1000);
      }

    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(100);
        Serial.print(".");
    }
    Serial.println("\nConnected!");

    // server address, port and URL
    socketIO.begin("34.122.140.168", 5000, "/socket.io/?EIO=4");

    // event handler
    socketIO.onEvent(socketIOEvent);
    
}

unsigned long messageTimestamp = 0;

void loop() {
    socketIO.loop();

    {
      // uint64_t now = millis();

      // if(now - messageTimestamp > 2000) {
      //     messageTimestamp = now;

      //     // create JSON message for Socket.IO (event)
      //     DynamicJsonDocument doc(1024);
      //     JsonArray array = doc.to<JsonArray>();

      //     // add event name
      //     // Hint: socket.on('event_name', ....
      //     array.add("event_name");

      //     // add payload (parameters) for the event
      //     JsonObject param1 = array.createNestedObject();
      //     param1["now"] = (uint32_t) now;

      //     // JSON to String (serialization)
      //     String output;
      //     serializeJson(doc, output);

      //     // Send event
      //     socketIO.sendEVENT(output);

      //     // Print JSON for debugging
      //     USE_SERIAL.println(output);
    }
}

