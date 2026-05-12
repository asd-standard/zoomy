#!/bin/bash

# Launch PyZUI with native Wayland support using the PyZui-wayland conda environment
# This environment has qt6-wayland installed for proper Wayland platform support

conda run -n PyZui-wayland python /home/asd/Projects/pyzui/main.py "$@"
