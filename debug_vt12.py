import pandas as pd
from pathlib import Path

file = Path('downloads/FFSTOCK 14-01-2026.xlsm')

print(f"Reading {file}...")

# Read BRAN sheet
df = pd.read_excel(file, sheet_name='BRAN', header=None, skiprows=2)
print(f"BRAN sheet has {len(df)} rows")

# Column mapping for BRAN (same as stock_importer)
col_map = {
    'code_cam': 1,     # B
    'ten_cam': 2,      # C
    'kich_co_bao': 3,  # D
    'kich_co_ep': 6,   # G
    'ton_kho_kg': 13,  # N
    'ton_kho_bao': 4,  # E
    'day_on_hand': 14, # O
}

VALID_PACK_SIZES = [25, 40, 50]

# Find VT12
for idx, row in df.iterrows():
    code_cam = str(row.iloc[col_map['code_cam']]).strip() if not pd.isna(row.iloc[col_map['code_cam']]) else ''
    ten_cam = str(row.iloc[col_map['ten_cam']]).strip() if not pd.isna(row.iloc[col_map['ten_cam']]) else ''
    
    if 'VT12' in code_cam.upper():
        kich_co_bao = row.iloc[col_map['kich_co_bao']]
        ton_kho_kg = row.iloc[col_map['ton_kho_kg']]
        ton_kho_bao = row.iloc[col_map['ton_kho_bao']]
        
        print(f"\nRow {idx}: code='{code_cam}', ten='{ten_cam}'")
        print(f"  kich_co_bao={kich_co_bao} (valid: {kich_co_bao in VALID_PACK_SIZES if isinstance(kich_co_bao, (int, float)) else 'N/A'})")
        print(f"  ton_kho_kg={ton_kho_kg}, ton_kho_bao={ton_kho_bao}")
        
        # Check skip conditions
        try:
            kcb = int(float(kich_co_bao))
            if kcb not in VALID_PACK_SIZES:
                print(f"  SKIPPED: kich_co_bao {kcb} not in {VALID_PACK_SIZES}")
        except:
            print(f"  SKIPPED: kich_co_bao cannot be parsed")
