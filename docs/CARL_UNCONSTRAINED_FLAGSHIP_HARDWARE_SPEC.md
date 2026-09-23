# CARL-Ω: Unconstrained Flagship Hardware & Sensor Specification
**Document Reference:** `d:\ebca\docs\CARL_UNCONSTRAINED_FLAGSHIP_HARDWARE_SPEC.md`  
**Target:** Frontier University Research Lab / Enterprise R&D  
**Budget Tier:** Unconstrained (~$3,500 – $6,000 USD / ₹3.0 Lakh – ₹5.0 Lakh INR)  
**Goal:** Zero-compromise hardware-native execution of the 8-layer EBCA cognitive stack.

---

## 1. High-Level Hardware Upgrades (Budget-Constrained vs. Unconstrained Flagship)

| Subsystem | Ultra-Frugal Budget Prototype (Sub-7.5K INR) | **Unconstrained Flagship Research Prototype** |
|---|---|---|
| **High-Level Compute** | Orange Pi 3B (0.8 TOPS NPU, 2GB RAM) | **NVIDIA Jetson Orin NX 16GB (100 TOPS AI Compute)** |
| **Neuromorphic Acceleration** | Software-simulated SNN on CPU | **BrainChip Akida AKD1000 PCIe / SpiNNaker2 Board** (Hardware-native SNN) |
| **Real-time MCU** | ESP32 (UART Serial link) | **Teensy 4.1 (600 MHz ARM Cortex-M7 with CAN-Bus)** |
| **Primary Spatial Sensor** | 12x HC-SR04 Ultrasonic Sonar Ring | **RPLIDAR S2L 360° 2D/3D LiDAR (30m range, 30,000 pts/sec)** |
| **Visual Perception** | 720p USB Web Camera | **OAK-D Pro Stereo Depth Camera** (Spatial AI + Infrared Laser Dot Projector) |
| **Tactile Sensing** | Simple micro-switch touch sites | **GelSight Mini / DIGIT Optical Tactile Skin Sensors** (Fingertip texture/force maps) |
| **Joint Actuators** | SG90 & MG996R RC Servos | **Dynamixel XM430-W210-T Smart Actuators** (RS485 Bus, current/torque feedback) |
| **Base Chassis** | 2WD BO Motor Acrylic Smart Car Kit | **CNC 7075-T6 Billet Aluminum & Carbon Fiber 4WD Chassis** |
| **Power System** | 2x 18650 Cells + LM2596 Buck Regulator | **6S 22.2V LiPo (5000mAh) + Smart Dual-Rail Active BMS System** |

---

## 2. Detailed Subsystem Architecture

### A. Compute: NVIDIA Jetson Orin NX + Hardware SNN Accelerator
* **NVIDIA Jetson Orin NX (16GB RAM)**:
  - 1024 CUDA Cores + 32 Tensor Cores delivering **100 TOPS of AI performance**.
  - Runs parallel PyTorch LSM reservoirs, real-time spatial place/grid cell maps, and 3D visual SLAM simultaneously.
* **BrainChip Akida AKD1000 SNN Coprocessor**:
  - Hardware-native Spiking Neural Network execution.
  - Executes R-STDP eligibility trace updates at zero energy cost (< 1 Watt), offloading the liquid state machine completely from the main CPU.

---

### B. Sensory Perception: LiDAR, Spatial Depth & Tactile Skin
* **RPLIDAR S2L 360° LiDAR**:
  - Replaces discrete ultrasonic sensors with continuous 30,000 samples/sec 2D/3D point clouds.
  - Feeds exact high-resolution distance boundaries directly into the 40,000-D Holographic HDC spatial memory registers (`M_spatial`).
* **OAK-D Pro Stereo Depth Camera**:
  - Features an onboard 4 TOPS Myriad X VPU for hardware stereo depth calculation and infrared laser dot projection in total darkness.
* **GelSight Mini Optical Tactile Fingertips**:
  - Uses micro-cameras behind elastomeric gel pads on the gripper fingers.
  - Measures micro-scale surface texture, slip detection, and 3D contact geometry when CARL grasps objects.

---

### C. Actuation: Dynamixel Smart Bus Servos
* **Dynamixel XM430-W210-T Actuators**:
  - Fully integrated brushless DC motor, magnetic encoder, and microcontroller communicating over a 4.5 Mbps RS485 daisy-chain bus.
  - **Full Telemetry Feedback**: Reads exact joint position, velocity, temperature, voltage, and **real-time motor current (torque)**.
  - **Motor Fatigue Integration**: Directly feeds back current and thermal accumulation to `carl_fatigue.py` to prevent joint burnout and execute organic limping dynamics under heavy loads.

---

### D. Chassis & Power Architecture
* **Chassis Fabrication**: Heavy-duty CNC machined 7075 aluminum chassis frame with carbon fiber structural plates, oil-filled shock absorbers, and all-terrain rubber tires.
* **Smart Power System**: 6S (22.2V) High-discharge LiPo battery feeding dual synchronous buck-boost power distribution boards (24V $\rightarrow$ 12V for Dynamixels, 24V $\rightarrow$ 19V for Jetson Orin).

---

## 3. Complete Unconstrained Flagship Bill of Materials (BOM)

| Subsystem / Item | Quantity | Unit Price ($ USD) | Est. Cost (₹ INR) | Primary Supplier |
| :--- | :---: | :---: | :---: | :--- |
| **NVIDIA Jetson Orin NX 16GB Module + Carrier Board** | 1 | $899.00 | ₹75,000.00 | NVIDIA / Seeed Studio |
| **RPLIDAR S2L 360° Laser Scanner** | 1 | $320.00 | ₹26,500.00 | Slamtec / Robu.in |
| **OAK-D Pro Stereo Spatial AI Camera** | 1 | $299.00 | ₹25,000.00 | Luxonis / Robu.in |
| **Dynamixel XM430-W210-T Smart Servos** (Arms/Neck) | 6 | $240.00 | ₹120,000.00 | ROBOTIS |
| **Teensy 4.1 USB/CAN Controller Board** | 1 | $35.00 | ₹3,000.00 | PJRC / Robu.in |
| **GelSight Mini Tactile Sensor Unit** | 2 | $450.00 | ₹75,000.00 | GelSight / Meta |
| **CNC Aluminum & Carbon Fiber Custom Chassis** | 1 | $350.00 | ₹29,000.00 | Custom CNC Shop |
| **Heavy-Duty Planetary Gear BO Motors + Encoders** | 4 | $45.00 | ₹15,000.00 | Pololu / Robu.in |
| **6S 22.2V 5000mAh LiPo + BMS + Power Distribution** | 1 set | $180.00 | ₹15,000.00 | GensAce / Robu.in |
| **TOTAL UNCONSTRAINED FLAGSHIP COST** | | **~$3,768.00 USD** | **~₹3,83,500 INR** | |
