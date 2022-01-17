# Ip-address-using-python
#You can get your IP address using python by using below code, you can make it a standalone application using pyinstaller

import socket

hostname = socket.gethostname()    

IPAddr = socket.gethostbyname(hostname)  

g=str(IPAddr)

f= open("myipadress.txt","a")

print("This software is created by Eng. Wael Sherif Selim , email: wael.sherif.selim@gmail.com")

print("This software is created by Eng. Wael Sherif Selim , email: wael.sherif.selim@gmail.com", file=f)

print("ipaddress is",g)

print("ipaddress is",g, file=f)

input("press enter and copy ipaddress from myipadress.txt")

f.close()  
