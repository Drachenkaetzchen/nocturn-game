'''
Created on 27.12.2010

@author: felicitus
@warning This is my first python program ever. Feel free to fix, blame or burn.
'''
import usb.core
import usb.util
import array
import random
import sys
import time
import binascii


# find our device
dev = usb.core.find(idVendor=0x1235, idProduct=0x000a)

# was it found?
if dev is None:
    raise ValueError('Device not found')

cfg = dev[1]
intf = cfg[(0,0)]

ep2 = intf[0]
ep = intf[1]

# First packet (init packet?)
# Needs to be sent to make anything works
ep.write(binascii.unhexlify("b00000"))

# Second packet (unknown)
ep.write(binascii.unhexlify("28002b4a2c002e35"))

# Third packet (unknown)
ep.write(binascii.unhexlify("2a022c722e30"))

ep.write(binascii.unhexlify("7f00"))


# Sets the LED ring mode for a specific LED ring
# possible modes: 0 = Start from MIN value, 1 = Start from MAX value, 2 = Start from MID value, single direction, 3 = Start from MID value, both directions, 4 = Single Value, 5 = Single Value inverted
# The center LED ring can't be set to a mode (or I haven't found out how)
def setLEDRingMode (ring, mode):
    if ((ring > 7) | (ring < 0)):
        raise NameError("The LED ring needs to be between 0 and 7")
    
    if ((mode < 0) | (mode > 5)):
        raise NameError("The mode needs to be between 0 and 5")

    ep.write(chr(ring+0x48) + chr(mode << 4))

# Sets the LED ring value
# ring = 0-8
# value = 0-127
def setLEDRingValue (ring, value):
    if ((ring > 8) | (ring < 0)):
        raise NameError("The LED ring needs to be between 0 and 8")
    
    if ((value < 0) | (value > 127)):
        raise NameError("The LED ring value needs to be between 0 and 127")
    
    ep.write(chr(0x40+ring) + chr(value))
    
# Turns a button LED on or off
# button = 0-16
# val = 0 or 1
def setButton (but, val):
    
    if ((but < 0) | (but > 15)):
        raise NameError("Button value needs inbetween 0 and 15 (0x00 and 0x0F")
    
    if ((val == 0) | (val == 1)):
        ep.write(chr(0x70 + but) + chr(val))
        return

    raise NameError("Button value needs to be 0 or 1")



for j in range(0,16):
    setButton(j, 1)
    time.sleep(0.05)

for i in range(0,128):
    ep.write(chr(0x50) + chr(i))

for i in range(0,8):
    setLEDRingMode(i,3)
    
for i in range(0, 127, 11):
    for j in range(0,8):
        setLEDRingValue(j,i)



# Reads a key and returns either "None" or the full packet.
# The packet consists of at least 3 bytes, where the first
# byte is irrelevant, the second byte is the control ID and
# the third byte is the value
def readKey ():
    try:
        data=ep2.read(ep2.wMaxPacketSize,10)
        
        return data
    
    except usb.core.USBError:
        return
    

#----------------- GAME STUFF --------------------
def blinkStuff ():
    for j in range(0,8):
        setLEDRingValue(j,127)
        time.sleep(0.02)
        setLEDRingValue(j,0)

def resetField ():
    for j in range(0,16):
        setButton(j,0)

def newRound ():
    random.seed()
    value = random.randint(0,7)
    
    correctButtons = [0,0]
    
    if (value < 4):
        setButton(value, 1)
        correctButtons[0] = 112 + value
        setButton(7 - value, 1)
        correctButtons[1] = 119 - value
    else:
        setButton(value+4,1)
        correctButtons[0] = 116 + value
        setButton(15-(value-4),1)
        correctButtons[1] = 127 - (value-4)
        
    while True:
        ret = readKey()
        if (ret != None):
            if ((ret[1] > 111) & (ret[1] < 128)):
                if (ret[1] == correctButtons[0]):
                    return 0
                if (ret[1] == correctButtons[1]):
                    return 1
                
def updateScore (score):
    setLEDRingValue(0, score[0] * (128/11))
    setLEDRingValue(7, score[1] * (128/11))
    
def updateScore2 (score2):
    setLEDRingValue(3, score2[0] * (128/11))
    setLEDRingValue(4, score2[1] * (128/11))

def playerWin (num, val):
    if (num == 2):
        for i in range(0,4):
            setLEDRingValue(i, val)
            setLEDRingValue(i+4, val)
    else:
        for i in range(0+(4*num),4+(4*num)):
            setLEDRingValue(i, val)

def playerBlink (num):
    for j in range(0,4):
        time.sleep(0.01)
        playerWin(num,0)
        time.sleep(0.1)
        playerWin(num,127)
        resetField()
        playerWin(num,0)
                
def startGame ():
    for j in range(0,8):
        setLEDRingMode(j, 0)
        setLEDRingValue(j,0)

    score = [0,0]
    score2 = [0,0]
    
    while True:
        updateScore(score)
        updateScore2(score2)
        resetField()
        res = newRound()
        score[res] = score[res] + 1
        
        if (score[res] == 11):
            score2[res] = score2[res] + 1
            
            score[0] = 0
            score[1] = 0
            
            if (score2[0] > score2[1]):
                playerBlink(0)
            elif (score2[1] > score2[0]):
                playerBlink(1)
            else:
                playerBlink(2)
                
            if (score2[res] == 5):
                resetField()
                playerBlink(res)
                return
            
            
        
    
while True:
    ret = readKey()
    
    if (ret != None):
        if ((ret[1] > 111) & (ret[1] < 128) & (ret[2] == 127)):
            blinkStuff()
            blinkStuff()
            blinkStuff()
            resetField()
            startGame()

    
sys.exit()


