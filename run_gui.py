#!/usr/bin/env python3
"""
Launcher script for the Email Inventory Processor GUI
"""

import sys
import os

# Add the noam directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'noam'))

# Import and run the GUI
from gui_app import main

if __name__ == "__main__":
    main() 