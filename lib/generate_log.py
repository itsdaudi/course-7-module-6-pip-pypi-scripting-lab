from datetime import datetime
import os

def generate_log(data):
    # STEP 1: Validate input
    if not isinstance(data, list):
        print("Error: data must be a list")
        return

    # STEP 2: Generate a filename with today's date
    filename = f"log_{datetime.now().strftime('%Y%m%d')}.txt"

    # STEP 3: Write the log entries to a file using File I/O
    with open(filename, "w") as file:
        for entry in data:
            file.write(f"{entry}\n")

    # STEP 4: Print a confirmation message with the filename
    print(f"Log written to {filename}")


if __name__ == "__main__":
    log_data = ["User logged in", "User updated profile", "Report exported"]
    generate_log(log_data)
