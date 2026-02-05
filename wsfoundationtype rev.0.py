import datetime
import socket
import tkinter as tk
from tkinter.ttk import *
import ntplib # pyright: ignore[reportMissingImports]
import sys

# Hard License System Configuration
# Set expiry date to August 19, 2025
TARGET_EXPIRY_DATE = datetime.datetime(2026, 8, 19, 23, 59, 59)
NTP_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
    "time.windows.com",
    "time.apple.com"
]

class HardLicenseManager:
    def __init__(self):
        pass

    def _get_ntp_time(self):
        """
        Get accurate time from NTP servers.
        Tries multiple servers and falls back to system time if all fail.
        """
        for server in NTP_SERVERS:
            try:
                client = ntplib.NTPClient()
                # Request NTP response with a timeout
                response = client.request(server, version=3, timeout=5)
                # Convert NTP timestamp to datetime object
                ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
                print(f"NTP time retrieved from {server}: {ntp_time}")
                return ntp_time
            except Exception as e:
                print(f"Failed to get time from {server}: {e}")
                continue

        # If all NTP servers fail, use system time (less secure but allows offline use)
        print("Warning: Could not connect to NTP servers, using system time.")
        return datetime.datetime.now()

    def verify_license(self):
        """
        Verify if the software license is still valid based on the current date.
        Compares current time (preferably NTP) against a hardcoded expiry date.
        """
        try:
            # Get current time using the NTP time retrieval method
            current_time = self._get_ntp_time()

            # Check if license has expired
            if current_time > TARGET_EXPIRY_DATE:
                print(f"License expired on: {TARGET_EXPIRY_DATE}")
                print(f"Current time: {current_time}")
                return False

            # Calculate days remaining until expiry
            days_remaining = (TARGET_EXPIRY_DATE - current_time).days
            print(f"License is valid. Days remaining: {days_remaining}")
            print(f"License expires on: {TARGET_EXPIRY_DATE}")
            return True

        except Exception as e:
            print(f"License verification failed: {e}")
            return False

# Initialize license manager
license_manager = HardLicenseManager()

# Verify license before running the main program
if not license_manager.verify_license():
    print("\n" + "="*50)
    print("LICENSE VERIFICATION FAILED")
    print("="*50)
    print("This software license has expired.")
    print(f"Software was valid until: {TARGET_EXPIRY_DATE}")
    print("Please contact the developer for a new license.")
    print("="*50)
    input("Press Enter to exit...")
    sys.exit()

# Original code continues here...
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
local_ip_address = str(IPAddr) # Renamed 'g' for clarity
print(local_ip_address)
current_datetime = datetime.datetime.now() # Renamed 'd' for clarity
g=str(IPAddr)
w=str('192.168.1.163')
if(g!=w):
    print("License Expired")
    print(1/0)
else:
    print("Software Activated")
# creating tkinter window
# Open the output file in append mode

f= open("wsfoundationtype.txt","a")
print("This software is created by Engineer Wael Sherif Selim,email:wael.sherif.selim@gmail.com")
print("This software is created by Engineer Wael Sherif Selim,email:wael.sherif.selim@gmail.com", file=f)
print("Wsfoundationtype")
print("Wsfoundationtype", file=f)
fields ='project name', 'project id','building name','area of building in m2','weight of building in ton','bearing capacity in ton/m2','write 1 if there is swelling soil under backfilling and write 2 if there is not'
def project_name(entries):
    pr =(entries['project name'].get())
    print("project:",pr)
    print("project:",pr, file=f)
    prid=(entries['project id'].get())
    print("project id:",prid)
    print("project id:",prid, file=f)
    bu=(entries['building name'].get())
    print("building:",bu)
    print("building:",bu, file=f)
    tem=(entries['area of building in m2'].get())
    print("area of building in m2=",tem,"m2")
    print("area of building in m2=",tem,"m2", file=f)
    h=(entries['weight of building in ton'].get())
    print("weight of building in ton=",h)
    print("weight of building in ton=",h, file=f)
    i=(entries['bearing capacity in ton/m2'].get())
    swe=int((entries['write 1 if there is swelling soil under backfilling and write 2 if there is not'].get()))
    st=float(h)/float(tem)
    rat=float(st)/float(i)
    if(float(rat)<0.67 ):
        print("use isolated footing")
        print("use isolated footing", file=f)
    elif(1>float(rat)>0.67 and swe==int(2)):
        print("use raft")
        print("use raft", file=f)
    elif(1>float(rat)>0.67 and swe==int(1)):
        print("use strap beam")
        print("use strap beam", file=f)
    elif(float(rat)>=1):
        print("use piles")
        print("use piles", file=f)
    else:
        print("license expired")
        print("license expired", file=f)
def makeform(root, frame):
    entries = {}
    row = 0
    for field in fields:
        lab = tk.Label(frame,width=65,text=field+": ", anchor='w',font=("Georgia 10"))
        lab.grid(row=row, column=0)
        ent = tk.Entry(frame)
        ent.grid(row=row, column=1)
        ent.insert(0, "0")
        entries[field] = ent
        row += 1
    f1 = tk.Frame(frame)
    b1 = tk.Button(f1, padx=1, pady=1, text="Run",font=("Georgia 9"), command=(lambda e=entries: project_name(e)))
    b2 = tk.Button(f1, padx=1, pady=1, text='Quit',font=("Georgia 9"), command=root.destroy)
    f1.grid(row=row, column=0, sticky="nsew")
    b1.pack(side="left")
    b2.pack(side="left")
def onFrameConfigure(canvas):
    '''Reset the scroll region to encompass the inner frame'''
    canvas.configure(scrollregion=canvas.bbox("all"))

if __name__ == '__main__':
    root = tk.Tk()
    root.title("wsfoundationtype")
    canvas = tk.Canvas(root, width=700, borderwidth=0)
    frame = tk.Frame(canvas)
    vsb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((4,4), window=frame, anchor="nw")
    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    makeform(root, frame)
    root.mainloop()


input()
f.close()
