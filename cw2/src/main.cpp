//////////////////// Includes //////////////////////////////////////////////////
#include "mbed.h"
#include "Crypto.h"

//////////////////// Variables /////////////////////////////////////////////////
//Photointerrupter input pins
#define I1pin D2
#define I2pin D11
#define I3pin D12

//Incremental encoder input pins
#define CHA   D7
#define CHB   D8  

//Motor Drive output pins   //Mask in output byte
#define L1Lpin D4           //0x01
#define L1Hpin D5           //0x02
#define L2Lpin D3           //0x04
#define L2Hpin D6           //0x08
#define L3Lpin D9           //0x10
#define L3Hpin D10          //0x20

//Mapping from sequential drive states to motor phase outputs
/*
State   L1  L2  L3
0       H   -   L
1       -   H   L
2       L   H   -
3       L   -   H
4       -   L   H
5       H   L   -
6       -   -   -
7       -   -   -
*/
//Drive state to output table
const int8_t driveTable[] = {0x12,0x18,0x09,0x21,0x24,0x06,0x00,0x00};

//Mapping from interrupter inputs to sequential rotor states. 0x00 and 0x07
// are not valid
const int8_t stateMap[] = {0x07,0x05,0x03,0x04,0x01,0x00,0x02,0x07};  
//const int8_t stateMap[] = {0x07,0x01,0x03,0x02,0x05,0x00,0x04,0x07};
  //Alternative if phase order of input or drive is reversed

//Phase lead to make motor spin
const int8_t lead = 2;  //2 for forwards, -2 for backwards

//Rotor states
int8_t orState = 0;              /* Rotot offset at motor state 0 */
volatile int8_t intStateOld = 0; /* Motor old state. Type is volatile since
                                    its value may change in ISR */
//Status LED
DigitalOut led1(LED1);

//Photointerrupter inputs
InterruptIn I1(I1pin);
InterruptIn I2(I2pin);
InterruptIn I3(I3pin);

//Motor Drive outputs
DigitalOut L1L(L1Lpin);
DigitalOut L1H(L1Hpin);
DigitalOut L2L(L2Lpin);
DigitalOut L2H(L2Hpin);
DigitalOut L3L(L3Lpin);
DigitalOut L3H(L3Hpin);

//TImers
Timer t_bitcoin;                /* for calculating hash computation rate */
 
//////////////////// Functions /////////////////////////////////////////////////

//Set a given drive state
void motorOut(int8_t driveState){
    
    //Lookup the output byte from the drive state.
    int8_t driveOut = driveTable[driveState & 0x07];
      
    //Turn off first
    if (~driveOut & 0x01) L1L = 0;
    if (~driveOut & 0x02) L1H = 1;
    if (~driveOut & 0x04) L2L = 0;
    if (~driveOut & 0x08) L2H = 1;
    if (~driveOut & 0x10) L3L = 0;
    if (~driveOut & 0x20) L3H = 1;
    
    //Then turn on
    if (driveOut & 0x01) L1L = 1;
    if (driveOut & 0x02) L1H = 0;
    if (driveOut & 0x04) L2L = 1;
    if (driveOut & 0x08) L2H = 0;
    if (driveOut & 0x10) L3L = 1;
    if (driveOut & 0x20) L3H = 0;
}
    
//Convert photointerrupter inputs to a rotor state
inline int8_t readRotorState(){
    return stateMap[I1 + 2*I2 + 4*I3];
}

//Basic synchronisation routine    
int8_t motorHome() {
    //Put the motor in drive state 0 and wait for it to stabilise
    motorOut(0);
    wait(2.0);
    
    //Get the rotor state
    return readRotorState();
}

// motor ISR
void motorISR() {
    int8_t intState = readRotorState();
    if (intState != intStateOld) {
        intStateOld = intState;
        motorOut((intState-orState+lead+6)%6); //+6 to make sure the remainder
                                               //  is positive
    }
}

//////////////////// Main //////////////////////////////////////////////////////
int main() {
    //Attach interrupt service routines to photointerrupters
    I1.rise(&motorISR);
    I1.fall(&motorISR);
    I2.rise(&motorISR);
    I2.fall(&motorISR);
    I3.rise(&motorISR);
    I3.fall(&motorISR);
    
    //Bitcoin
    SHA256 sha;
    const uint8_t sequence[] = {\
        0x45,0x6D,0x62,0x65,0x64,0x64,0x65,0x64,\
        0x20,0x53,0x79,0x73,0x74,0x65,0x6D,0x73,\
        0x20,0x61,0x72,0x65,0x20,0x66,0x75,0x6E,\
        0x20,0x61,0x6E,0x64,0x20,0x64,0x6F,0x20,\
        0x61,0x77,0x65,0x73,0x6F,0x6D,0x65,0x20,\
        0x74,0x68,0x69,0x6E,0x67,0x73,0x21,0x20,\
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,\
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    };
    uint64_t* key = (uint64_t*)((int)sequence + 48);
    uint64_t* nonce = (uint64_t*)((int)sequence + 56);
    uint8_t hash[32];
    uint32_t hash_counter = 0;  // for calculating hash computation rate
    
    /* Initialise the serial port */
    Serial pc(SERIAL_TX, SERIAL_RX);
    pc.printf("\n\rHello world!\n\r");
    
    /* Run the motor synchronisation
       orState is subtracted from future rotor state inputs to align rotor and
       motor states */
    orState = motorHome();
    pc.printf("Rotor origin: %x\n\r",orState);
    
    /* Bitcoin mining (photointerrupter may also happen in this loop) */
    t_bitcoin.start();          // start timer
    while (1) {
        sha.computeHash(hash, (uint8_t*)sequence, 64);
        if(hash[0] == 0 && hash[1] == 0)            // if nonce is found
            printf("Nonce: 0x%016llX\n\r", *nonce);
            
        (*nonce)++;         // increment nonce value
        hash_counter++;     // increment counter
        
        if(t_bitcoin.read() >= 1) {                 // check if 1 second passed
            //printf("Computation rate per second: %d\n\r", hash_counter);
            printf("Comp. rate: %d\n\r", hash_counter);// report rate per second
            t_bitcoin.reset();  // reset timer
            hash_counter = 0;   // reset counter
        }
    }
}
