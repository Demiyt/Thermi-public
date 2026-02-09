# SmartTempControl

SmartTempControl is an experimental smart thermostat system that improves temperature regulation by **accounting for thermal inertia**.  
The project explores how predictive control (including a simple neural network) can reduce temperature overshoot and unnecessary energy consumption.

## Key Idea

In conventional heating systems, temperature continues to rise even after the heater is turned off due to stored heat in radiators and building structures.  
This project uses that effect **intentionally**, turning the heater off earlier to reach the target temperature more accurately.

## Project Structure

SmartTempControl/

├── Neuronetwork/

│   ├── data_normalization/

│   │   └── data.npz

│   ├── full_nn_files/

│   │   ├── neuronetwork.py

│   │   └── nn_no_normalization.py

│   ├── weights/

│   │   └── weights.npz

│   ├── main.py

│   └── training.py

├── web_server/

│   └── app.py

├── main.py

├── .gitignore

└── README.md




## Features

- Predictive temperature control
- Thermal inertia compensation
- Neural network–based decision making
- Modular architecture (control logic, ML, web interface)
- Designed for low-cost hardware (e.g. Raspberry Pi)

## How It Works (Conceptually)

1. Temperature data is collected from sensors
2. The system estimates future temperature behavior
3. Heating is switched off *before* the target temperature is reached
4. Residual heat brings the room to the desired level without overshoot

## Technologies

- Python
- NumPy
- Simple neural network (custom implementation)
- Flask (web server)
- Raspberry Pi (target platform)
- C# (mobile application)

## Status

This project is **experimental** and intended for research, prototyping, and educational purposes.

## Possible Applications

- Smart home heating systems
- Energy-efficient buildings
- Greenhouse climate control
- Industrial temperature stabilization

