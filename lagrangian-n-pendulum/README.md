# Lagrangian N-Pendulum

A small interactive N-pendulum simulation based on Lagrangian dynamics and fourth-order Runge-Kutta (RK4) integration.

This project was originally developed as an experimental visualization and is included as a small interactive easter egg alongside the VRM21 Studios portfolio.

## Features

* Configurable number of pendulum joints
* Adjustable mass, length, angle, and angular velocity
* Configurable gravitational acceleration
* RK4 numerical integration
* Adjustable simulation time step and sub-stepping
* Joint trajectory traces
* Interactive PySide6 control interface
* Matplotlib-based real-time visualization

## Requirements

* Python 3.x
* NumPy
* SciPy
* Matplotlib
* PySide6

## Running

Install the required dependencies and run:

```bash
python lagrangian_n_pendulum.py
```

The simulation can be configured directly through the graphical interface.

## Notes

This is an experimental visualization project rather than a validated physics simulation package. The implementation is provided primarily for exploration, visualization, and educational purposes.
