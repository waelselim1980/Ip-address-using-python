import datetime
import socket
import tkinter as tk
from tkinter.ttk import *
import ntplib # pyright: ignore[reportMissingImports]
import sys
import matplotlib.pyplot as plt # pyright: ignore[reportMissingModuleSource]
import math
import datetime
import socket
import tkinter as tk
from tkinter.ttk import * 
from time import strftime
import bs4 as bs # pyright: ignore[reportMissingImports]
import urllib.request
import re
import nltk # pyright: ignore[reportMissingImports]
import os, os.path

# This is to get the directory that the program 
# is currently running in.
import nltk.data # pyright: ignore[reportMissingImports]
# Hard License System Configuration
# Set expiry date to August 19, 2025
hostname = socket.gethostname()    
IPAddr = socket.gethostbyname(hostname)  
g=str(IPAddr)
w=str("192.168.1.163")
if(g!=w): # pyright: ignore[reportUndefinedVariable]
    print("License Expired")
    print(1/0)
else:
    print("Software Activated")
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
f= open("wssummary2025.txt","a")    
print("This software is created by Engineer Wael Sherif Selim to summarize any online text, email;wael.sherif.selim@gmail.com")
print("This software is created by Engineer Wael Sherif Selim to summarize any online text, email;wael.sherif.selim@gmail.com", file=f)
nltk.download('punkt')
nltk.download('stopwords')
fields='enter article title','enter url name'
def enter_article_title(entries):
    tit=(entries['enter article title'].get())
    urlin=(entries['enter url name'].get())
    scraped_data = urllib.request.urlopen(urlin)
    article = scraped_data.read()

    parsed_article = bs.BeautifulSoup(article,'lxml')

    paragraphs = parsed_article.find_all('p')

    article_text = ""

    for p in paragraphs:
      article_text += p.text
    article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
    article_text = re.sub(r'\s+', ' ', article_text)
    formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )
    formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
    sentence_list = nltk.sent_tokenize(article_text)
    stopwords = nltk.corpus.stopwords.words('english')

    word_frequencies = {}
    for word in nltk.word_tokenize(formatted_article_text):
      if word not in stopwords:
        if word not in word_frequencies.keys():
            word_frequencies[word] = 1
        else:
            word_frequencies[word] += 1
    maximum_frequncy = max(word_frequencies.values())

    for word in word_frequencies.keys():
      word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)
    sentence_scores = {}
    for sent in sentence_list:
      for word in nltk.word_tokenize(sent.lower()):
        if word in word_frequencies.keys():
            if len(sent.split(' ')) < 30:
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word]
                else:
                    sentence_scores[sent] += word_frequencies[word]
    import heapq
    summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)

    summary = ' '.join(summary_sentences)
    if(d>ad): # pyright: ignore[reportUndefinedVariable]
     print("expired")
    else:
     print(tit)
     print(tit, file=f)
     print(summary)
     print((summary), file=f)
def makeform(root, frame):
    entries = {}
    row = 0
    for field in fields:
        lab = tk.Label(frame,width=115,text=field+": ", anchor='w')
        lab.grid(row=row, column=0)
        ent = tk.Entry(frame)
        ent.grid(row=row, column=1)
        ent.insert(0, "0")
        entries[field] = ent
        row += 1
    f1 = tk.Frame(frame)
    b1 = tk.Button(f1, padx=1, pady=1, text="Run", command=(lambda e=entries: enter_article_title(e)))
    b2 = tk.Button(f1, padx=1, pady=1, text='Quit', command=root.destroy)
    f1.grid(row=row, column=0, sticky="nsew")
    b1.pack(side="left")
    b2.pack(side="left")
def onFrameConfigure(canvas):
    '''Reset the scroll region to encompass the inner frame'''
    canvas.configure(scrollregion=canvas.bbox("all"))
  
if __name__ == '__main__':
    root = tk.Tk()
    root.title("wssummary")
    canvas = tk.Canvas(root, width=950, borderwidth=0)
    frame = tk.Frame(canvas)
    vsb = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((4,4), window=frame, anchor="nw")
    frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))
    makeform(root, frame)
    root.mainloop()
input("")
f.close() 
