import pandas as pd
from pathlib import Path

# Find the file
files = list(Path('downloads').glob('*14-01-2026*')) + list(Path('EXCEL').glob('*14-01-2026*'))
print("Files found:", files)

for file in files:
    if 'FFSTOCK' in str(file):
        print(f"\nReading {file}...")
        try:
            # Read BRAN sheet 
            df = pd.read_excel(file, sheet_name='BRAN', header=None, skiprows=2)
            print(f"BRAN sheet has {len(df)} rows")
            
            # Find VT12
            for idx, row in df.iterrows():
                code = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else ''
                ten = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else ''
                if 'VT12' in code.upper() or 'VT12' in ten.upper():
                    ton_bao = row.iloc[4] if not pd.isna(row.iloc[4]) else 0
                    ton_kg = row.iloc[5] if not pd.isna(row.iloc[5]) else 0
                    print(f"Found: code='{code}', ten='{ten}', ton_bao={ton_bao}, ton_kg={ton_kg}")
        except Exception as e:
            print(f"Error: {e}")
