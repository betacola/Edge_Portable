import os
import re
import requests
import subprocess

APP_ID = "msedge-stable-win-x64"
USER_AGENT = "Microsoft Edge Update/1.3.183.29;winhttp"
EDGE_UPDATE_API = "https://msedge.api.cdp.microsoft.com/api/v2/contents/Browser/namespaces/Default/names/{0}/versions/latest?action=select"

def get_upstream_version():
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
            EDGE_UPDATE_API.format(APP_ID), json=data, headers=headers, verify=False
        )
        if response.status_code == 200:
            content_id = response.json().get("ContentId")
            if content_id:
                return content_id.get("Version")
    except Exception as e:
        print(f"Error checking upstream version: {e}")
    return None

def get_latest_release_info():
    repo = os.getenv('GITHUB_REPOSITORY')
    if not repo:
        print("GITHUB_REPOSITORY not set, assuming local test or first run")
        return None
    
    token = os.getenv('GITHUB_TOKEN')
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
        
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 404:
            print("No releases found.")
            return None
        resp.raise_for_status()
        data = resp.json()
        body = data.get('body', '')
        
        version_match = re.search(r'Edge 版本:\s*([\d\.]+)', body)
        
        version = version_match.group(1) if version_match else None
        
        return {
            'id': data.get('id'),
            'tag_name': data.get('tag_name'),
            'version': version,
        }
    except Exception as e:
        print(f"Error getting latest release: {e}")
        return None

def get_major_version(version):
    if not version:
        return None
    parts = version.split('.')
    if parts:
        return parts[0]
    return None

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
    print("Checking for updates...")
    
    upstream_version = get_upstream_version()
    
    print(f"Upstream Version: {upstream_version}")
    
    if not upstream_version:
        print("Failed to get upstream version. Forcing build to be safe.")
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
        print(f"Latest Release ID: {release_id}")
        print(f"Latest Release Tag: {release_tag}")
        print(f"Latest Release Version: {latest_version}")
    else:
        latest_version = None
        release_id = None
        release_tag = None
    
    update_needed = upstream_version != latest_version
    
    if update_needed:
        print("Version mismatch/update detected.")
        
    if not latest_version:
        print("No previous version info found or failed to parse. Treating as update needed.")
        update_needed = True

    print(f"Update needed: {update_needed}")
    
    create_new_release = False
    minor_update = False
    if not release_id:
        create_new_release = True
        print("No existing release found. Will create new release.")
    elif update_needed and is_major_version_update(upstream_version, latest_version):
        create_new_release = True
        print(f"Major version update detected: {latest_version} -> {upstream_version}. Will create new release.")
    else:
        print("Minor version update. Will update existing release.")
        if update_needed and is_minor_update(upstream_version, latest_version):
            minor_update = True
            print(f"Minor version update detected: {latest_version} -> {upstream_version}. Will update release title.")
    
    print(f"Create new release: {create_new_release}")
    print(f"Minor update: {minor_update}")
    
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

if __name__ == '__main__':
    main()
