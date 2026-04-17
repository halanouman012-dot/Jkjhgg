import subprocess
import os
import sys
from pathlib import Path
import shutil

def read_bytes_at_offset(file_path: str, offset: int, length: int = 4) -> bytes:

    try:
        with open(file_path, "rb") as f:
            f.seek(offset)
            return f.read(length)
    except Exception as e:
        print(f"❌ Error reading bytes at offset {offset}: {e}")
        return b""

def extract_patch_entries(lib_path: str, keyword: str, patch_format: str, byte_length: int) -> int:

    if not shutil.which("strings"):
        print("❌ Error: 'strings' command not found. Please install binutils.")
        return 0

    try:
        result = subprocess.run(["strings", "-td", lib_path], capture_output=True, text=True, timeout=30)
    except Exception as e:
        print(f"❌ Error running strings: {e}")
        return 0

    libname = os.path.basename(lib_path)
    libvar = libname.replace("lib", "").replace(".so", "")

    lines = result.stdout.splitlines()
    matches = []

    keyword_lower = keyword.lower()
    for line in lines:
        if keyword_lower in line.lower():
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                try:
                    offset = int(parts[0])
                    text = parts[1]
                    matches.append((offset, text))
                except:
                    continue

    if not matches:
        print(f"❌")
        return 0

    output_file = f"{libvar}_patches.c"
    try:
        with open(output_file, "a") as out:
            for offset, text in matches:
                bytes_ = read_bytes_at_offset(lib_path, offset, byte_length)
                if not bytes_:
                    continue
                hex_bytes = " ".join(f"{b:02X}" for b in bytes_)
                if patch_format == "hex":
                    out.write(f'MemoryPatch::createWithHex("{libname}", 0x{offset:X}, "{hex_bytes}").Modify(); // {text}\n')
                elif patch_format == "macro":
                    out.write(f'PATCH_LIB("{libname}", "0x{offset:X}", "{hex_bytes}"); // {text}\n')
                else:
                    out.write(f'Tools::WriteAddr((void *) ({libvar} + 0x{offset:X}), (void *) "{hex_bytes}", {byte_length}); // {text}\n')
        print(f"✅ Extracted {len(matches)} keyword-based offsets to {output_file}")
        return len(matches)
    except Exception as e:
        print(f"❌ Error writing to {output_file}: {e}")
        return 0

def main():
    print("𓆩𝑨𝑯𝑴𝑫.ᴾᴿᴼ 🇪🇬")
    lib_path = input(" lib file path :").strip()

    if not os.path.exists(lib_path):
        print("❌ File does not exist.")
        return

    try:
        file_size = os.path.getsize(lib_path)
        if file_size == 0:
            print("❌ File is empty.")
            return
    except Exception as e:
        print(f"❌ Error checking file size: {e}")
        return

    print("\nChoose Patch Format:")
    print("1) MemoryPatch::createWithHex")
    print("2) PATCH_LIB")
    print("3) Tools::WriteAddr(...)")
    mode_input = input("Your format (1, 2 or 3): ").strip()

    if mode_input == "1":
        patch_format = "hex"
    elif mode_input == "2":
        patch_format = "macro"
    else:
        patch_format = "tools"

    while True:
        try:
            byte_length = int(input("Enter number of bytes per instruction (e.g., 4, 8): ").strip())
            if byte_length <= 0:
                raise ValueError
            break
        except ValueError:
            print("❌ Please enter a valid positive integer.")

    while True:
        word = input("Enter keyword (or type exit to quit): ").strip()
        if word.lower() in ["exit", "quit"]:
            break
        extract_patch_entries(lib_path, word, patch_format, byte_length)

if __name__ == "__main__":
    main()