"""Extract VBA using olevba command line tool"""
import subprocess
import sys
import os

# Target file
file_path = r"D:\PYTHON\B7KHSX\EXCEL\THÔNG TIN NHÂN SỰ .xlsm"
output_dir = r"D:\PYTHON\B7KHSX\EXCEL\VBA_CODE"

print("STARTING VBA EXTRACTION...")
print(f"File: {file_path}")
print(f"Output: {output_dir}")

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Try to use olevba command
try:
    result = subprocess.run(
        ["olevba", "--decode", file_path],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        # Save output
        output_file = os.path.join(output_dir, "ALL_VBA_CODE.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        print(f"VBA code saved to: {output_file}")
        print("\n" + "="*60)
        print("VBA CODE CONTENT:")
        print("="*60)
        print(result.stdout)
    else:
        print(f"Error: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("Command timed out")
except FileNotFoundError:
    print("olevba not found, trying Python API...")
    
    # Fallback to Python API
    try:
        from oletools.olevba import VBA_Parser
        
        vba_parser = VBA_Parser(file_path)
        
        if vba_parser.detect_vba_macros():
            combined_file = os.path.join(output_dir, "ALL_VBA_CODE.txt")
            with open(combined_file, 'w', encoding='utf-8') as f:
                for (filename, stream_path, vba_filename, vba_code) in vba_parser.extract_macros():
                    print(f"\n{'='*60}")
                    print(f"MODULE: {vba_filename}")
                    print(f"{'='*60}")
                    print(vba_code)
                    
                    f.write(f"\n{'='*80}\n")
                    f.write(f"MODULE: {vba_filename}\n")
                    f.write(f"{'='*80}\n")
                    f.write(vba_code)
                    f.write("\n\n")
                    
                    # Also save individual files
                    safe_name = vba_filename.replace("/", "_").replace("\\", "_")
                    module_file = os.path.join(output_dir, f"{safe_name}.bas")
                    with open(module_file, 'w', encoding='utf-8') as mf:
                        mf.write(vba_code)
            
            print(f"\nAll VBA saved to: {combined_file}")
        else:
            print("No VBA macros detected")
            
        vba_parser.close()
        
    except Exception as e:
        print(f"Error with Python API: {e}")
        import traceback
        traceback.print_exc()

print("\nDONE!")
