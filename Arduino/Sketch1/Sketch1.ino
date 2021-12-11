#include "Command.h"
#include <eeprom.h>
#define I2CMODE
//#define HAS_SERIAL

#ifdef HAS_SERIAL
#include <SoftwareSerial.h>
#endif
#ifdef I2CMODE
#include "Wire/Wire.h"
#endif

#define PMOTOR1 PIN_PD5
#define PMOTOR3 PIN_PD6
#define PMOTOR2 PIN_PB1
#define PMOTOR4 PIN_PB2


#define PDATA PIN_PB0
#define PCLK PIN_PC7
#define PLATCH PIN_PD7
#define PFIRE PIN_PB4

#define PSENSE_PAPER PIN_PB3
#define PSENSE_PRESS PIN_PB7

byte btn_led_pins[] = { PIN_PD0, PIN_PD1, PIN_PD2, PIN_PD3, PIN_PD4, PIN_PB6 };

#define PBUZZER PIN_PB5
#define PPAPERBTN PIN_PC2

#define NO_PAPER_AFTER_INTERACTION_FOR_MS 1000
#define LED_BLINK_INTERVAL 500

void setup_aux_pins() {

    for (byte i = 0; i < sizeof(btn_led_pins); ++i) {
        digitalWrite(btn_led_pins[i], LOW);
        pinMode(btn_led_pins[i], OUTPUT);
    }
    digitalWrite(PBUZZER, LOW);
    pinMode(PBUZZER, OUTPUT);
    pinMode(PPAPERBTN, INPUT_PULLUP);
}


#ifdef HAS_SERIAL
#define PRX PIN_PD0
#define PTX PIN_PD1
#endif

#define FIRE_DELAY 1
#define MAX_BURNING_COUNT 32

byte line_data[16];
//byte rot[8] = { 0x09,0x01,0x03,0x02,0x06,0x04,0x0c,0x08 };
byte rot[4] = { 0x01,0x02,0x04,0x08 };
byte motor_pins[] = { PMOTOR1, PMOTOR2, PMOTOR3, PMOTOR4 };
int motor_step_delay = 10;
int motor_ptr = 0;
volatile int steps_remain = 0;
unsigned long long next_step_at = 0;
unsigned long long last_op = 0;
byte led_status = 0;
byte led_blink = 0;
uint32_t next_led_blink = 0;
byte just_reset = 1;
#ifdef HAS_SERIAL
SoftwareSerial serial(PRX, PTX);
#endif
#ifdef I2CMODE
TwoWire pi;
byte i2c_outgoing[4] = { 7, 8, 9, 10 };
byte i2c_incoming[20] = { 0 };
volatile byte i2c_received = 0;
volatile int8_t i2c_tosend = 0;
volatile int i2c_received_ptr = 0;
void write_i2c(byte data) {
    i2c_outgoing[0] = data;
    i2c_tosend = 1;
}
void write_i2c(const byte* data, byte length) {
    memcpy(i2c_outgoing, data, length);
    i2c_tosend = length;
}

void on_i2crequest() {
    if (i2c_tosend > 0) {
        pi.write(i2c_outgoing, i2c_tosend);
    }
    i2c_tosend = 0;
}

void on_i2creceive(int num_bytes) {
    pi.readBytes(i2c_incoming, num_bytes);
    i2c_received = num_bytes;
#ifdef HAS_SERIAL
    serial.println("DATA");
#endif
}
#endif

void setup() {
#ifdef I2CMODE
    pi.begin(42);
    pi.onRequest(on_i2crequest);
    pi.onReceive(on_i2creceive);
#endif
#ifdef HAS_SERIAL
    serial.begin(38400);
#endif
    pinMode(PDATA, OUTPUT);
    pinMode(PCLK, OUTPUT);
    digitalWrite(PLATCH, HIGH);
    pinMode(PLATCH, OUTPUT);
    pinMode(PFIRE, OUTPUT);
#ifdef HAS_SERIAL
    serial.println("Hi");
#endif
    setup_aux_pins();
}
void move_motor(int steps) {
    steps_remain = steps;
    pinMode(PMOTOR1, OUTPUT);
    pinMode(PMOTOR2, OUTPUT);
    pinMode(PMOTOR3, OUTPUT);
    pinMode(PMOTOR4, OUTPUT);
}

void motor_step() {
    if (steps_remain == 0 || millis() < next_step_at) {
        return;
    }
    int8_t dir = steps_remain > 0 ? 1 : -1;
    motor_ptr += dir;
    if (motor_ptr == sizeof(rot)) {
        motor_ptr = 0;
    }
    if (motor_ptr == -1) {
        motor_ptr = sizeof(rot) - 1;
    }
    steps_remain -= dir;
    for (int i = 0; i < 4; ++i) {
        digitalWrite(motor_pins[i], rot[motor_ptr] & (1 << i) ? HIGH : LOW);
    }
    if (steps_remain == 0) {
        pinMode(PMOTOR1, INPUT);
        pinMode(PMOTOR2, INPUT);
        pinMode(PMOTOR3, INPUT);
        pinMode(PMOTOR4, INPUT);
    }
    next_step_at = millis() + motor_step_delay;
}

void paper_step() {
    if (digitalRead(PPAPERBTN) == LOW && millis() > last_op + NO_PAPER_AFTER_INTERACTION_FOR_MS) {
        move_motor(10);
    }
}



bool fire_chunk(int fire_delay) {
    int num_ones = 0;
    byte tosend[16] = { 0 };
    for (int i = 0; i < 16 && num_ones < MAX_BURNING_COUNT; ++i) {
        byte& cur = line_data[i];
        for (int bit = 0; bit < 8 && num_ones < MAX_BURNING_COUNT; ++bit) {
            byte mask = 1 << bit;
            if (cur & mask) {
                ++num_ones;
                tosend[i] |= mask;
                cur &= ~mask;
            }
        }
    }
    if (num_ones) {
        for (int i = 0; i < 16; ++i) {
            shiftOut(PDATA, PCLK, MSBFIRST, tosend[i]);
        }
        digitalWrite(PLATCH, LOW);
        delay(1);
        digitalWrite(PLATCH, HIGH);
        delay(1);
        digitalWrite(PFIRE, HIGH);
        delayMicroseconds(fire_delay);
        digitalWrite(PFIRE, LOW);
        return true;
    }
    return false;
}


void fire(int32_t delay) {
    while (fire_chunk(delay));
}

void scroll(int32_t steps) {
    move_motor(steps);
}


void line(byte* data) {
    memcpy(line_data, data, 16);
}

#ifndef I2CMODE
int ser_read() {
    int val = serial.read();
    while (val == -1) {
        val = serial.read();
    }
    return val;
}
#else


int ser_read() {
    while (!i2c_received) {

    }
    int data = i2c_incoming[i2c_received_ptr++];
    if (i2c_received_ptr == i2c_received) {
        i2c_received = i2c_received_ptr = 0;
    }
#ifdef HAS_SERIAL
    serial.print("Got from i2c: ");
    serial.println(data);
#endif
    return data;
}
#endif

void send_ok() {
#ifdef HAS_SERIAL
    serial.println("OK");
#endif
#ifdef I2CMODE
    write_i2c(1);
#endif
}

void send_err() {
#ifdef HAS_SERIAL
    serial.println("ERR");
#endif
#ifdef I2CMODE
    write_i2c(99);
#endif
}

class Siren {
#define FREQ_MULTIPLIER 1.059463094359
#define DURATION_MULTIPLIER 100
    byte freq;
    byte freq2;
    byte duration;
    byte freq_duration;
    uint32_t run_until = 0;
    uint32_t next_freq_switch_at = 0;
    inline void set_freq() {
        if (freq == 0) {
            noTone(PBUZZER);
        }
        else {
            tone(PBUZZER, 440 * pow(FREQ_MULTIPLIER, freq - 128));
        }
    }
    inline void stop_sound() {
        noTone(PBUZZER);
    }
public:
    void set(byte freq1, byte freq2, byte duration, byte freq_duration) {
        this->freq = freq1;
        this->freq2 = freq2;
        this->freq = freq1;
        this->duration = duration;
        this->freq_duration = freq_duration;
        run_until = duration ? millis() + duration * DURATION_MULTIPLIER : 0xFFFFFFFF;
        next_freq_switch_at = freq_duration ? millis() + freq_duration * DURATION_MULTIPLIER : 0xFFFFFFFF;
        set_freq();
    }
    void step() {
        if (millis() > run_until) {
            stop_sound();
            return;
        }
        if (millis() > next_freq_switch_at) {
            freq = freq ^ freq2;
            freq2 = freq ^ freq2;
            freq = freq ^ freq2;
            set_freq();
            next_freq_switch_at = millis() + freq_duration * DURATION_MULTIPLIER;
        }
    }
};

Siren siren;

void led_step() {
    if (millis() > next_led_blink) {
        led_status ^= led_blink;
        next_led_blink = millis() + LED_BLINK_INTERVAL;
    }
    for (int i = 0; i < 6; ++i) {
        digitalWrite(btn_led_pins[i], led_status & (1 << i) ? HIGH : LOW);
    }

}

bool execute_i2cc(Command & cmd, byte* data, byte length) {
    switch (cmd) {
    case Command::Fire:
        last_op = millis();
        fire(FIRE_DELAY);
        send_ok();
        return true;
    case Command::FireDelay:
        if (length == 4) {
            last_op = millis();
            fire(*(int32_t*)data);
            send_ok();
            return true;
        }
        return false;
    case Command::Scroll:
        if (length == 4) {
            last_op = millis();
            scroll(*(int32_t*)data);
            send_ok();
            return true;
        }
        return false;
    case Command::Line:
        if (length == 16) {
            last_op = millis();
            line(data);
            send_ok();
            return true;
        }
        return false;
    case Command::Speed:
        if (length == 4) {
            int spd = *(uint32_t*)data;
            motor_step_delay = spd;
            send_ok();
            return true;
        }
        return false;
    case Command::Buzz:
        if (length == 4) {
            byte freq1 = data[0];
            byte freq2 = data[1];
            byte duration = data[2];
            byte freq_duration = data[3];
            siren.set(freq1, freq2, duration, freq_duration);
            send_ok();
            return true;
        }
        return false;
    case Command::LEDs:
        if (length == 2) {
            led_status = data[0];
            led_blink = data[1];
            send_ok();
            return true;
        }
        return false;
    case Command::Status:
        if (length == 1) {
            byte sendme[] = { (!digitalRead(PSENSE_PAPER)) | (digitalRead(PSENSE_PRESS) << 1) | (just_reset << 2), 1 };
            // Reset the just_reset flag if pi confirmed the reset flag
            just_reset &= ~data[0];
            write_i2c(sendme, 2);
            return true;
        }
        return false;
    }
    return false;
}

void i2c_step() {
    if (!i2c_received) {
        return;
    }
    int magic = ser_read();
    if (magic != 42) {
        send_err();
        return;
    }
    auto cmd = (Command)ser_read();
    byte length = ser_read();
    if (length > 16) {
        send_err();
        return;
    }
    byte data[16];
    for (int i = 0; i < length; ++i) {
        data[i] = ser_read();
    }
    //serial.print("Have cmd ");
    //serial.print((int)cmd);
    //serial.print(" with length ");
    //serial.print(length);
    //serial.print(" and data ");
    //for (int i = 0; i < length; ++i) {
    //    serial.print((int)data[i]);
    //    serial.print(' ');
    //}
    //serial.println();

    bool ok = execute_i2cc(cmd, data, length);
    if (!ok) {
        send_err();
    }

}
void(*resetFunc) (void) = 0;
void loop() {
    if (millis() > 0x80000000 && millis() > last_op + NO_PAPER_AFTER_INTERACTION_FOR_MS) {
        resetFunc();
    }
    i2c_step();
    motor_step();
    paper_step();
    siren.step();
    led_step();
}
