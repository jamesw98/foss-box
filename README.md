# foss-box

A fencing scoring machine based on the [Pimoroni Interstate75W (RP2350)](https://shop.pimoroni.com/products/interstate-75) driving a 64x32 HUB75 LED matrix.

# Requirements

- Python
- [Interstate75W (RP2350)](https://shop.pimoroni.com/products/interstate-75-w?variant=54977948713339) or [Adafruit Matrix Portal S3](https://www.adafruit.com/product/5778)
  - Note: The I75W seems to be hard to find in the US currently. I was only able to find one at a local Microcenter. You can order from their site, but you'll be hit by tariffs. 
  - Note part 2: the FossBox was originally written for the I75W. Any new features will likely be written for that board first. 
- [64x32 HUB75 LED matrix panel](https://www.adafruit.com/product/2278)
- USB C cable
- 2x epee sockets (or 4mm banana sockets)

# Setup

## 1. Edit the config
Make any changes to `Config.py` that you need. Most likely you'll need to change the GPIO pins for the weapon and bells.  

I would also recommend changing `BLUETOOTH_ID` if you have more than one box  
  
## 2. Get your controller ready    
### 2a. Pimoroni Interstate75W
1. Download Pimoroni's custom MicroPython firmware for the RP2350 from their [GitHub releases page](https://github.com/pimoroni/pimoroni-pico/releases) - look for a file targeting the Interstate75W.
2. Hold the **BOOT** button and plug in USB - the board mounts as a mass storage drive.
3. Drag the `.uf2` onto the drive; it will reboot automatically.

### 2b. Matrix Portal S3  
1. Download the CircuitPython `.uf2` for the Matrix Portal S3 from [circuitpython.org](https://circuitpython.org/board/adafruit_matrix_portal_s3).
2. Double-tap the reset button - the board mounts as `MATRIXBOOT`.
3. Drag the `.uf2` onto the drive; it reboots as a `CIRCUITPY` drive.
 
## 3. Flash the FossBox code
### 3a. Pimoroni Interstate75W
1. In `src/main.py`, uncomment `PimoroniI75` and comment out `MatrixPortalS3`.
2. Copy the contents of `lib/pimoroni-i75w/` to the `/lib` directory on the board.
3. Copy all `.py` files from `src/` to the root of the board. The `src/pwa/` folder is the web remote only - it does not go on the board.

### 3b. Matrix Portal S3
1. In `src/main.py`, confirm `MatrixPortalS3` is uncommented (it is by default).
2. Copy the contents of `lib/adafruit-metro-portal-s3/` to the `/lib` directory on the board.
3. Copy the fonts from `fonts/` in this repo to a `/fonts` directory on the board (create it if it doesn't exist).
4. Copy all `.py` files from `src/` to the root of the board, **except `boot.py`** - that file is Pimoroni-specific and will cause an error on CircuitPython. The `src/pwa/` folder is the web remote only - it does not go on the board.

# Third-party credits

- **[adafruit_ble](https://github.com/adafruit/Adafruit_CircuitPython_BLE)**, **[adafruit_bitmap_font](https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font)**, **[adafruit_display_text](https://github.com/adafruit/Adafruit_CircuitPython_Display_Text)** - Copyright (c) Adafruit Industries, MIT License
- **Fonts** (`5x8.bdf`, `4x6.bdf`) - sourced from the [u8g2 font collection](https://github.com/olikraus/u8g2/tree/master/tools/font/bdf) by olikraus. Licenses vary per font; see the [u8g2 font license overview](https://github.com/olikraus/u8g2/wiki/fntlistall) for details.