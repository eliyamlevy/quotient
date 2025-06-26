import pandas as pd
from openpyxl import load_workbook
import torch
from transformers import pipeline

pipeline = pipeline(
    task="text-classification",
    model="Qwen/Qwen2.5-14B-GGUF",
    device=0
)
pipeline("Please extract the following data from this text. The data needs to be caputring part number, description, and quantity. The text is as follows: 'Hi, could I please get pricing for these items below and how fast you could get them shipped to Huntington Beach location.Alkemix 5-finger Lap Shear Panels in Alclad 2024-T3 quantity 100 Alkemix 5-finger Lap Shear Panels in Bare 7075-T6 quantity 50")


# Add filler information to the DataFrame
filler_data = {
    'LINE #': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'MFCTR P/N': ['BAC1234-001', 'BAC5678-002', 'BAC9012-003', 'BAC3456-004', 'BAC7890-005',
                  'BAC2345-006', 'BAC6789-007', 'BAC0123-008', 'BAC4567-009', 'BAC8901-010'],
    'DESCRIPTION': ['Fuselage Panel Assembly', 'Wing Spar Component', 'Landing Gear Bracket', 
                   'Engine Mount Plate', 'Cockpit Instrument Panel', 'Fuel Tank Seal', 
                   'Hydraulic Line Connector', 'Electrical Harness Clamp', 'Control Surface Hinge',
                   'Avionics Mounting Bracket'],
    'QTY': [2, 1, 4, 1, 1, 8, 12, 6, 2, 3]
}

# Create new DataFrame with filler data
df_filled = pd.DataFrame(filler_data)

print("\nFilled DataFrame:")
print(df_filled.head())

print("\nFilled DataFrame Info:")
print(df_filled.info())

# Load the existing workbook to preserve all formatting
wb = load_workbook('data/Boeing MO.xlsx')
ws = wb['Input Form']  # or whatever your sheet name is

# Update only the specific cells with our data (preserving all formatting)
for i, row_data in enumerate(df_filled.values):
    row_num = 23 + i  # Start at row 22 (since we skipped 21 rows)
    
    # Update cells A, B, C, D for this row
    ws[f'A{row_num}'] = row_data[0]  # LINE #
    ws[f'B{row_num}'] = row_data[1]  # MFCTR P/N
    ws[f'C{row_num}'] = row_data[2]  # DESCRIPTION
    ws[f'D{row_num}'] = row_data[3]  # QTY

# Save the workbook (this preserves all formatting, dropdowns, colors, etc.)
wb.save('data/Boeing MO.xlsx')
print("\nFile updated successfully while preserving all formatting!")