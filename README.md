# 获取

全自动无人管理项目，每周定时拉取最新 Edge 离线包，并封装为便携版。

采用GitHub Actions自动编译发布，下载地址：[https://github.com/betacola/Edge_Portable/releases/latest](https://github.com/betacola/Edge_Portable/releases/latest)

[![build status](https://github.com/betacola/Edge_Portable/actions/workflows/build.yml/badge.svg)](https://github.com/betacola/Edge_Portable/actions/workflows/build.yml)

# 相关项目

- [ChromiumPortable](https://github.com/Piracola/ChromiumPortable)：Chromium 系便携版构建核心，提供可复用的自动构建、打包和发行流程。
- [Chrome-Portable](https://github.com/Piracola/Chrome-Portable)：同系列 Google Chrome 便携版子项目。

# 安装

**解压 Edge 文件夹，为 msedge.exe 建立桌面快捷方式即可**

# 更新

无法自动更新，未来可以建立独立的绿色升级软件，原 Edge 每4周发布一次新版本，定时为每周，会出现最新的版本相同的情况，平时不需要频繁升级。

**保留 Edge 文件夹中的 User Data, 其他文件删除后解压新压缩包即可，单纯的文件替换。**

# 卸载

删除 Edge 文件夹，删除快捷方式即可，无残留。**注意提前保存 User Data，避免自己的个人浏览数据清空（可微软账号同步，但不如本地数据全面）。**

# 本地构建

```powershell
python -m pip install requests
$env:PYTHONPATH="..\ChromiumPortable"
python -m portable_builder --config browser.json --target edge_stable --workdir . build
```
