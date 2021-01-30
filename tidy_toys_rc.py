#!/usr/bin/env python3
# coding: Latin-1

# RC 'fallback' code for the Tidy Up The Toys challenge PiWars 2021.
# Oringinaly used for PiWars 2018 Golf Course challenge
# Amended for PS3 SHAWAN controller mapping

# Load library functions we want
import time
import os
import sys
import pygame
import ThunderBorg3
import UltraBorg3

global TB
# Re-direct our output to standard error, we need to ignore standard out to hide some nasty print statements from pygame
sys.stdout = sys.stderr

# Setup the ThunderBorg
TB = ThunderBorg3.ThunderBorg()
#TB.i2cAddress = 0x15                  # Uncomment and change the value if you have changed the board address
TB.Init()
if not TB.foundChip:
    boards = ThunderBorg3.ScanForThunderBorg()
    if len(boards) == 0:
        print("No ThunderBorg found, check you are attached :)")
    else:
        print("No ThunderBorg at address %02X, but we did find boards:" % (TB.i2cAddress))
        for board in boards:
            print("    %02X (%d) " % (board, board))
        print("If you need to change the I�C address change the setup line so it is correct, e.g.")
        print("TB.i2cAddress = 0x%02X" % (boards[0]))
    sys.exit()
# Ensure the communications failsafe has been enabled!
failsafe = False
for i in range(5):
    TB.SetCommsFailsafe(True)
    failsafe = TB.GetCommsFailsafe()
    if failsafe:
        break
if not failsafe:
    print("Board %02X failed to report in failsafe mode!" % (TB.i2cAddress))
    sys.exit()

# Start the UltraBorg
UB = UltraBorg3.UltraBorg()      # Create a new UltraBorg object
UB.Init()                       # Set the board up (checks the board is connected)

# Settings for the joystick
axisUpDown = 1                          # Joystick axis to read for up / down position
axisUpDownInverted = False              # Set this to True if up and down appear to be swapped
axisLeftRight = 0                       # Joystick axis to read for left / right position
axisLeftRightInverted = False           # Set this to True if left and right appear to be swapped
buttonSlow = 5                          # Joystick button number for driving slowly whilst held (R1)
slowFactor = 0.75                        # Speed to slow to when the drive slowly button is held, e.g. 0.5 would be half speed
buttonFastTurn = 7                      # Joystick button number for turning fast (R2)
interval = 0.00                         # Time between updates in seconds, smaller responds faster but uses more processor time
grabber_open_close = 4                  # Joystick axis to read for grabber open close position

# Power settings
voltageIn = 1.48 * 10                    # Total battery voltage to the ThunderBorg
voltageOut = 14.8 * 0.95                # Maximum motor voltage, we limit it to 95% to allow the RPi to get uninterrupted power

# Setup the power limits
if voltageOut > voltageIn:
    maxPower = 0.5
else:
    maxPower = voltageOut / float(voltageIn)

# Show battery monitoring settings
battMin, battMax = TB.GetBatteryMonitoringLimits()
battCurrent = TB.GetBatteryReading()
print("Battery monitoring settings:")
print("    Minimum  (red)     %02.2f V" % (battMin))
print("    Half-way (yellow)  %02.2f V" % ((battMin + battMax) / 2))
print("    Maximum  (green)   %02.2f V" % (battMax))
print("")
print("    Current voltage    %02.2f V" % (battCurrent))
print("")

# Setup pygame and wait for the joystick to become available
TB.MotorsOff()
TB.SetLedShowBattery(False)
TB.SetLeds(0,0,1)
os.environ["SDL_VIDEODRIVER"] = "dummy" # Removes the need to have a GUI window
pygame.init()
#pygame.display.set_mode((1,1))
print("Waiting for joystick... (press CTRL+C to abort)")
while True:
    try:
        try:
            pygame.joystick.init()
            # Attempt to setup the joystick
            if pygame.joystick.get_count() < 1:
                # No joystick attached, set LEDs blue
                TB.SetLeds(0,0,1)
                pygame.joystick.quit()
                time.sleep(0.1)
            else:
                # We have a joystick, attempt to initialise it!
                joystick = pygame.joystick.Joystick(0)
                break
        except pygame.error:
            # Failed to connect to the joystick, set LEDs blue
            TB.SetLeds(0,0,1)
            pygame.joystick.quit()
            time.sleep(0.1)
    except KeyboardInterrupt:
        # CTRL+C exit, give up
        print("\nUser aborted")
        TB.SetCommsFailsafe(False)
        TB.SetLeds(0,0,0)
        sys.exit()
print("Joystick found")
joystick.init()
TB.SetLedShowBattery(True)
ledBatteryMode = True
try:
    print("Press CTRL+C to quit")
    driveLeft = 0.0
    driveRight = 0.0
    running = True
    hadEvent = False
    upDown = 0.0
    leftRight = 0.0
    # Loop indefinitely
    while running:
        # Get the latest events from the system
        hadEvent = False
        events = pygame.event.get()
        # Handle each event individually
        for event in events:
            if event.type == pygame.QUIT:
                # User exit
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                # A button on the joystick just got pushed down
                hadEvent = True
            elif event.type == pygame.JOYAXISMOTION:
                # A joystick has been moved
                hadEvent = True
            if hadEvent:
                #Servo control here
                if joystick.get_axis(grabber_open_close):
                    # grabber servo using right joy
                    grabber_open_close = joystick.get_axis(grabber_open_close)
                    servo4 = grabber_open_close
                    UB.SetServoPosition4(servo4)
                # Read axis positions (-1 to +1)
                if axisUpDownInverted:
                    upDown = -joystick.get_axis(axisUpDown)
                else:
                    upDown = joystick.get_axis(axisUpDown)
                if axisLeftRightInverted:
                    leftRight = -joystick.get_axis(axisLeftRight)
                else:
                    leftRight = joystick.get_axis(axisLeftRight)
                # Apply steering speeds
                if not joystick.get_button(buttonFastTurn):
                    leftRight *= 0.5
                # Determine the drive power levels
                driveLeft = -upDown
                driveRight = -upDown
                if leftRight < -0.05:
                    # Turning left
                    driveLeft *= 1.0 + (2.0 * leftRight)
                elif leftRight > 0.05:
                    # Turning right
                    driveRight *= 1.0 - (2.0 * leftRight)
                # Check for button presses

                if joystick.get_button(buttonSlow):
                    driveLeft *= slowFactor
                    driveRight *= slowFactor

                # Custom speed adjustment to slow things down
                driveRight = driveRight * 0.7
                driveLeft = driveLeft * 0.5

                # Set the motors to the new speeds
                TB.SetMotor1(driveRight * maxPower)
                TB.SetMotor2(driveLeft * maxPower)
                #print(driveRight)
                #print(driveLeft)

        # Change LEDs to purple to show motor faults
        if TB.GetDriveFault1() or TB.GetDriveFault2():
            if ledBatteryMode:
                TB.SetLedShowBattery(False)
                TB.SetLeds(1,0,1)
                ledBatteryMode = False
        else:
            if not ledBatteryMode:
                TB.SetLedShowBattery(True)
                ledBatteryMode = True
        # Wait for the interval period
        time.sleep(interval)
    # Disable all drives
    TB.MotorsOff()
except KeyboardInterrupt:
    # CTRL+C exit, disable all drives
    TB.MotorsOff()
    TB.SetCommsFailsafe(False)
    TB.SetLedShowBattery(False)
    TB.SetLeds(0,0,0)
print

