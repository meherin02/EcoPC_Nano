import serial

try:
    with serial.Serial("COM3", 9600, timeout=1) as arduino:
        print("Connected. Sensor ready hote 60 seconds lagte pare.")
        print("Bondho korte Ctrl+C chapo.")

        while True:
            message = arduino.readline().decode(
                "utf-8", errors="replace"
            ).strip()

            if message:
                print(message)

except KeyboardInterrupt:
    print("\nStopped.")

except serial.SerialException as error:
    print(f"Connection error: {error}")