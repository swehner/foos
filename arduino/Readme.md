# Arduino Options

This folder orgranizes the arduino design options into directories based on different Model/Configuration options for supported Arduinos.  

The available Options and their corresponding folders are listed in the table below.

Directory | Model | Description | Diagram |
| --- | ----------- | --------------------------- | ---- |
| foos_arduino | Nano | Original IR/NPN Design utilizing diagram | [schematic](../doc/schematics/foos_arduino_schem.png) |
| foos_arduino_micro | Micro | Original IR/NPN Design using a Micro instead of a Nano | [schematic](../doc/schematics/foos_arduino_micro_schem.png) |
| foos_arduino_micro_bb | Micro | Design utilizing Adafruit's Break Beam sensor | [schematic](../doc/schematics/micro_breakbeam_schem.png) |

Utilizing the [Adafruit breakbeam sensor](https://www.adafruit.com/product/2167), the use of the D9 (pwm) pin and NPN is eliminated.  Additionally, the D2/D3 pins have been freed up, incase we add support for an lcd1602/I2C, or lcd2004/I2C display.
