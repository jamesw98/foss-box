# foss-box

A fencing scoring machine for the [Pimoroni Interstate75W (RP2350)](https://shop.pimoroni.com/products/interstate-75) driving a 64x32 HUB75 LED matrix.

## Requirements

- Python
- Interstate75W (RP2350)
- 64x32 HUB75 LED matrix panel
- USB C cable

## Setup

### 1. Flash Pimoroni MicroPython firmware

This project requires the Pimoroni MicroPython build, which includes the `hub75`, `plasma`, `picographics`, and `pimoroni_i2c` C extensions.

1. Download the latest `pimoroni-interstate75w-rp2350-*.uf2` from the [Pimoroni Pico releases page](https://github.com/pimoroni/pimoroni-pico/releases)
2. Hold the **BOOT** button on the board while plugging in USB — it will appear as a drive
3. Drag the `.uf2` file onto the drive — the board will reboot automatically

This step only needs to be done once (or when updating firmware).

### 2. Copy files to the board

Install [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html):

```
pip install mpremote
```

Then from the project directory:

```
mpremote mkdir lib
mpremote cp boot.py :boot.py
mpremote cp main.py :main.py
mpremote cp lib/interstate75.py :lib/interstate75.py
mpremote cp lib/pimoroni.py :lib/pimoroni.py
```

The board will run `main.py` automatically on power-up.
