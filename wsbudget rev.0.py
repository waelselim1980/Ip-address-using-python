import matplotlib.pyplot as plt # pyright: ignore[reportMissingModuleSource]
import math
import datetime
import socket
import tkinter as tk
from tkinter.ttk import *
from time import strftime
import ntplib # pyright: ignore[reportMissingImports]
from datetime import datetime, timezone

# Function to get international date from NTP server
def get_international_date():
    """
    Queries an NTP server to get the current UTC time.
    Returns a datetime object with UTC timezone, or None if an error occurs.
    """
    try:
        # Initialize NTP client
        client = ntplib.NTPClient()
        # Query a public NTP server pool for robust time synchronization
        response = client.request("pool.ntp.org", version=3)

        # Convert the NTP timestamp (seconds since 1900) to a datetime object
        # and explicitly set its timezone to UTC.
        utc_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
        return utc_time  # Return the datetime object directly
    except Exception as e:
        print(f"Error getting international date from NTP server: {e}")
        # Return None to indicate that date retrieval failed, which can be handled
        # by the calling function to prevent the application from running.
        return None

# Main application logic
def run_application():
    """
    Contains the core logic of the application, including the license expiry check
    and the Tkinter GUI for budget calculation.
    """
    try:
        # Attempt to get the current UTC date from the NTP server
        today_utc_dt = get_international_date()

        # If date retrieval failed, print an error and exit the application
        if today_utc_dt is None:
            print("Failed to retrieve international date. Application cannot proceed.")
            return # Exit the function gracefully

        # Print the current UTC date for verification
        print(f"Today's Date (UTC): {today_utc_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Define the hard expiry date.
        # It's crucial to make this datetime object timezone-aware (UTC)
        # for accurate comparison with the NTP-derived UTC time.
        expiry_date = datetime(2026, 6, 19, 0, 0, 0, tzinfo=timezone.utc) # August 19, 2025, 00:00:00 UTC

        # Check if the current date is past the expiry date
        if today_utc_dt > expiry_date:
            print("License expired. This software is no longer usable.")
            # Exit the application gracefully if the license has expired.
            return # Exit the function

        # If the license is valid, proceed with the application's functionality
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        g = str(IPAddr)
        w=str('192.168.1.163')
        if(g!=w):
          print("License Expired")
          print(1/0)
        else:
          print("Software Activated")
          print(f"Local IP Address: {g}")

        # Open a file to append output. The file will be closed after the GUI mainloop finishes.
        f = open("wsbudget2025.txt", "a")
        print("This software is created by Engineer Wael Sherif Selim,email:wael.sherif.selim@gmail.com")
        print("This software is created by Engineer Wael Sherif Selim,email:wael.sherif.selim@gmail.com", file=f)
        print("Wsbudget2025")
        print("Wsbudget2025", file=f)

        # Define the fields for the Tkinter input form
        fields = ('project name', 'project id', 'building name', 'area of floor in m2', 'number of floors', 'write 1 if finished and write 2 if unfinished')

        def project_name(entries):
            """
            Calculates project details and costs based on user inputs from the Tkinter form.
            Prints results to console and writes them to the output file.
            """
            # Retrieve values from entry widgets
            pr = (entries['project name'].get())
            print("project:", pr)
            print("project:", pr, file=f)

            prid = (entries['project id'].get())
            print("project id:", prid)
            print("project id:", prid, file=f)

            bu = (entries['building name'].get())
            print("building:", bu)
            print("building:", bu, file=f)

            tem = (entries['area of floor in m2'].get())
            print("area of floor in m2=", tem, "m2")
            print("area of floor in m2=", tem, "m2", file=f)

            h = (entries['number of floors'].get())
            print("number of floors=", h)
            print("number of floors=", h, file=f)

            i = (entries['write 1 if finished and write 2 if unfinished'].get())

            # Validate 'finished/unfinished' input
            try:
                i_int = int(i)
                if i_int not in [1, 2]:
                    raise ValueError("Input must be 1 or 2.")
            except ValueError as ve:
                print(f"Invalid input for 'finished/unfinished': {ve}. Please enter 1 or 2.")
                print(f"Invalid input for 'finished/unfinished': {ve}. Please enter 1 or 2.", file=f)
                return # Exit the function if input is invalid

            if (i_int == 1):
                print("building is finished")
                print("building is finished", file=f)
            else:
                print("building is unfinished")
                print("building is unfinished", file=f)

            # Validate and convert numerical inputs
            try:
                tem_float = float(tem)
                h_float = float(h)
            except ValueError:
                print("Invalid input for area or number of floors. Please enter numeric values.")
                print("Invalid input for area or number of floors. Please enter numeric values.", file=f)
                return # Exit the function if numerical input is invalid

            # Calculate volume of concrete
            volc = (1.0 + h_float) * tem_float * 0.2 * 1.2
            print("volume of concrete to be poured=", float(volc), "m3")
            print("volume of concrete to be poured=", float(volc), "m3", file=f)

            # Calculate number of columns (simplified calculation)
            print("number of columns in building=", int(tem_float / 12) + 1, "columns")
            print("number of columns in building=", int(tem_float / 12) + 1, "columns", file=f)

            # Calculate material requirements
            print("cement required in ton is", 0.35 * float(volc), "tons")
            print("cement required in ton is", 0.35 * float(volc), "tons", file=f)
            print("aggregate required is", 0.8 * float(volc), "m3")
            print("aggregate required is", 0.8 * float(volc), "m3", file=f)
            print("sand required is", 0.4 * float(volc), "m3")
            print("sand required is", 0.4 * float(volc), "m3", file=f)
            print("RFT required is about", 0.15 * float(volc), "tons")
            print("RFT required is about", 0.15 * float(volc), "tons", file=f)

            # Estimated costs
            print("estimated cost for 1 m3 of concrete in 2025 is about 12850 EGP")
            print("estimated cost for 1 m3 of concrete in 2025 is about 12850 EGP", file=f)

            # Corrected cocs (cost of RC Skeleton) calculation to match the printed value
            cocs = 12850 * volc
            print("cost of RC Skeleton of building including foundations is", float(cocs), "EGP")
            print("cost of RC Skeleton of building including foundations is", float(cocs), "EGP", file=f)

            # Calculate finishing costs if building is finished
            if (i_int == 1):
                print("estimated cost of finishing in 2025 is about 6300 EGP/m2")
                print("estimated cost of finishing in 2025 is about 6300 EGP/m2", file=f)
                print("cost of finishing of 1 floor is", 6300 * tem_float, "EGP")
                print("cost of finishing of 1 floor is", 6300 * tem_float, "EGP", file=f)
                total_finishing_cost = 6300 * tem_float * h_float
                print("total cost of finishing is", total_finishing_cost, "EGP")
                print("total cost of finishing is", total_finishing_cost, "EGP", file=f)
                total_building_cost = cocs + total_finishing_cost
                print("total cost of building=", total_building_cost, "EGP")
                print("total cost of building=", total_building_cost, "EGP", file=f)
            else:
                print("total cost of unfinished building is", cocs, "EGP")
                print("total cost of unfinished building is", cocs, "EGP", file=f)

        def makeform(root_window, parent_frame):
            """
            Creates the input form using Tkinter widgets.
            """
            entries = {}
            row = 0
            for field in fields:
                lab = tk.Label(parent_frame, width=50, text=field + ": ", anchor='w', font=('georgia 10'))
                lab.grid(row=row, column=0, pady=2) # Add some padding
                ent = tk.Entry(parent_frame)
                ent.grid(row=row, column=1, pady=2) # Add some padding
                ent.insert(0, "0") # Default value
                entries[field] = ent
                row += 1

            # Create buttons frame
            button_frame = tk.Frame(parent_frame)
            # Use columnspan to center buttons or span across both columns
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            b1 = tk.Button(button_frame, padx=10, pady=5, text="Run Calculation", font=('georgia 9'), command=(lambda e=entries: project_name(e)))
            b2 = tk.Button(button_frame, padx=10, pady=5, text='Quit', command=root_window.destroy)

            b1.pack(side="left", padx=5) # Pack buttons within the button_frame
            b2.pack(side="left", padx=5)
            return entries

        def onFrameConfigure(canvas_widget):
            """
            Resets the scroll region of the canvas to encompass the inner frame,
            allowing scrolling if content exceeds visible area.
            """
            canvas_widget.configure(scrollregion=canvas_widget.bbox("all"))

        # Tkinter GUI setup
        root = tk.Tk()
        root.title("wsbudget2025")

        # Create a canvas with a scrollbar for the form
        canvas = tk.Canvas(root, width=500, borderwidth=0)
        frame = tk.Frame(canvas) # Frame to hold the input widgets
        vsb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        # Create a window on the canvas to place the frame
        canvas.create_window((4, 4), window=frame, anchor="nw")
        # Bind the frame's configure event to adjust scroll region
        frame.bind("<Configure>", lambda event, canvas_ref=canvas: onFrameConfigure(canvas_ref))

        # Create the form within the frame
        makeform(root, frame)

        # Start the Tkinter event loop
        root.mainloop()

        # Close the file after the Tkinter window is closed
        f.close()

    except Exception as e:
        # Catch any unexpected errors during the application's execution
        print(f"An unexpected error occurred during application execution: {e}")

# Entry point for the script
if __name__ == '__main__':
    run_application()

