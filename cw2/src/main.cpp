//////////////////// Includes //////////////////////////////////////////////////
#include "mbed.h"
#include "Crypto.h" // hash
#include "rtos.h"   // RTOS

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
int8_t lead = 2;  //2 for forwards, -2 for backwards

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
PwmOut     L1L(L1Lpin);
DigitalOut L1H(L1Hpin);
PwmOut     L2L(L2Lpin);
DigitalOut L2H(L2Hpin);
PwmOut     L3L(L3Lpin);
DigitalOut L3H(L3Hpin);

//TImers
Timer t_bitcoin;                // for calculating hash computation rate

//Threads
Thread commOutT(    osPriorityAboveNormal,1024);  // output to serial
Thread commInT(     osPriorityAboveNormal,1024);  // input from serial
Thread motorCtrlT(  osPriorityNormal,     1024);  // motor control

//Serial port
RawSerial pc(SERIAL_TX, SERIAL_RX);

//Mail
enum MsgCode {
    MSG_CODE_NONCE_MATCH,
    MSG_CODE_COMP_RATE,
    MSG_CODE_DECODED_KEY,
    MSG_CODE_DECODED_TORQUE,
    MSG_CODE_DECODED_VEL,
    MSG_CODE_DECODED_POS,
    MSG_CODE_REPORT_VEL,
    MSG_CODE_REPORT_POS,
    MSG_CODE_MISC
};
typedef struct {
    MsgCode code;
    uint32_t data;
} message_t;
Mail<message_t,16> outMessages;

//Queue
Queue<void, 8> inCharQ;

//Serial command buffer
#define MAX_CMD_LEN 64
char newCmd[MAX_CMD_LEN];
volatile uint8_t newCmd_index = 0;

//For passing key from command to bitcoin miner
volatile uint64_t newKey;   // new mining key
Mutex newKey_mutex;         // prevent simultaneous access of newKey

#define MAX_PWM_PULSEWIDTH_US 1000
volatile uint32_t motorPower = MAX_PWM_PULSEWIDTH_US; // motor toque
volatile float    motorVelocity; // current motor vel. (updated by controller)
volatile float    motorPosition; // current motor pos. (updated by motorISR)
volatile float    targetVelocity = 50;
volatile float    targetPosition = 600;
volatile float    targetRotation = 0;

//////////////////// Function prototypes ///////////////////////////////////////
void motorOut(int8_t driveState, uint32_t pw);
inline int8_t readRotorState();
int8_t motorHome();
void motorISR();

void commOutFn();
void putMessage(MsgCode code, uint32_t data);

void serialISR();
void commInFn();

void motorCtrlFn();
void motorCtrlTick(); //ISR triggered by Ticker

//////////////////// Main //////////////////////////////////////////////////////
int main() {
    /* Initialisation */
    pc.printf("\n\r\n\rGroup: LLLJ\n\rMotor started\n\r");
    pc.printf("Initial targets:\n\r");
    pc.printf("\tVelocity:\t%f\n\r", targetVelocity);
    pc.printf("\tPosition:\t%f\n\r", targetPosition);
    pc.printf("\tRotation:\t%f\n\r", targetRotation);
    
    // Start threads
    commOutT.start(commOutFn);
    commInT.start(commInFn);
    motorCtrlT.start(motorCtrlFn);
    
    // Attach ISR to serial
    pc.attach(&serialISR);
    
    // Attach ISR to photointerrupters
    I1.rise(&motorISR);
    I1.fall(&motorISR);
    I2.rise(&motorISR);
    I2.fall(&motorISR);
    I3.rise(&motorISR);
    I3.fall(&motorISR);
    
    // Declare bitcoin variables
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
    
    // Set PWM period
    // CAUTION: duty cycle must be limited to 0-50% due to hardware limitation
    L1L.period_us(2000); // set to 2000us
    L2L.period_us(2000);
    L3L.period_us(2000);
    
    /* Run the motor synchronisation: orState is subtracted from future rotor
       state inputs to align rotor and motor states */
    orState = motorHome();
    //pc.printf("Rotor origin: %x\n\r", orState);
    
    // Initial jolt
    motorISR();
    
    /* Main loop */
    t_bitcoin.start();          // start timer
    while (1) {
        // update key
        newKey_mutex.lock();
        *key = newKey;
        newKey_mutex.unlock();
        
        // compute hash
        sha.computeHash(hash, (uint8_t*)sequence, 64);
        if(hash[0] == 0 && hash[1] == 0)
            putMessage(MSG_CODE_NONCE_MATCH, *nonce);   // matching nonce
        
        // increment nonce value and counter
        (*nonce)++;
        hash_counter++;
        
        // report rate every second
        if(t_bitcoin.read() >= 1) {
            putMessage(MSG_CODE_COMP_RATE, hash_counter); // comp. rate
            t_bitcoin.reset();  // reset timer
            hash_counter = 0;   // reset counter
        }
    }
}

//////////////////// Functions /////////////////////////////////////////////////

//Set a given drive state
void motorOut(int8_t driveState, uint32_t pw){
    
    //Lookup the output byte from the drive state.
    int8_t driveOut = driveTable[driveState & 0x07];
      
    //Turn off first
    if (~driveOut & 0x01) L1L.pulsewidth_us(0);
    if (~driveOut & 0x02) L1H = 1;
    if (~driveOut & 0x04) L2L.pulsewidth_us(0);
    if (~driveOut & 0x08) L2H = 1;
    if (~driveOut & 0x10) L3L.pulsewidth_us(0);
    if (~driveOut & 0x20) L3H = 1;
    
    //Then turn on
    if (driveOut & 0x01) L1L.pulsewidth_us(pw);
    if (driveOut & 0x02) L1H = 0;
    if (driveOut & 0x04) L2L.pulsewidth_us(pw);
    if (driveOut & 0x08) L2H = 0;
    if (driveOut & 0x10) L3L.pulsewidth_us(pw);
    if (driveOut & 0x20) L3H = 0;
}
    
//Convert photointerrupter inputs to a rotor state
inline int8_t readRotorState(){
    return stateMap[I1 + 2*I2 + 4*I3];
}

//Basic synchronisation routine    
int8_t motorHome() {
    //Put the motor in drive state 0 and wait for it to stabilise
    motorOut(0, MAX_PWM_PULSEWIDTH_US); // set to max PWM
    wait(2.0);
    
    //Get the rotor state
    return readRotorState();
}

// Motor ISR (photointerrupters)
void motorISR() {
    static int8_t oldRotorState;
    int8_t rotorState = readRotorState();
    
    motorOut((rotorState-orState+lead+6)%6,motorPower);
    
    // update motorPosition and oldRotorState
    if (rotorState - oldRotorState == 5) motorPosition--;
    else if (rotorState - oldRotorState == -5) motorPosition++;
    else motorPosition += (rotorState - oldRotorState);
    oldRotorState = rotorState;
}

// Print message in queue
void commOutFn() {
    while(1) {
        osEvent newEvent = outMessages.get();
        message_t *pMessage = (message_t*)newEvent.value.p;
          
        switch(pMessage->code) {
            case MSG_CODE_NONCE_MATCH:
                pc.printf("Nonce found:\t0x%016x\n\r", pMessage->data);
                break;
            case MSG_CODE_COMP_RATE:
                pc.printf("Mining rate:\t%u hashes per second\n\r", \
                    pMessage->data);
                break;
            case MSG_CODE_DECODED_KEY:
                pc.printf("New key:\t0x%016x\n\r", pMessage->data);
                break;
            case MSG_CODE_DECODED_TORQUE:
                pc.printf("New torque:\t%d\n\r", pMessage->data);
                break;
            case MSG_CODE_DECODED_VEL:
                pc.printf("New target velocity:\t%.1f\n\r", targetVelocity);
                break;
            case MSG_CODE_DECODED_POS:
                pc.printf("New target roation:\t%.2f\n\r", targetPosition);
                break;
            case MSG_CODE_REPORT_VEL:
                pc.printf("Velocity:\t%.1f\n\r", motorVelocity / 6);
                break;
            case MSG_CODE_REPORT_POS:
                pc.printf("Position:\t%.2f\n\r", motorPosition / 6);
                break;
            default:
                pc.printf("Message %d, data 0x%016x\n\r", pMessage->code,\
                    pMessage->data);
                break;
        }
        outMessages.free(pMessage);
    }
}

// Adding message to Mail queue
void putMessage(MsgCode code, uint32_t data){
    message_t *pMessage = outMessages.alloc();
    pMessage->code = code;
    pMessage->data = data;
    outMessages.put(pMessage);
}

// Receive & decode input command
void commInFn() {
    while (1) {
        osEvent newEvent = inCharQ.get();
        uint8_t newChar = (uint8_t)newEvent.value.p;
        
        if (newChar == '\r') { // end of command
            newCmd[newCmd_index] = '\0';
            newCmd_index = 0; // reset index
            
            // decode the command
            switch(newCmd[0]) {             // check first char
                case 'K':                   // set new key
                    newKey_mutex.lock();
                    sscanf(newCmd, "K%x", &newKey);
                    putMessage(MSG_CODE_DECODED_KEY, newKey);
                    newKey_mutex.unlock();
                    break;
                case 'T':                   // set motor torque
                    sscanf(newCmd, "T%d", &motorPower);
                    putMessage(MSG_CODE_DECODED_TORQUE, motorPower);
                    break;
                case 'V':                   // set target motor velocity
                    sscanf(newCmd, "V%f", &targetVelocity);
                    putMessage(MSG_CODE_DECODED_VEL, targetVelocity);
                    break;
                case 'P':                   // set target motor position
                    sscanf(newCmd, "P%f", &targetPosition);
                    putMessage(MSG_CODE_DECODED_POS, targetPosition);
                    break;
                case 'R':                   // set target motor rotation
                    sscanf(newCmd, "R%f", &targetRotation);
                    putMessage(MSG_CODE_DECODED_POS, targetRotation);
                    break;
                    
                default:
                    break;
            }
            newCmd[0] = '0'; // clear first char
            
        } else {
            newCmd[newCmd_index] = newChar;
            if (newCmd_index++ >= MAX_CMD_LEN) // if overflow
                newCmd_index = MAX_CMD_LEN - 1;// keep overwriting last char
        }
    }
}

// Serial ISR
void serialISR() {
    uint8_t newChar = pc.getc();
    inCharQ.put((void*)newChar);
}


// For motor control thread
void motorCtrlFn() {
    Ticker motorCtrlTicker;
    motorCtrlTicker.attach_us(&motorCtrlTick,100000);
    
    // local variables
    float vel;      // local copy of motorVelocity
    float pos;      // local copy of motorPosition
    int32_t torque; // local copy of motorPower
    static uint8_t motorCtrl_counter = 0;
    static float   pos_old = 0;
    static float   E_r_old;
    
    while(1) {
        // wait for signal
        motorCtrlT.signal_wait(0x1);
        
        // measure velocity
        pos = motorPosition;        // read motorPosition ONCE
        vel = (pos - pos_old) * 10; // calculate velocity
        pos_old = pos;              // update old motor position
        motorVelocity = vel;        // write motorVelocity ONCE

        // report measured velocity every second
        if (motorCtrl_counter++ >= 10) {
            motorCtrl_counter = 0;                  // reset counter
            putMessage(MSG_CODE_REPORT_VEL, vel);   // report
            putMessage(MSG_CODE_REPORT_POS, pos);
        }
        
        // speed & position control
        float   E_r  = targetPosition - pos / 6; // access targetPosition ONCE
        
        /* speed controller
           equation: y_s = k_p(s-|v|)sgn(E_r)
           y_s: controller output (motorPower)
           k_p: empirical constant
           s  : target velocity (targetVelocity)
           v  : measured velocity (vel)
           E_r: position error */
        int32_t s    = targetVelocity * 6;      // access targetVelocity ONCE
        int32_t y_s;
        if (s == 0) y_s = MAX_PWM_PULSEWIDTH_US;        // set to max if V0
        else        y_s = (int)(10 * ( s - abs(vel) )); // calculate as normal
        if (E_r < 0) y_s = -y_s;                        // multiply by sgn(E_r)
        
        /* position controller
           equation: y_r = k_p*E_r + k_d*(d E_r/dt)
           y_r: controller output (motorPower)
           E_r: position error
           k_p,k_d: empirical constants */
        int32_t y_r = (int)(10 * E_r - 20 * (E_r - E_r_old) );
        E_r_old = E_r; // update old position error
        
        /* torque: choose y_r or y_s
           y = max(y_s, y_r), v <  0
               min(y_s, y_r), v >= 0 */
        if (((vel < 0) && (y_s > y_r)) || ((vel >= 0) && (y_s < y_r))) {
            torque = y_s;
        } else {
            torque = y_r;
        }
        
        // direction
        if (torque > 0) {
            lead = 2;
        } else {
            torque = -torque;  // torque should be positive
            lead = -2;         // reverse direction
        }
        if (torque > MAX_PWM_PULSEWIDTH_US)
            torque = MAX_PWM_PULSEWIDTH_US; // set max value
            
        // output
        motorPower = torque;   // write motorPower ONCE
        
        if (vel == 0) motorISR(); // give jolt if velocity is 0
    }
}

// ISR triggered by Ticker
void motorCtrlTick(){
    motorCtrlT.signal_set(0x1);
}
