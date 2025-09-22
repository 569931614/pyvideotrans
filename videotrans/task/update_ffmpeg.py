"""
# License

This script for downloading/updating ffmpeg was created by Thiago Ramos.
Contact: thiagojramos@outlook.com

The ffmpeg executables (ffmpeg.exe and ffprobe.exe) are created and maintained by the FFmpeg developers.
For more information, visit the FFmpeg GitHub repository: https://github.com/BtbN/FFmpeg-Builds

This script is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the script or the use or other dealings in the script.
"""

import os
import shutil
import zipfile

import requests

# Gets the current script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Defines the destination directory and temporary directory relative to the script directory
dest_dir = os.path.join(script_dir, "..", "..", "ffmpeg")
temp_dir = os.path.join(dest_dir, "temp_ffmpeg")
os.makedirs(dest_dir, exist_ok=True)

# GitHub API URL to get the latest ffmpeg version
api_url = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
resp = requests.get(api_url, timeout=60)
resp.raise_for_status()
latest_release = resp.json()

# Prefer win64 gpl static build; fall back to any win64-gpl zip
assets = latest_release.get("assets", [])
download_url = None
asset_name = None
preferred_keywords = ["win64-gpl", ".zip"]
for a in assets:
    name = a.get("name", "")
    url = a.get("browser_download_url")
    if not url:
        continue
    if all(k in name for k in preferred_keywords) and "shared" not in name:
        download_url = url
        asset_name = name
        break

# Fallback: try master-latest naming if not found in assets
if not download_url:
    download_url = "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip"
    asset_name = "ffmpeg-master-latest-win64-gpl.zip"

# Destination path for the download
zip_path = os.path.join(dest_dir, asset_name or "ffmpeg.zip")

# Download the zip file
print(f"Downloading {asset_name or 'ffmpeg.zip'}...")
with requests.get(download_url, stream=True, timeout=300) as r:
    r.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

# Extract the contents of the zip file
print("Extracting the contents of the ffmpeg package...")
with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(temp_dir)

# Detect the extracted root directory dynamically and locate binaries
extracted_root = None
for entry in os.listdir(temp_dir):
    p = os.path.join(temp_dir, entry)
    if os.path.isdir(p) and os.path.exists(os.path.join(p, "bin")):
        extracted_root = p
        break

if not extracted_root:
    # Some archives may extract directly to bin
    extracted_root = temp_dir

ffmpeg_exe = os.path.join(extracted_root, "bin", "ffmpeg.exe")
ffprobe_exe = os.path.join(extracted_root, "bin", "ffprobe.exe")

# Checks if the files already exist and removes them if necessary
if os.path.exists(os.path.join(dest_dir, "ffmpeg.exe")):
    print("Removing existing ffmpeg.exe file...")
    os.remove(os.path.join(dest_dir, "ffmpeg.exe"))
if os.path.exists(os.path.join(dest_dir, "ffprobe.exe")):
    print("Removing existing ffprobe.exe file...")
    os.remove(os.path.join(dest_dir, "ffprobe.exe"))

# Moves the new binaries to the destination directory
print("Moving new binaries to the destination directory...")
shutil.move(ffmpeg_exe, os.path.join(dest_dir, "ffmpeg.exe"))
shutil.move(ffprobe_exe, os.path.join(dest_dir, "ffprobe.exe"))

# Clean up temporary files
print("Cleaning up temporary files...")
os.remove(zip_path)
shutil.rmtree(temp_dir)

print("Download, extraction, and replacement completed!")
