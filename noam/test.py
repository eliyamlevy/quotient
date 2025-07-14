import pandas as pd

def generate_dataframe():
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
    return df_filled

# td = generate_dataframe()