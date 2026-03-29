import serial
import numpy as np
import matplotlib.pyplot as plt
import threading
import re
import time
import json
from scipy.signal import find_peaks, savgol_filter

PORT = 'COM12'
BAUD = 115200


def safe_savgol(data, max_window, poly):
    n = len(data)
    if n < 5:
        return data

    window = min(max_window, n if n % 2 == 1 else n - 1)

    if window % 2 == 0:
        window -= 1

    if window < 5:
        return data

    return savgol_filter(data, window, poly)


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
                    match = re.search(r"[-+]?\d+", line)
                    if match:
                        val = float(match.group())
                        self.data.append(val)
                        print(f"\r{val} | {len(self.data)}", end="")

            time.sleep(0.001)

    def analyze(self):
        self.scanning = False

        if len(self.data) < 60:
            print("\nNot enough data")
            return

        sig = np.array(self.data)

        smooth = safe_savgol(sig, 31, 3)
        smooth = safe_savgol(smooth, 21, 3)

        baseline = safe_savgol(smooth, 151, 2)
        curve = smooth - baseline

        curve = (curve - np.mean(curve)) / (np.std(curve) + 1e-6)
        energy = np.abs(curve)

        threshold = np.median(energy) + 1.2 * np.std(energy)

        peaks, _ = find_peaks(
            energy,
            height=threshold,
            distance=25,
            prominence=0.8
        )

        clusters = []
        gap = 50
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

        count = len(clusters)

        print(f"\nDetected: {count}")

        
        # 🔥 GRAPH
        plt.figure(figsize=(10, 5))
        plt.plot(smooth, linewidth=2)
        plt.title("Radar Signal")
        plt.xlabel("Time")
        plt.ylabel("RSSI")
        plt.show()
        # 🔥 SAVE FOR WEBSITE
        output = {
        "people_count": int(count),
        "signal": [float(x) for x in smooth]
        }

        with open(r"C:\Users\Ishan\OneDrive\Documents\Website\data.json", "w") as f:
            json.dump(output, f)

    def run(self):
        threading.Thread(target=self.reader, daemon=True).start()

        print("Press ENTER to start/stop, x to exit")

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