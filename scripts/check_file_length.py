import sys

MAX_LINES = 500
failed = False

for filename in sys.argv[1:]:
    if not filename.endswith(".py"):
        continue
    if ".venv" in filename:
        continue
    try:
        with open(filename, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)
            if line_count > MAX_LINES:
                print(
                    f"❌ Error: {filename} has {line_count} lines "
                    f"(max allowed is {MAX_LINES}). Please modularize."
                )
                failed = True
    except Exception as e:
        print(f"Warning: Could not read {filename}: {e}")

if failed:
    sys.exit(1)
