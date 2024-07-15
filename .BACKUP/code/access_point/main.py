# import machine
# import time

# led = machine.Pin('LED', machine.Pin.OUT) #configure LED Pin as an output pin and create and led object for Pin class

# while True:
#   led.value(True)  #turn on the LED
#   time.sleep(1)   #wait for one second
#   led.value(False)  #turn off the LED
#   time.sleep(1)   #wait for one second

try:
    import usocket as socket        #importing socket
except:
    import socket

import network            #importing network
import gc

gc.collect()
ssid = 'HEXAPOD Projekt'                  #Set access point name 
password = 'kkkDevTeam666'      #Set your access point password

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)            #activating

while ap.active() == False:
    pass

print('Connection is successful')
print(ap.ifconfig())

def web_page():
    html = """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                h1 {
                    margin-top: 30px;
                    text-align: center;
                }

                p {
                    text-align: center;
                }

                a {
                    text-decoration: none;
                    color: royalblue;
                }
            </style>
        </head>
        <body>
            <h1>Welcome to the HEXAPOD Project Webpage!</h1>
            <p>Come visit our GitHub at: <a href="https://github.com/revalew/HEXAPOD" target="_blank">HEXAPOD</a>!</p>
        </body>
    </html>"""
    return html

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
s.bind(('', 80))
s.listen(5)

while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    print('Content = %s' % str(request))
    response = web_page()
    conn.send(response)
    conn.close()