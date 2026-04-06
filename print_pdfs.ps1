# Print all PDF files in the script's directory (two copies each)
# Usage: Right-click > "Run with PowerShell", or run: powershell -ExecutionPolicy Bypass -File print_pdfs.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pdfFiles = Get-ChildItem -Path $scriptDir -Filter "*.pdf"

if ($pdfFiles.Count -eq 0) {
    Write-Host "No PDF files found in $scriptDir"
    pause
    exit 1
}

foreach ($pdf in $pdfFiles) {
    for ($i = 1; $i -le 2; $i++) {
        Write-Host "Printing copy $i of 2: $($pdf.Name)"
        Start-Process -FilePath $pdf.FullName -Verb Print -PassThru | Out-Null
        Start-Sleep -Seconds 3
    }
}

Write-Host "`nDone. Sent $($pdfFiles.Count) PDF file(s) to the default printer (2 copies each)."
pause
