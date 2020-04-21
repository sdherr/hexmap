# HexMap

This application creates a basic interactable hex map. It's just a proof-of-concept for using pygame that may be extended later for actual games.

## Controls

* Left-Click: Create a hex at location, or change its color if one exists
* Left-Drag: Pan
* Right-Drag: Rotate
* Scroll-Wheel: Zoom
* Scroll-Click: Re-center and reset zoom

## Setup

Assuming you already have python3 installed, we can create a simple virtual environment so you don't need to install things as root. There's only really one dependency for now, but maybe things will become more complicated.

To create:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To run (assuming the virtual environment has been sourced):
```
python hexmap.py
```
