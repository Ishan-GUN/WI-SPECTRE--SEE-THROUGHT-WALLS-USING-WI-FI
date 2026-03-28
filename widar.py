import serial
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from collections import deque
import sys
import time

# Windows only - for cross-platform, use keyboard library or simpler method
try:
    import msvcrt

    PLATFORM = 'windows'
except ImportError:
    PLATFORM = 'other'
    import select
    import termios
    import tty


class LiveMotionDetector:
    """
    Real-time RSSI/CSI variance-based motion detector
    """

    def __init__(self, port='COM9', baud=115200, window_size=20):
        self.ser = serial.Serial(port, baud, timeout=0.1)  # Small timeout for non-blocking
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.variance_data = []
        self.calibration_data = []
        self.threshold = 0

    def calibrate(self, duration_seconds=3):
        """
        Calibrate by collecting baseline data with no motion
        """
        print(f"\n CALIBRATION PHASE")
        print(f"   Keep area EMPTY for {duration_seconds} seconds...")

        start_time = time.time()
        samples = 0

        while time.time() - start_time < duration_seconds:
            line = self.ser.readline().decode(errors='ignore').strip()
            if line:
                try:
                    value = float(line)
                    self.calibration_data.append(value)
                    samples += 1
                    print(f"   Sample {samples}: {value:.4f}", end='\r')
                except:
                    continue

        if len(self.calibration_data) > 0:
            # Calculate baseline noise floor
            baseline_mean = np.mean(self.calibration_data)
            baseline_std = np.std(self.calibration_data)

            # Set threshold: baseline mean + 2-3x standard deviation
            self.threshold = baseline_mean + 2.5 * baseline_std

            print(f"\n Calibration complete!")
            print(f"   Baseline mean: {baseline_mean:.4f}")
            print(f"   Baseline std: {baseline_std:.4f}")
            print(f"   Motion threshold: {self.threshold:.4f}")
            return True
        else:
            print("\n Calibration failed - no data received")
            return False

    def get_key(self):
        """
        Cross-platform key press detection
        """
        if PLATFORM == 'windows':
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8', errors='ignore').lower()
        else:
            # Unix/Linux/Mac
            import sys, select, termios, tty
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                return sys.stdin.read(1).lower()
        return None

    def live_scan(self):
        """
        Main live scanning loop
        """
        print("\n" + "=" * 50)
        print(" LIVE MOTION DETECTION")
        print("=" * 50)
        print("   Press 'q' to stop scanning")
        print("   Press 'c' to re-calibrate")
        print("-" * 50)

        motion_count = 0
        motion_detected = False

        while True:
            # Read data from serial
            line = self.ser.readline().decode(errors='ignore').strip()

            if line:
                try:
                    value = float(line)

                    # Add to sliding window
                    self.window.append(value)

                    # Calculate variance if window is full
                    if len(self.window) == self.window_size:
                        variance = np.var(self.window)
                        self.variance_data.append(variance)

                        # Motion detection
                        is_motion = variance > self.threshold

                        if is_motion and not motion_detected:
                            motion_count += 1
                            motion_detected = True
                            print(f"  MOTION DETECTED! (Event #{motion_count})")
                            print(f"   Variance: {variance:.4f} > Threshold: {self.threshold:.4f}")
                        elif not is_motion:
                            motion_detected = False

                        # Print live variance
                        status = " MOTION" if is_motion else " IDLE"
                        print(f"   Variance: {variance:.4f} | {status}", end='\r')

                except ValueError:
                    # Not a number, maybe debug output
                    if line:
                        print(f"Debug: {line[:50]}")

            # Check for user input (non-blocking)
            key = self.get_key()
            if key == 'q':
                print("\n\n  Stopping scan...")
                break
            elif key == 'c':
                print("\n\n Re-calibrating...")
                self.calibration_data = []
                self.window.clear()
                if self.calibrate():
                    continue
                else:
                    print("Calibration failed, continuing with old threshold")

            # Small delay to prevent CPU overload
            time.sleep(0.01)

        return motion_count

    def process_results(self):
        """
        Process collected variance data to detect multiple people
        """
        if len(self.variance_data) < 10:
            print("  Insufficient data for analysis")
            return []

        # Use adaptive threshold (mean + 0.5*std)
        adaptive_threshold = np.mean(self.variance_data) + 0.5 * np.std(self.variance_data)

        # Find peaks
        peaks, properties = find_peaks(
            self.variance_data,
            height=adaptive_threshold,
            distance=8,
            prominence=0.1
        )

        # Cluster nearby peaks (same person)
        clusters = []
        if len(peaks) > 0:
            current_cluster = [peaks[0]]
            for i in range(1, len(peaks)):
                if peaks[i] - peaks[i - 1] < 12:
                    current_cluster.append(peaks[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [peaks[i]]
            clusters.append(current_cluster)

        # Classify each cluster
        results = []
        for i, cluster in enumerate(clusters):
            # Get peak heights
            peak_heights = [properties['peak_heights'][j] for j in range(len(cluster))]
            avg_intensity = np.mean(peak_heights)

            # Multiple peaks within cluster = moving person
            if len(cluster) > 1:
                classification = "Active (Moving)"
            elif avg_intensity > 0.3:
                classification = "Active (Motion)"
            else:
                classification = "Stationary (Still)"

            results.append({
                'person': i + 1,
                'classification': classification,
                'peaks': cluster,
                'intensity': avg_intensity
            })

        return results

    def visualize(self, results):
        """
        Create visualization of results
        """
        if len(self.variance_data) == 0:
            print("No data to visualize")
            return

        plt.figure(figsize=(14, 8))

        # Subplot 1: Variance over time
        plt.subplot(2, 1, 1)
        plt.plot(self.variance_data, 'b-', linewidth=1.5, label='Variance')

        # Threshold line
        adaptive_threshold = np.mean(self.variance_data) + 0.5 * np.std(self.variance_data)
        plt.axhline(y=adaptive_threshold, color='r', linestyle='--',
                    label=f'Threshold ({adaptive_threshold:.3f})')

        # Mark peaks
        all_peaks = []
        for r in results:
            all_peaks.extend(r['peaks'])

        if all_peaks:
            peak_values = [self.variance_data[p] for p in all_peaks]
            plt.scatter(all_peaks, peak_values, color='orange', s=80,
                        marker='o', label='Peaks')

        plt.xlabel('Sample Number')
        plt.ylabel('Variance')
        plt.title('CSI/RSSI Variance - Motion Detection')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Subplot 2: Detected people
        plt.subplot(2, 1, 2)
        if results:
            names = [f"Person {r['person']}" for r in results]
            intensities = [r['intensity'] for r in results]
            colors = ['red' if 'Active' in r['classification'] else 'blue' for r in results]

            plt.bar(names, intensities, color=colors)
            plt.ylabel('Motion Intensity')
            plt.title('Detected People Classification')

            # Add labels
            for i, r in enumerate(results):
                plt.text(i, intensities[i] + 0.02, r['classification'],
                         ha='center', fontsize=9)
        else:
            plt.text(0.5, 0.5, 'No people detected',
                     ha='center', va='center', fontsize=14)
            plt.ylim(0, 1)

        plt.tight_layout()
        plt.show()

    def close(self):
        self.ser.close()
        print("\n🔌 Serial connection closed")


# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    print("=" * 50)
    print("🔍 Wi-ESPectre Motion Detector")
    print("=" * 50)

    # Create detector
    detector = LiveMotionDetector(port='COM9', baud=115200, window_size=20)

    # Calibration phase
    print("\n  Make sure the area is EMPTY for calibration!")
    input("Press Enter to start calibration...")

    if not detector.calibrate(duration_seconds=3):
        print("Exiting...")
        detector.close()
        exit()

    # Live scan
    print("\n Ready for motion detection!")
    input("Press Enter to start live scan...")

    motion_events = detector.live_scan()

    # Process and visualize results
    print(f"\n Motion events detected: {motion_events}")
    print("Processing data for analysis...")

    results = detector.process_results()

    # Print results
    print("\n" + "=" * 50)
    print(" FINAL RESULTS")
    print("=" * 50)

    if results:
        for r in results:
            print(f" Person {r['person']}: {r['classification']}")
            print(f"   - Motion intensity: {r['intensity']:.3f}")
            print(f"   - Peak count: {len(r['peaks'])}")
    else:
        print("No significant motion detected")

    # Visualize
    detector.visualize(results)

    # Clean up
    detector.close()
    print("\n Scan complete!")
