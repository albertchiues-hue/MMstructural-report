#!/bin/bash
# Print all PDF files in the script's directory (two copies each)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

shopt -s nullglob
pdf_files=("$SCRIPT_DIR"/*.pdf)

if [ ${#pdf_files[@]} -eq 0 ]; then
    echo "No PDF files found in $SCRIPT_DIR"
    exit 1
fi

for pdf in "${pdf_files[@]}"; do
    echo "Printing 2 copies of: $(basename "$pdf")"
    lp -n 2 "$pdf"
done

echo "Done. Sent ${#pdf_files[@]} PDF file(s) to the printer (2 copies each)."
