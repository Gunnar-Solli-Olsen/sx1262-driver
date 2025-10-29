import csv
import numpy as np
import seaborn as sns

import matplotlib.pyplot as plt

results = ['./results.csv']

data = []
def load_data(filename):
    with open(filename, 'r', newline='') as csvfile:
        reader=csv.DictReader(csvfile)

        for row in reader:
            # print(row.items())
            data.append(row.items())
        return data

def make_surface():
    data = load_data(results[0])
    
    print(data[0])

    # Convert dict_items to real dictionaries with stripped keys/values
    cleaned = []
    for d in data:
        as_dict = {k.strip(): v.strip() for k, v in d}  # strip whitespace
        as_dict["time"] = float(as_dict["time"])
        as_dict["ping_pongs"] = int(as_dict["ping_pongs"])
        as_dict["air_speed"] = int(as_dict["air_speed"])
        as_dict["db"] = int(as_dict["db"])
        as_dict["baudrate"] = int(as_dict["baudrate"])
        cleaned.append(as_dict)

    # Extract unique airspeeds and db levels
    airspeeds = sorted(set(entry["air_speed"] for entry in cleaned))
    baudrate = sorted(set(entry["baudrate"] for entry in cleaned))

    # Initialize heatmap grid
    heatmap_data = np.zeros((len(baudrate), len(airspeeds)))

    # Fill the heatmap with ping_pongs values
    for entry in cleaned:
        i = baudrate.index(entry["baudrate"])
        j = airspeeds.index(entry["air_speed"])
        heatmap_data[i, j] = entry["ping_pongs"]

    # Plot heatmap with matplotlib
    plt.figure(figsize=(8, 6))
    im = plt.imshow(heatmap_data, cmap="plasma", aspect="auto", origin="lower")

    # Add colorbar
    cbar = plt.colorbar(im)
    cbar.set_label("Ping-Pongs")

    # Set axis ticks
    plt.xticks(ticks=np.arange(len(airspeeds)), labels=airspeeds)
    plt.yticks(ticks=np.arange(len(baudrate)), labels=baudrate)

    # Add annotations (numbers on cells)
    for i in range(len(baudrate)):
        for j in range(len(airspeeds)):
            plt.text(j, i, int(heatmap_data[i, j]), ha="center", va="center", color="white")

    plt.title("Heatmap of Ping-Pongs vs Airspeed and baudrate")
    plt.xlabel("Airspeed")
    plt.ylabel("baudrate")
    plt.show()

    # Extract x and y
    x = [entry["baudrate"] for entry in cleaned]
    y = [entry["ping_pongs"] for entry in cleaned]

    # Make scatter/line plot
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, marker="o", linestyle="-", label="Ping-Pongs")
    plt.title("Ping-Pongs vs baudrate")
    plt.xlabel("baudrate")
    plt.ylabel("Ping-Pongs")
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == '__main__':
    make_surface()