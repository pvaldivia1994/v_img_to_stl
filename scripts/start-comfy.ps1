$ErrorActionPreference = 'Stop'
$env:HF_HOME = 'C:\_IA\cache\huggingface'
$env:TORCH_HOME = 'C:\_IA\cache\torch'
$env:PIP_CACHE_DIR = 'C:\_IA\cache\pip'
$taskPortable = 'C:\_IA\ComfyUI_windows_portable'
Set-Location $taskPortable
& "$taskPortable\python_embeded\python.exe" -s ComfyUI\main.py --windows-standalone-build --disable-auto-launch --listen 127.0.0.1 --port 8188 --lowvram --preview-method none
