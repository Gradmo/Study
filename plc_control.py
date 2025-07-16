import pymodbus
from pymodbus.client import ModbusTcpClient
import time

# Parametry połączenia z PLC
PLC_IP = "192.168.0.100"  # Adres IP symulowanego PLC
PLC_PORT = 502  # Standardowy port Modbus TCP

# Inicjalizacja klienta Modbus
client = ModbusTcpClient(PLC_IP, port=PLC_PORT)

def read_sensor():
    """Odczytuje stan czujnika obecności detalu (coil 0)"""
    try:
        result = client.read_coils(0, 1)
        return result.bits[0]
    except Exception as e:
        print(f"Błąd odczytu czujnika: {e}")
        return False

def control_motor(state):
    """Włącza (True) lub wyłącza (False) silnik (coil 1)"""
    try:
        client.write_coil(1, state)
        print(f"Silnik: {'Włączony' if state else 'Wyłączony'}")
    except Exception as e:
        print(f"Błąd sterowania silnikiem: {e}")

def main():
    print("Rozpoczynanie sterowania linią produkcyjną...")
    if client.connect():
        try:
            while True:
                # Odczyt stanu czujnika
                sensor_state = read_sensor()
                
                # Logika sterowania
                if sensor_state:
                    control_motor(True)  # Włącz silnik, jeśli detal jest obecny
                else:
                    control_motor(False)  # Wyłącz silnik, jeśli brak detalu
                
                time.sleep(1)  # Odstęp czasowy między odczytami
        except KeyboardInterrupt:
            print("Zatrzymano program")
        finally:
            client.close()
    else:
        print("Nie udało się połączyć z PLC")

if __name__ == "__main__":
    main()