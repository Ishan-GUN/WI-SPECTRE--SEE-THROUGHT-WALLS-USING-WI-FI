# WI-SPECTRE--SEE-THROUGHT-WALLS-USING-WI-FI
# WiFi Radar – Human Detection Using Signal Variations

## Overview

WiFi Radar is a real-time system that detects human movement using fluctuations in WiFi signal strength (RSSI). By analyzing how the signal changes over time, the system identifies motion patterns and estimates the number of people present in an area.

This project combines embedded systems (ESP32) with signal processing and data visualization in Python.

---

## How It Works

### 1. Signal Acquisition

An ESP32 continuously measures WiFi RSSI values and streams them over serial to a Python program.

### 2. Preprocessing

The raw signal is:

* Smoothed using Savitzky-Golay filtering
* Cleaned to reduce noise and jitter
* Normalized to remove drift

### 3. Motion Extraction

Instead of using raw values directly, the system:

* Removes slow baseline trends
* Computes signal deviation (movement component)
* Converts it into an “energy” signal representing motion intensity

### 4. Thresholding

A dynamic threshold is computed using statistical properties of the signal:

* Median + scaled standard deviation
* Adapts to environmental noise automatically

### 5. Peak Detection

Significant motion events are identified using:

* Minimum peak height
* Prominence filtering (ignores weak noise)
* Minimum width constraints

### 6. Clustering

Nearby peaks are grouped into clusters:

* Each cluster represents a single human movement event
* Prevents overcounting due to jitter

---

## Visualization

The system generates a smooth, continuous graph of the signal:

* Raw RSSI is interpolated for natural visualization
* Threshold is displayed for reference
* Focus is on clarity and interpretability rather than raw data noise
* <img width="803" height="406" alt="image" src="https://github.com/user-attachments/assets/5d675d41-3e13-41ff-addd-2af5d71c91c0" />


---

## Tech Stack

* ESP32 – WiFi signal acquisition
* Python – Data processing and visualization
* NumPy / SciPy – Signal processing
* Matplotlib – Graphing

---

## Features

* Real-time data streaming
* Adaptive noise filtering
* Robust peak detection
* Human movement estimation
* Smooth and intuitive visualization

---

## Challenges & Learnings

* RSSI data is highly noisy and quantized
* Small signal changes can appear exaggerated
* Over-smoothing removes useful information
* Proper thresholding is critical for accuracy
* Visualization must balance realism and clarity
* <img width="867" height="1156" alt="image" src="https://github.com/user-attachments/assets/acfdd6aa-2281-436b-8074-1ec5ddb84816" />


---

## Future Improvements

* Real-time live detection (no stop required)
* Multi-person tracking and separation
* Direction and speed estimation
* Machine learning-based classification
* GUI dashboard
* Real Time analytics for each person inside
* using ESP32 (with modified firmware)
* ESP32-S3 CSI firmware

---

## Key Insight

The project demonstrates that even low-resolution WiFi signals can be used for meaningful environmental sensing when combined with proper signal processing techniques.

---

## Author

Ishan Dutta | Rishit Mukherjee | Ishan Pandey | Vinayak Borkar 
Built as part of an exploration into wireless sensing and real-time signal processing.
