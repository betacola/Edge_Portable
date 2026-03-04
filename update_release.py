import os
import requests

def get_github_api_headers():
    token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    if token:
        headers['Authorization'] = f'token {token}'
    return headers

def delete_release_asset(release_id, asset_id):
    repo = os.getenv('GITHUB_REPOSITORY')
    url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
    headers = get_github_api_headers()
    
    resp = requests.delete(url, headers=headers)
    if resp.status_code == 204:
        print(f"Deleted asset {asset_id}")
        return True
    else:
        print(f"Failed to delete asset {asset_id}: {resp.status_code} {resp.text}")
        return False

def get_release_assets(release_id):
    repo = os.getenv('GITHUB_REPOSITORY')
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = get_github_api_headers()
    
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get('assets', [])

def delete_assets_by_pattern(release_id, pattern):
    assets = get_release_assets(release_id)
    for asset in assets:
        name = asset.get('name', '')
        if pattern in name.lower():
            asset_id = asset.get('id')
            print(f"Deleting asset: {name} (ID: {asset_id})")
            delete_release_asset(release_id, asset_id)

def update_release_body(release_id, new_body):
    repo = os.getenv('GITHUB_REPOSITORY')
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = get_github_api_headers()
    
    data = {
        'body': new_body
    }
    
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code == 200:
        print(f"Updated release {release_id} body")
        return True
    else:
        print(f"Failed to update release body: {resp.status_code} {resp.text}")
        return False

def update_release_title_and_tag(release_id, new_title, new_tag):
    repo = os.getenv('GITHUB_REPOSITORY')
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = get_github_api_headers()
    
    data = {
        'name': new_title,
        'tag_name': new_tag
    }
    
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code == 200:
        print(f"Updated release {release_id} title to '{new_title}' and tag to '{new_tag}'")
        return True
    else:
        print(f"Failed to update release title/tag: {resp.status_code} {resp.text}")
        return False

def generate_release_body(version, build_date):
    lines = [
        "自动构建的 Microsoft Edge 便携版",
        "解压后即可使用，数据文件存储在同级文件夹下",
        "官方发行说明 / Official Release Notes: [microsoft-edge-relnote-stable-channel](https://learn.microsoft.com/zh-cn/deployedge/microsoft-edge-release-notes)",
        "",
        f"构建时间: {build_date}",
        f"Edge 版本: {version}",
    ]
    return "\n".join(lines)

def main():
    release_id = os.getenv('RELEASE_ID')
    minor_update = os.getenv('MINOR_UPDATE', 'false').lower() == 'true'
    version = os.getenv('EDGE_VERSION', '')
    upstream_version = os.getenv('UPSTREAM_VERSION', '')
    build_date = os.getenv('BUILD_DATE', '')
    
    if not release_id:
        print("No existing release ID found. This will be handled by the create release step.")
        return
    
    print(f"Updating release {release_id}")
    print(f"Minor update: {minor_update}")
    
    print("Deleting old assets...")
    delete_assets_by_pattern(release_id, 'edge')
    
    final_version = version if version else upstream_version
    
    new_body = generate_release_body(final_version, build_date)
    update_release_body(release_id, new_body)
    
    if minor_update and final_version:
        new_title = f"Edge Portable v{final_version}"
        new_tag = f"v{final_version}"
        update_release_title_and_tag(release_id, new_title, new_tag)
    
    print("Release update completed.")

if __name__ == '__main__':
    main()
