#include "SIM900.h"
#include <SoftwareSerial.h>
#include "sms.h"

SMSGSM sms;

SoftwareSerial mySerial(7, 8);
char serialData[50];
int counter = 0;
int numdata;
boolean started=false;
char smsbuffer[160];
char n[20];

void setup() 
{
  //Serial connection.
  mySerial.begin(9600);
  Serial.begin(9600);
  Serial.println("GSM Shield testing.");
  //Start configuration of shield with baudrate.
  //For http uses is raccomanded to use 4800 or slower.
  if (gsm.begin(2400)){
    Serial.println("\nstatus=READY");
    started=true;  
  }
  else Serial.println("\nstatus=IDLE");
  
//  if(started){
//    //Enable this two lines if you want to send an SMS.
//    if (sms.SendSMS("+639165568927", "Arduino SMS"))
//      Serial.println("\nSMS sent OK");
//  }

};

void loop() 
{
  if (started) {
    Serial.println("\nstatus=STARTED");
    while (!Serial.available()) {} // wait for data to arrive
    // serial read section
    while (Serial.available()) {
      Serial.println("\n" + Serial.available());
      if(Serial.available()>0) {
        String stringData = Serial.readString();
        char smsCode[7]; 
        char mobileNo[14]; 
        char lockerNo[6]; 
        char hours[2]; 
        char expiryDate[20];
        char smsMessage[150] = "You're now subscribed to ";

        //Convert string data to multiple char data type
        stringData.substring(0,5).toCharArray(smsCode, 7);
        stringData.substring(7,20).toCharArray(mobileNo, 14);
        stringData.substring(21,26).toCharArray(lockerNo, 6);
        stringData.substring(27,28).toCharArray(hours, 2);
        stringData.substring(29).toCharArray(expiryDate, 20);

        //char smsMessage[] = "You're now subscribed to " + lockerNo + " locker slot for " + hours + " hours and will expire on " + expiryDate + ". Thank you for subscribing.";
        //strcat(smsMessage, "You're now subscribed to ");
        
        //smsMessage = "You're now subscribed to ";
        strcat(smsMessage, lockerNo);
        strcat(smsMessage, " locker slot for ");
        strcat(smsMessage, hours);
        strcat(smsMessage, " hours and will expire on ");
        strcat(smsMessage, expiryDate);
        strcat(smsMessage, ". Thank you for subscribing.");
        
        if(counter<1) {
          String contactNo(mobileNo);
          Serial.println("\n" + contactNo);
          sms.SendSMS(mobileNo, smsMessage);
          Serial.println("\nTest SMS sent OK");
        }
      }
      delay(500);
    }
    if (mySerial.available()>0) Serial.write(mySerial.read());
    
   }
};
