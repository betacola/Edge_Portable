import json
import re
import sys

import requests


APP_ID = "msedge-stable-win-x64"
USER_AGENT = "Microsoft Edge Update/1.3.183.29;winhttp"
EDGE_UPDATE_API = "https://msedge.api.cdp.microsoft.com/api/v2/contents/Browser/namespaces/Default/names/{0}/versions/latest?action=select"
EDGE_DOWNLOAD_API = "https://msedge.api.cdp.microsoft.com/api/v1.1/internal/contents/Browser/namespaces/Default/names/{0}/versions/{1}/files?action=GenerateDownloadInfo"
EDGE_INSTALLER_REPO = "Bush2021/edge_installer"


def compare_versions(v1, v2):
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]
    for index in range(max(len(parts1), len(parts2))):
        p1 = parts1[index] if index < len(parts1) else 0
        p2 = parts2[index] if index < len(parts2) else 0
        if p1 != p2:
            return 1 if p1 > p2 else -1
    return 0


def get_version_from_microsoft_api():
    headers = {"User-Agent": USER_AGENT}
    data = {
        "targetingAttributes": {
            "IsInternalUser": True,
            "Updater": "MicrosoftEdgeUpdate",
            "UpdaterVersion": "1.3.183.29",
        }
    }
    response = requests.post(EDGE_UPDATE_API.format(APP_ID), json=data, headers=headers, verify=False, timeout=60)
    response.raise_for_status()
    content_id = response.json().get("ContentId")
    return content_id.get("Version") if content_id else None


def get_version_from_edge_installer():
    response = requests.get(f"https://api.github.com/repos/{EDGE_INSTALLER_REPO}/releases/latest", timeout=60)
    if response.status_code != 200:
        return None
    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", response.json().get("tag_name", ""))
    return match.group(1) if match else None


def get_download_info(version):
    headers = {"User-Agent": USER_AGENT}
    response = requests.post(EDGE_DOWNLOAD_API.format(APP_ID, version), headers=headers, verify=False, timeout=60)
    response.raise_for_status()
    items = response.json()
    if not items:
        raise RuntimeError("Microsoft Edge download API returned no files.")
    items.sort(key=lambda item: item.get("SizeInBytes", 0), reverse=True)
    item = items[0]
    file_name = item.get("FileId") or "MicrosoftEdgeSetup.exe"
    if not file_name.lower().endswith(".exe"):
        file_name += ".exe"
    return item.get("Url"), file_name


def main():
    requests.packages.urllib3.disable_warnings()
    ms_version = get_version_from_microsoft_api()
    repo_version = get_version_from_edge_installer()
    version = ms_version or repo_version
    if ms_version and repo_version and compare_versions(repo_version, ms_version) > 0:
        version = repo_version
    if not version:
        raise RuntimeError("Unable to determine Edge version.")

    url, file_name = get_download_info(version)
    print(json.dumps({
        "version": version,
        "url": url,
        "file_name": file_name,
        "verify_ssl": False
    }))


if __name__ == "__main__":
    sys.exit(main())
