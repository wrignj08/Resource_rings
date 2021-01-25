# Resource_rings
This was a weekend project to display my computers (Ubuntu 20.04) CPU, RAM and GPU (NVIDIA) utilisation and temps on an external display, all the code and design files are available.
The project is powered by a Teensy 4.0 and uses four Addressable LED Ring - 16 Bit WS2812 RGB LED modules.
The display is designed to be mounted on the underside of a KOGAN 34" WQHD CURVED 21:9 ULTRAWIDE monitor.

You can check out the design and download the CAD at the link below
https://cad.onshape.com/documents/9b6b9370298a401bef62185d/w/3fc23328799e8dd97975f60a/e/fd6b8e9bd227a1a2b682e71e

The code on the Teensy is an Arduino sketch, the code on the PC is Python.


![alt text](https://github.com/wrignj08/Resource_rings/blob/main/Photos/img1.png?raw=true)
![alt text](https://github.com/wrignj08/Resource_rings/blob/main/Photos/img2.png?raw=true)


Features:<br>
CPU usage max core, purple on dial 1<br>
CPU usage max core last reading, green on dial 1<br>
CPU usage all core mean, teal on dial 1 overprints max core<br>
CPU temp, red on dial 1<br>
RAM usage, purple on dial 2<br>
RAM usage last reading, green on dial 2<br>
GPU usage, purple on dial 3<br>
GPU usage last reading, green on dial 3<br>
GPU temp, red on dial 3<br>
VRAM usage, purple on dial 4<br>
VRAM usage last reading, green dial 4<br>


Hardware:<br>
  1 x Teensy 4.0 (probibly overkill but does a good job)<br>
  https://core-electronics.com.au/teensy-4-0.html<br>
  4 x Addressable LED Ring - 16 Bit WS2812 RGB LED<br>
  https://core-electronics.com.au/cjmcu-16-bit-ws2812-5050-rgb-led-built-in-full-color-driving-lights-circle-development-board.html<br>
  6 x M3 stainless steel self tapping thread insert<br>
  https://www.aliexpress.com/item/32889542737.html<br>
  6 x M3 x 8mm bolts<br>
  https://www.aliexpress.com/item/1005001975621423.html<br>
  3D printed housing (3 files, PLA is fine)<br>
  https://github.com/wrignj08/Resource_rings/tree/main/CAD/3D%20printed%20STL%20files<br>
  Laser cut and engraved acrylic face plate<br>
  https://github.com/wrignj08/Resource_rings/tree/main/CAD/Later%20cut%20acrylic<br>
