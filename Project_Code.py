import serial
import numpy as np
import matplotlib.pyplot as plt
import threading
import re
import time
from scipy.signal import find_peaks, savgol_filter
from scipy.interpolate import make_interp_spline

PORT = 'COM12'
BAUD = 115200

class Radar:
    def __init__(self):
        self.data = []
        self.running = True
        self.scanning = False
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=0)
            print("Connected")
        except:
            print("Serial error")
            self.ser = None

    def reader(self):
        buffer = ""
        while self.running:
            if self.scanning and self.ser and self.ser.in_waiting:
                raw = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                buffer += raw
                lines = buffer.split("\n")
                buffer = lines[-1]
                for line in lines[:-1]:
                    m = re.search(r"[-+]?\d+", line)
                    if m:
                        val = float(m.group())
                        self.data.append(val)
                        print(f"\r{val} | {len(self.data)}", end="")
            time.sleep(0.001)

    def analyze(self):
        self.scanning = False
        if len(self.data) < 80:
            print("\nNot enough data")
            return

        sig = np.array(self.data)

        smooth = savgol_filter(sig, 31, 3)

        smooth = savgol_filter(smooth, 21, 3)

        baseline = savgol_filter(smooth, 151, 2)
        curve = smooth - baseline

        curve = (curve - np.mean(curve)) / (np.std(curve) + 1e-6)
        energy = np.abs(curve)

        threshold = np.percentile(energy, 75)

        peaks, _ = find_peaks(energy, height=threshold, distance=25, prominence=0.8)

        clusters = []
        gap = 60
        current = []
        for p in peaks:
            if not current:
                current.append(p)
            elif p - current[-1] <= gap:
                current.append(p)
            else:
                clusters.append(current)
                current = [p]
        if current:
            clusters.append(current)

        print(f"\nDetected: {len(clusters)}")

        x = np.arange(len(smooth))

        x_dense = np.linspace(0, len(smooth)-1, len(smooth)*10)

        spline = make_interp_spline(x, smooth, k=3)
        smooth_curve = spline(x_dense)

        threshold_visual = np.mean(smooth_curve) + threshold * np.std(smooth_curve)

        plt.figure(figsize=(10,5))
        plt.plot(x_dense, smooth_curve, linewidth=2)
        plt.axhline(threshold_visual, linestyle='--')
        plt.title("Radar Signal (Clean Smooth)")
        plt.xlabel("Time")
        plt.ylabel("RSSI")
        plt.show()
        import json

        output = {
        "people_count": len(clusters),
        "signal": smooth.tolist()
        }

with open("data.json", "w") as f:
    json.dump(output, f)

    def run(self):
        threading.Thread(target=self.reader, daemon=True).start()
        print("ENTER to start/stop, x to exit")
        while self.running:
            cmd = input()
            if cmd.lower() == 'x':
                self.running = False
                break
            if not self.scanning:
                self.data = []
                self.scanning = True
                print("START")
            else:
                print("\nSTOP")
                self.analyze()

if __name__ == "__main__":
    Radar().run()
