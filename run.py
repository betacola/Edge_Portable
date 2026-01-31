import os
import shutil
import json
import requests
import subprocess
import sys
from datetime import datetime

# Configuration
APP_ID = "msedge-stable-win-x64"
USER_AGENT = "Microsoft Edge Update/1.3.183.29;winhttp"
EDGE_UPDATE_API = "https://msedge.api.cdp.microsoft.com/api/v2/contents/Browser/namespaces/Default/names/{0}/versions/latest?action=select"
EDGE_DOWNLOAD_API = "https://msedge.api.cdp.microsoft.com/api/v1.1/internal/contents/Browser/namespaces/Default/names/{0}/versions/{1}/files?action=GenerateDownloadInfo"
SEVEN_ZIP_URL = 'https://www.7-zip.org/a/7zr.exe'
CHROME_PLUS_DIR = "chrome++"
LAST_VERSION_FILE = "last_build_version.txt"

def get_latest_version():
    """Fetch the latest Edge version from Microsoft API."""
    headers = {"User-Agent": USER_AGENT}
    data = {
        "targetingAttributes": {
            "IsInternalUser": True,
            "Updater": "MicrosoftEdgeUpdate",
            "UpdaterVersion": "1.3.183.29",
        }
    }
    try:
        # verify=False is used to match the behavior of the provided fetch.py
        response = requests.post(
            EDGE_UPDATE_API.format(APP_ID), json=data, headers=headers, verify=False
        )
        if response.status_code == 200:
            content_id = response.json().get("ContentId")
            if content_id:
                return content_id.get("Version")
    except Exception as e:
        print(f"Error checking version: {e}")
    return None

def get_download_info(version):
    """Get download URL for the specific version."""
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.post(
            EDGE_DOWNLOAD_API.format(APP_ID, version), headers=headers, verify=False
        )
        if response.status_code == 200:
            items = response.json()
            if items:
                # Sort by size (descending) to get the full installer (usually the largest file)
                items.sort(key=lambda x: x.get("SizeInBytes", 0), reverse=True)
                item = items[0]
                return {
                    "url": item.get("Url"),
                    "name": item.get("FileId"),
                    "size": item.get("SizeInBytes")
                }
    except Exception as e:
        print(f"Error getting download link: {e}")
    return None

def download_file(url, path):
    """Download a file with progress indication."""
    if os.path.exists(path):
        print(f"File {path} already exists. Skipping download.")
        return

    print(f"Downloading {url} to {path}...")
    try:
        with requests.get(url, stream=True, verify=False) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
    except Exception as e:
        print(f"Download failed: {e}")
        if os.path.exists(path):
            os.remove(path)
        sys.exit(1)

def extract_with_7z(archive, output_dir=None, seven_zip_path='7zr.exe'):
    """Extract archive using 7zr.exe."""
    cmd = [os.path.abspath(seven_zip_path), 'x', archive, '-y']
    if output_dir:
        cmd.append(f'-o{output_dir}')
    
    print(f"Extracting {archive}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Extraction failed: {result.stderr}")
        return False
    return True

def get_last_build_version():
    """Get the version of the last build from git tags."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-creatordate"], capture_output=True, text=True
        )
        tags = result.stdout.strip().split("\n")
        for tag in tags:
            if tag.startswith("v"):
                # Tag format is v120.0.2210.91 or v2026-01-23_120.0.2210.91
                # The original script used date as tag, let's see.
                # Actually, let's look at the old download.py logic again.
                return tag.lstrip("v")
    except Exception:
        pass
    return "0.0.0.0"

def main():
    requests.packages.urllib3.disable_warnings()
    
    # 1. Check for updates
    print("Checking for latest Edge version...")
    latest_version = get_latest_version()
    if not latest_version:
        print("Failed to get latest version from Microsoft API.")
        sys.exit(1)
    
    print(f"Latest Edge version found: {latest_version}")
    
    # Use git tags or local file to check version
    last_version = "0.0.0.0"
    if os.path.exists(LAST_VERSION_FILE):
        with open(LAST_VERSION_FILE, 'r') as f:
            last_version = f.read().strip()
    else:
        last_version = get_last_build_version()

    if last_version == latest_version:
        # Check for force build environment variable
        if os.environ.get('FORCE_BUILD', 'false').lower() == 'true':
            print(f"Version {latest_version} is already built, but FORCE_BUILD is set. Proceeding...")
        else:
            print(f"Version {latest_version} is already built. Skipping.")
            sys.exit(0)
    
    print("New version detected. Starting build process...")

    # 2. Prepare environment
    if not os.path.exists('7zr.exe'):
        download_file(SEVEN_ZIP_URL, '7zr.exe')
    
    work_dir = 'temp_work'
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)
    
    # 3. Download Edge Installer
    info = get_download_info(latest_version)
    if not info:
        print("Failed to get download info.")
        sys.exit(1)
        
    installer_name = info['name']
    # Ensure it ends with .exe if it doesn't (though usually FileId is just name)
    if not installer_name.endswith('.exe'):
        installer_name += '.exe'
        
    installer_path = os.path.join(work_dir, installer_name)
    download_file(info['url'], installer_path)
    
    # 4. Extract Edge Installer
    # The installer is a 7z SFX or similar.
    if not extract_with_7z(installer_path, work_dir):
        sys.exit(1)
        
    # 5. Extract MSEDGE.7z
    # After extracting installer, we expect MSEDGE.7z
    msedge_7z = None
    for root, dirs, files in os.walk(work_dir):
        for f in files:
            if f.upper() == 'MSEDGE.7Z':
                msedge_7z = os.path.join(root, f)
                break
    
    if not msedge_7z:
        print("MSEDGE.7z not found in extracted files.")
        sys.exit(1)
        
    # Extract MSEDGE.7z to work_dir
    if not extract_with_7z(msedge_7z, work_dir):
        sys.exit(1)
        
    # 6. Locate Version Directory
    # Structure: Chrome-bin/{version}/...
    chrome_bin = os.path.join(work_dir, 'Chrome-bin')
    if not os.path.exists(chrome_bin):
        print("Chrome-bin directory not found after extraction.")
        sys.exit(1)
        
    version_dir_name = None
    # Try to find the folder matching the version
    if os.path.exists(os.path.join(chrome_bin, latest_version)):
        version_dir_name = latest_version
    else:
        # Fallback: look for any version-like directory
        for item in os.listdir(chrome_bin):
            if os.path.isdir(os.path.join(chrome_bin, item)) and item[0].isdigit():
                version_dir_name = item
                break
                
    if not version_dir_name:
        print("Version directory not found in Chrome-bin.")
        sys.exit(1)
        
    print(f"Found version directory: {version_dir_name}")
    
    # 7. Build Output Structure
    # We want:
    # Edge/
    #   {version}/ (containing msedge.exe)
    #   version.dll
    #   chrome++.ini
    
    build_root = "Edge"
    if os.path.exists(build_root):
        shutil.rmtree(build_root)
    os.makedirs(build_root)
    
    # Move the version directory to Edge/
    src_version_path = os.path.join(chrome_bin, version_dir_name)
    dst_version_path = os.path.join(build_root, version_dir_name)
    shutil.move(src_version_path, dst_version_path)
    
    # 8. Setup Setdll and version.dll from local chrome++ directory
    print(f"Setting up setdll from local directory: {CHROME_PLUS_DIR}...")
    if not os.path.exists(CHROME_PLUS_DIR):
        print(f"Error: Local directory '{CHROME_PLUS_DIR}' not found.")
        sys.exit(1)
    
    # Determine architecture from APP_ID
    arch_suffix = "x64"
    if "x86" in APP_ID:
        arch_suffix = "x86"
    elif "ARM64" in APP_ID.upper():
        arch_suffix = "arm64"
    
    print(f"Detected target architecture: {arch_suffix}")

    # 8.1 version.dll (rename from version-{arch}.dll)
    version_dll_name = f'version-{arch_suffix}.dll'
    version_dll_src = os.path.join(CHROME_PLUS_DIR, version_dll_name)
    
    if os.path.exists(version_dll_src):
        shutil.copy(version_dll_src, os.path.join(build_root, 'version.dll'))
    else:
        print(f"Error: Required file '{version_dll_name}' not found in {CHROME_PLUS_DIR}.")
        sys.exit(1)

    # 8.2 chrome++.ini
    # Prioritize chrome++ directory, then project root
    dest_ini_path = os.path.join(dst_version_path, 'chrome++.ini')
    ini_src = os.path.join(CHROME_PLUS_DIR, 'chrome++.ini')
    if not os.path.exists(ini_src):
        ini_src = 'chrome++.ini' # Fallback to root
        
    if os.path.exists(ini_src):
        print(f"Using chrome++.ini from {ini_src}")
        shutil.copy(ini_src, dest_ini_path)
    else:
        print(f"Warning: chrome++.ini not found in {CHROME_PLUS_DIR} or root.")
        
    # 8.3 setdll tool (matching architecture)
    setdll_tool_name = f'setdll-{arch_suffix}.exe'
    setdll_tool_src = os.path.join(CHROME_PLUS_DIR, setdll_tool_name)
    setdll_tool = os.path.join(build_root, setdll_tool_name)
    
    if os.path.exists(setdll_tool_src):
        shutil.copy(setdll_tool_src, setdll_tool)
    else:
        print(f"Error: Required tool '{setdll_tool_name}' not found in {CHROME_PLUS_DIR}.")
        sys.exit(1)
        
    # 9. Inject DLL
    msedge_exe = os.path.join(dst_version_path, 'msedge.exe')
    version_dll = os.path.join(build_root, 'version.dll')
    
    if os.path.exists(setdll_tool) and os.path.exists(version_dll) and os.path.exists(msedge_exe):
        # Move version.dll to the same directory as msedge.exe for portability
        print("Moving version.dll to version directory for robust injection...")
        dest_version_dll = os.path.join(dst_version_path, 'version.dll')
        shutil.copy(version_dll, dest_version_dll)
        
        # 9.1 Verify Architecture with /t (as recommended in README_setdll.md)
        print(f"Verifying {msedge_exe} architecture...")
        verify_cmd = [os.path.abspath(setdll_tool), '/t', os.path.abspath(msedge_exe)]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        print(verify_result.stdout)
        
        # 9.2 Perform Injection with /d
        print(f"Injecting version.dll into {msedge_exe}...")
        inject_cmd = [
            os.path.abspath(setdll_tool),
            '/d:version.dll',
            os.path.abspath(msedge_exe)
        ]
        
        try:
            # Run from the directory of msedge.exe so "version.dll" is found by setdll validation
            target_dir = os.path.dirname(msedge_exe)
            result = subprocess.run(inject_cmd, capture_output=True, text=True, cwd=target_dir)
            if result.returncode == 0:
                print("Injection successful.")
                print(result.stdout)
            else:
                print("Injection failed.")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                sys.exit(1)
        except Exception as e:
            print(f"Injection execution error: {e}")
            sys.exit(1)
        
        # Clean up root version.dll to avoid confusion
        if os.path.exists(version_dll):
            os.remove(version_dll)

        # Remove setdll tool after use
        os.remove(setdll_tool)
    else:
        print("Skipping injection (missing setdll, version.dll, or msedge.exe).")
        
    # 10. Finalize
    # Move to build/release/Edge
    release_dir = os.path.join('build', 'release')
    os.makedirs(release_dir, exist_ok=True)
    
    final_edge_path = os.path.join(release_dir, 'Edge')
    if os.path.exists(final_edge_path):
        shutil.rmtree(final_edge_path)
    
    shutil.move(build_root, final_edge_path)
    
    # Save version info
    with open(os.path.join(final_edge_path, 'version.txt'), 'w') as f:
        f.write(latest_version)
        
    with open(LAST_VERSION_FILE, 'w') as f:
        f.write(latest_version)
        
    # Cleanup
    shutil.rmtree(work_dir, ignore_errors=True)
    
    # Output for GitHub Actions
    build_name = f'Edge_Portable_Win64_{latest_version}_{datetime.now().strftime("%Y-%m-%d")}'
    env_file = os.getenv('GITHUB_ENV')
    if env_file:
        with open(env_file, 'a') as f:
            f.write(f"BUILD_NAME={build_name}\n")
            
    print(f"Build completed successfully: {build_name}")

if __name__ == "__main__":
    main()
