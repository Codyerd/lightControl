#include <WiFi.h> 
#include <SocketIoClient.h>


const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* serverUrl = "moscapital.ddns.net";  // URL
const int serverPort = 5000;

const int relay = 26;
const char* device_id = "esp32_switch";  // Fixed ID for this relay-switch

SocketIoClient socket;


void registerDevice() {
    Serial.print("Registering device... ");
    socket.emit("register", "\" esp32_switch \"");
}

void onMessageReceived(const char *data, size_t length) {
    Serial.print("Received: ");
    Serial.println(data);

    if (String(data).indexOf("\"state\":\"on\"") != -1) {
        digitalWrite(relay, HIGH);  // Turn light ON
    } else {
        digitalWrite(relay, LOW);   // Turn light OFF
    }
}
 
void setup() {
    Serial.begin(115200);
    pinMode(relay, OUTPUT);
    digitalWrite(relay, LOW);

    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi...");
    while (WiFi.status() != WL_CONNECTED) {
        delay(100);
        Serial.print(".");
    }
    Serial.println("\nConnected!");

    // socket.begin(serverUrl, serverPort, "/socket.io/?EIO=4");
    socket.begin(serverUrl, serverPort, "/socket.io/?EIO=4&transport=websocket");
    Serial.print("Destination server binded.");
    socket.on("light_status", onMessageReceived);  // Listen for light status updates

    // Wait a bit before sending registration
    delay(1000);
    registerDevice();
}

void loop() {
    socket.loop();  // Keep listening for messages
    delay(1000);
}

