import os
import re
import requests
import subprocess
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

APP_ID = "msedge-stable-win-x64"
USER_AGENT = "Microsoft Edge Update/1.3.183.29;winhttp"
EDGE_UPDATE_API = "https://msedge.api.cdp.microsoft.com/api/v2/contents/Browser/namespaces/Default/names/{0}/versions/latest?action=select"
EDGE_INSTALLER_REPO = "Bush2021/edge_installer"

def get_version_from_microsoft_api():
    headers = {"User-Agent": USER_AGENT}
    data = {
        "targetingAttributes": {
            "IsInternalUser": True,
            "Updater": "MicrosoftEdgeUpdate",
            "UpdaterVersion": "1.3.183.29",
        }
    }
    try:
        requests.packages.urllib3.disable_warnings()
        response = requests.post(
            EDGE_UPDATE_API.format(APP_ID), json=data, headers=headers, verify=False, timeout=30
        )
        if response.status_code == 200:
            content_id = response.json().get("ContentId")
            if content_id:
                return content_id.get("Version")
    except Exception as e:
        print(f"[ERROR] Microsoft API error: {e}")
    return None

def get_version_from_edge_installer():
    url = f"https://api.github.com/repos/{EDGE_INSTALLER_REPO}/releases/latest"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            tag_name = data.get('tag_name', '')
            match = re.match(r'^(\d+\.\d+\.\d+\.\d+)$', tag_name)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"[ERROR] Edge installer repo error: {e}")
    return None

def get_upstream_version():
    ms_version = get_version_from_microsoft_api()
    gh_version = get_version_from_edge_installer()
    
    if ms_version:
        print(f"[INFO] Version from Microsoft API: {ms_version}")
    if gh_version:
        print(f"[INFO] Version from edge_installer repo: {gh_version}")
    
    if ms_version and gh_version:
        if compare_versions(gh_version, ms_version) > 0:
            print(f"[INFO] Using newer version from edge_installer: {gh_version} > {ms_version}")
            return gh_version
        else:
            print(f"[INFO] Using version from Microsoft API: {ms_version}")
            return ms_version
    elif gh_version:
        print("[INFO] Using version from edge_installer repo (Microsoft API unavailable)")
        return gh_version
    elif ms_version:
        print("[INFO] Using version from Microsoft API (edge_installer unavailable)")
        return ms_version
    
    print("[ERROR] All version sources failed!")
    return None

def extract_version_from_body(body):
    patterns = [
        r'Edge\s*版本[:：]\s*(\d+\.\d+\.\d+\.\d+)',
        r'Edge\s*版本[:：]\s*([\d\.]+)',
        r'Version[:：]\s*(\d+\.\d+\.\d+\.\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, body)
        if match:
            return match.group(1)
    return None

def get_latest_release_info():
    repo = os.getenv('GITHUB_REPOSITORY')
    if not repo:
        print("[INFO] GITHUB_REPOSITORY not set, assuming local test or first run")
        return None
    
    token = os.getenv('GITHUB_TOKEN')
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
        
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 404:
            print("[INFO] No releases found.")
            return None
        resp.raise_for_status()
        data = resp.json()
        body = data.get('body', '')
        tag_name = data.get('tag_name', '')
        
        print(f"[DEBUG] Release body preview (first 500 chars):\n{body[:500]}...")
        
        version = extract_version_from_body(body)
        
        if not version and tag_name:
            tag_match = re.search(r'v?(\d+\.\d+\.\d+\.\d+)', tag_name)
            if tag_match:
                version = tag_match.group(1)
                print(f"[INFO] Version extracted from tag: {version}")
        
        if not version:
            print("[WARN] Failed to extract version from release body")
        
        return {
            'id': data.get('id'),
            'tag_name': tag_name,
            'version': version,
        }
    except Exception as e:
        print(f"[ERROR] Failed to get latest release: {e}")
        return None

def get_major_version(version):
    if not version:
        return None
    parts = version.split('.')
    if parts:
        return parts[0]
    return None

def compare_versions(v1, v2):
    if not v1 or not v2:
        return 0
    try:
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
    except ValueError as e:
        print(f"[WARN] Version comparison error: {e}")
        return 0

def is_version_upgrade(new_version, old_version):
    return compare_versions(new_version, old_version) > 0

def is_major_version_update(new_version, old_version):
    new_major = get_major_version(new_version)
    old_major = get_major_version(old_version)
    
    if new_major and old_major:
        return new_major != old_major
    return False

def is_minor_update(new_version, old_version):
    if not new_version or not old_version:
        return False
    new_major = get_major_version(new_version)
    old_major = get_major_version(old_version)
    if new_major and old_major and new_major == old_major:
        return new_version != old_version
    return False

def main():
    print("=" * 60)
    print("[INFO] Starting version check...")
    print("=" * 60)
    
    upstream_version = get_upstream_version()
    
    print(f"[INFO] Upstream Version: {upstream_version}")
    
    if not upstream_version:
        print("[ERROR] Failed to get upstream version. Forcing build to be safe.")
        env_file = os.getenv('GITHUB_ENV')
        if env_file:
            with open(env_file, 'a') as f:
                f.write("UPDATE_NEEDED=true\n")
        return

    release_info = get_latest_release_info()
    
    if release_info:
        latest_version = release_info.get('version')
        release_id = release_info.get('id')
        release_tag = release_info.get('tag_name')
        print(f"[INFO] Latest Release ID: {release_id}")
        print(f"[INFO] Latest Release Tag: {release_tag}")
        print(f"[INFO] Latest Release Version: {latest_version}")
    else:
        latest_version = None
        release_id = None
        release_tag = None
    
    update_needed = False
    
    if latest_version:
        if upstream_version != latest_version:
            if is_version_upgrade(upstream_version, latest_version):
                update_needed = True
                print(f"[INFO] Version upgrade detected: {latest_version} -> {upstream_version}")
            else:
                print(f"[WARN] Upstream version ({upstream_version}) is NOT newer than current ({latest_version}).")
                print("[WARN] This appears to be a version rollback. Skipping update.")
        else:
            print("[INFO] Version is up to date. No update needed.")
    else:
        update_needed = True
        print("[WARN] No previous version found. Will create/update release.")
    
    print("-" * 60)
    print(f"[RESULT] Update needed: {update_needed}")
    print("-" * 60)
    
    create_new_release = False
    minor_update = False
    if not release_id:
        create_new_release = True
        print("[INFO] No existing release found. Will create new release.")
    elif update_needed and is_major_version_update(upstream_version, latest_version):
        create_new_release = True
        print(f"[INFO] Major version update detected: {latest_version} -> {upstream_version}. Will create new release.")
    else:
        print("[INFO] Will update existing release.")
        if update_needed and is_minor_update(upstream_version, latest_version):
            minor_update = True
            print(f"[INFO] Minor version update detected: {latest_version} -> {upstream_version}. Will update release title.")
    
    print(f"[RESULT] Create new release: {create_new_release}")
    print(f"[RESULT] Minor update: {minor_update}")
    print("=" * 60)
    
    env_file = os.getenv('GITHUB_ENV')
    if env_file:
        with open(env_file, 'a') as f:
            f.write(f"UPDATE_NEEDED={str(update_needed).lower()}\n")
            f.write(f"UPSTREAM_VERSION={upstream_version or ''}\n")
            f.write(f"CREATE_NEW_RELEASE={str(create_new_release).lower()}\n")
            f.write(f"MINOR_UPDATE={str(minor_update).lower()}\n")
            if release_id:
                f.write(f"RELEASE_ID={release_id}\n")
            if release_tag:
                f.write(f"RELEASE_TAG={release_tag}\n")
        print("[INFO] Environment variables written successfully.")

if __name__ == '__main__':
    main()
