# CARL-DX Stage 6.4: ₹2,150 ($25.80) ESP32 Sim-to-Real Frugal Prototype Specification

**Document Classification:** HARDWARE EMBODIMENT & FIRMWARE SPECIFICATION  
**Target Platform:** Dual-Core Xtensa LX6 (ESP32-WROOM-32)  
**Total BOM Budget:** ₹2,150 INR (~$25.80 USD)  
**Architecture:** 2,114-Unit Continuous Attractor Neural Network (CANN) + FreeRTOS Real-Time HAL  

---

## 1. Executive Summary & Sim-to-Real Philosophy

Stage 6.4 closes the master developmental loop by transferring the cognitive architecture developed across Stages 1–6 into a **physical, low-cost autonomous robot**. 

Rather than relying on expensive $5,000+ GPU workstations or cloud compute, CARL's architecture is quantized to **Q7 Fixed-Point arithmetic** to run natively on a ₹380 ESP32 microcontroller with **33.6 KB SRAM footprint** (< 11% of available memory).

---

## 2. Complete Bill of Materials (₹2,150 Total)

| Component | Specification | Vendor / Source | Cost (INR) | Cost (USD) |
|---|---|---|---|---|
| **MCU** | ESP-WROOM-32 DevKit (Dual-Core 240MHz, 520KB SRAM, 4MB Flash) | Robu.in / Amazon | ₹380 | $4.56 |
| **IMU** | MPU-6050 6-DOF Accelerometer & Gyroscope (I2C) | Robu.in | ₹140 | $1.68 |
| **Sensors** | 3x HC-SR04 Ultrasonic Sonar Sensors (Left, Center, Right) | ElectronicsComp | ₹195 (3x ₹65) | $2.34 |
| **Driver** | DRV8833 Dual H-Bridge Motor Driver (1.5A per channel) | Robu.in | ₹120 | $1.44 |
| **Motors** | 2x N20 Micro Metal Gearmotors (6V 300 RPM) + Rubber Wheels | Robu.in | ₹420 (2x ₹210) | $5.04 |
| **Encoders** | 2x Magnetic Hall-Effect Encoders (12 CPR quadrature) | Robu.in | ₹180 | $2.16 |
| **Power** | 2S 18650 Li-ion Battery (7.4V 2200mAh) + BMS + LM2596 Buck | Robocraze | ₹490 | $5.88 |
| **Chassis** | 3mm Laser-cut Acrylic Round Chassis (140mm dia) + Caster Wheel | Local FabLab | ₹225 | $2.70 |
| **TOTAL** | **Complete Autonomous Embodied Robot** | **All Local Suppliers** | **₹2,150** | **$25.80** |

---

## 3. Hardware Architecture & Pin Interconnects

```
                      +---------------------------------------+
                      |         ESP-WROOM-32 (240 MHz)        |
                      |                                       |
                      | [Core 0: HAL 50Hz]  [Core 1: CANN 30Hz]|
                      +---------------------------------------+
                           |     |       |          |      |
            +--------------+     |       |          |      +--------------+
            |                    |       |          |                     |
     I2C (SDA=21, SCL=22)        |       |    GPIO (Trigger=5)      PWM (LEDC 20kHz)
            |                    |       |          |                     |
      [MPU-6050 IMU]             |       |     3x HC-SR04 Sonar     [DRV8833 Motor Driver]
      - Yaw Rate (gyro_z)        |       |     - Left (Echo=34)           |
      - Linear Accel             |       |     - Center (Echo=35)    +----+----+
                                 |       |     - Right (Echo=32)     |         |
                                 |       |                        [Left]    [Right]
                     Encoder_L=36+       +Encoder_R=39            Motor     Motor
```

---

## 4. FreeRTOS Dual-Core Concurrency & Memory Budget

### Dual-Core Thread Allocation
- **Core 0 (Task 1: Sensorimotor HAL @ 50 Hz):**
  - Reads raw angular rate from MPU-6050 over 400 kHz I2C DMA.
  - Measures pulse widths from 3x HC-SR04 sonars via hardware edge interrupts.
  - Updates atomic double-buffered `SensorimotorPacket_t`.
  - Dispatches PWM motor duty cycles to DRV8833 via LEDC timer.
- **Core 1 (Task 2: CARL Neuromorphic Engine @ 30 Hz):**
  - Continuous integration of 64-HD ring Continuous Attractor Neural Network (CANN).
  - 1,024-unit spatial phase toroidal projection.
  - Stage 5 "The Witness" introspective surprise filtering.
  - Drosophila PFL2 reflex steering and motor synergy arbitration.

### Memory Footprint
- 64-HD Ring Attractor (Q7): **4.16 KB**
- 1,024-Grid Sheet Torus (Q7): **5.00 KB**
- HDC 2,048-D Episodic Memory: **8.19 KB**
- FreeRTOS Task Stacks + Buffers: **16.20 KB**
- **Total SRAM Consumed:** **33.55 KB** (< 11% of ESP32's 320 KB usable SRAM).
