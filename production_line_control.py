import time
import random
import logging
from threading import Thread, Lock
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from typing import List, Dict, Optional
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_line.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Configuration:
    """Singleton class for system configuration."""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Configuration, cls).__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        """Load configuration from file or set defaults."""
        self.max_speed = 100  # units per minute
        self.error_threshold = 0.05  # 5% error rate
        self.maintenance_interval = 3600  # seconds (1 hour)
        self.sensor_count = 4
        logger.info("Configuration loaded")

class MachineState:
    """Enum-like class for machine states."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"

class ProductionObserver:
    """Observer interface for production updates."""
    def update(self, state: str, metrics: Dict) -> None:
        pass

class ProductionLine:
    """Main class for production line control."""
    def __init__(self):
        self.config = Configuration()
        self.state = MachineState.IDLE
        self.production_rate = 0
        self.error_count = 0
        self.total_produced = 0
        self.uptime = 0
        self.start_time = time.time()
        self.observers: List[ProductionObserver] = []
        self._lock = Lock()
        self._running = False
        self.metrics_history = {
            'time': [],
            'production_rate': [],
            'error_count': [],
            'total_produced': []
        }

    def register_observer(self, observer: ProductionObserver) -> None:
        """Register an observer for state updates."""
        self.observers.append(observer)
        logger.info(f"Registered observer: {observer.__class__.__name__}")

    def notify_observers(self) -> None:
        """Notify all observers of state change."""
        metrics = {
            'production_rate': self.production_rate,
            'error_count': self.error_count,
            'total_produced': self.total_produced,
            'uptime': self.uptime
        }
        for observer in self.observers:
            observer.update(self.state, metrics)

    def start_production(self) -> None:
        """Start the production line."""
        with self._lock:
            if self.state != MachineState.IDLE:
                logger.warning("Cannot start: Machine not in IDLE state")
                return
            self.state = MachineState.RUNNING
            self._running = True
            logger.info("Production line started")
        self.notify_observers()
        Thread(target=self._run_production).start()

    def stop_production(self) -> None:
        """Stop the production line."""
        with self._lock:
            if self.state != MachineState.RUNNING:
                logger.warning("Cannot stop: Machine not in RUNNING state")
                return
            self._running = False
            self.state = MachineState.IDLE
            logger.info("Production line stopped")
        self.notify_observers()

    def _run_production(self) -> None:
        """Main production loop."""
        while self._running:
            try:
                self._simulate_production_cycle()
                self.uptime = time.time() - self.start_time
                
                if self.uptime >= self.config.maintenance_interval:
                    self._perform_maintenance()
                
                self._update_metrics()
                self.notify_observers()
                time.sleep(1.0)  # Simulate cycle time
                
            except Exception as e:
                logger.error(f"Production error: {str(e)}")
                self.state = MachineState.ERROR
                self.notify_observers()
                break

    def _simulate_production_cycle(self) -> None:
        """Simulate one production cycle."""
        with self._lock:
            if random.random() < self.config.error_threshold:
                self.error_count += 1
                logger.warning("Production error detected")
                if self.error_count > 5:  # Arbitrary threshold
                    raise RuntimeError("Too many errors")
            
            self.production_rate = random.uniform(0.8, 1.0) * self.config.max_speed
            self.total_produced += int(self.production_rate / 60)  # Per second

    def _perform_maintenance(self) -> None:
        """Perform scheduled maintenance."""
        with self._lock:
            self.state = MachineState.MAINTENANCE
            logger.info("Starting maintenance")
            self.notify_observers()
            time.sleep(5)  # Simulate maintenance duration
            self.error_count = 0
            self.state = MachineState.RUNNING
            logger.info("Maintenance completed")
            self.notify_observers()

    def _update_metrics(self) -> None:
        """Update metrics history for visualization."""
        current_time = time.time() - self.start_time
        self.metrics_history['time'].append(current_time)
        self.metrics_history['production_rate'].append(self.production_rate)
        self.metrics_history['error_count'].append(self.error_count)
        self.metrics_history['total_produced'].append(self.total_produced)

class Visualizer(ProductionObserver):
    """Real-time visualization of production metrics."""
    def __init__(self):
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.line_rate, = self.ax1.plot([], [], 'b-', label='Production Rate')
        self.line_errors, = self.ax2.plot([], [], 'r-', label='Error Count')
        self.ax1.set_title('Production Line Metrics')
        self.ax1.set_ylabel('Production Rate (units/min)')
        self.ax2.set_ylabel('Error Count')
        self.ax2.set_xlabel('Time (s)')
        self.ax1.legend()
        self.ax2.legend()
        self.ax1.grid(True)
        self.ax2.grid(True)

    def update(self, state: str, metrics: Dict) -> None:
        """Update visualization with new metrics."""
        self.line_rate.set_data(
            metrics['time'],
            metrics['production_rate']
        )
        self.line_errors.set_data(
            metrics['time'],
            metrics['error_count']
        )
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

    def animate(self, frame) -> tuple:
        """Animation function for matplotlib."""
        return self.line_rate, self.line_errors

    def start(self) -> None:
        """Start the visualization."""
        ani = FuncAnimation(self.fig, self.animate, interval=1000)
        plt.tight_layout()
        plt.show()

class DataLogger(ProductionObserver):
    """Log production data to JSON file."""
    def __init__(self, filename: str = "production_data.json"):
        self.filename = filename

    def update(self, state: str, metrics: Dict) -> None:
        """Log metrics to JSON file."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'metrics': metrics
        }
        try:
            with open(self.filename, 'a') as f:
                json.dump(data, f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to log data: {str(e)}")

def main():
    """Main function to run the production line simulation."""
    try:
        # Initialize components
        line = ProductionLine()
        visualizer = Visualizer()
        data_logger = DataLogger()

        # Register observers
        line.register_observer(visualizer)
        line.register_observer(data_logger)

        # Start production
        line.start_production()

        # Start visualization
        visualizer.start()

        # Run for some time
        time.sleep(30)
        
        # Stop production
        line.stop_production()

    except KeyboardInterrupt:
        logger.info("Shutting down production line")
        line.stop_production()
    except Exception as e:
        logger.error(f"System error: {str(e)}")

if __name__ == "__main__":
    main()