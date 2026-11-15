# Native Word is used only for headless file conversion, not UI automation.
param([string]$InputFile,[string]$OutputFile)
$ErrorActionPreference='Stop'
$word=$null; $document=$null
try {
    $word=New-Object -ComObject Word.Application
    $word.Visible=$false
    $word.DisplayAlerts=0
    $document=$word.Documents.Open($InputFile,$false,$true)
    $document.ExportAsFixedFormat($OutputFile,17)
} finally {
    if($document){$document.Close(0); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)}
    if($word){$word.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
}
