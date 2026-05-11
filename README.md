# Edge 便携版

> 全自动构建的 Microsoft Edge 便携版，集成 Chrome++ 增强组件，提供纯净、高效的浏览体验。

[![Build Status](https://github.com/betacola/Edge_Portable/actions/workflows/build.yml/badge.svg)](https://github.com/betacola/Edge_Portable/actions/workflows/build.yml)

## 仓库导航

- [ChromiumPortable（主仓库）](https://github.com/Piracola/ChromiumPortable)：通用构建核心仓库。
- [Chrome-Portable](https://github.com/Piracola/Chrome-Portable)：同系列 Google Chrome 便携版项目。
- [Helium_Portable](https://github.com/Piracola/Helium_Portable)：同系列 Helium 便携版子项目。

## 项目简介

本项目全自动构建，每天定时检查 Microsoft 官方是否有最新 Edge 离线安装包更新，集成 Chrome++ 组件并封装为便携版。

项目预配置了自定义增强功能，具体配置请查看`chrome++.ini`。

目前项目默认同步构建 Stable 版本，如后续扩展其他渠道，将在同一流程内统一维护。


## 功能特性

以下功能均可在`chrome++.ini`中修改：

- 所有用户数据及缓存均存储于程序同级目录的 `Data` 和 `Cache` 文件夹
- 双击关闭标签页、保留最后一个标签页
- 支持新建前台标签页打开书签或地址栏内容
- 更多增强功能请查看`chrome++.ini`

## 快速开始

**安装**

1. 下载：访问 [Releases](https://github.com/betacola/Edge_Portable/releases/latest) 获取最新版本
2. 解压：将压缩包解压至任意位置
3. 运行`开始.bat`文件创建快捷方式

**更新**

1. 保留旧版 Edge 文件夹中的 `User Data` 目录。
2. 删除其余旧文件后，解压新版 Edge 文件夹到同级目录完成覆盖更新。

**卸载**

1. 删除 Edge 文件夹即可完成卸载。

## 致谢

本项目基于以下优秀开源项目构建：

| 项目                                                                     | 说明        |
| ---------------------------------------------------------------------- | --------- |
| [Bush2021/chrome\_plus](https://github.com/Bush2021/chrome_plus)       | 提供核心便携化组件 |
| [rnamoy/chrome\_installer](https://github.com/rnamoy/chrome_installer) | 提供安装包解析   |

## 许可证

本项目源码遵循 MIT 许可证。

- Microsoft Edge 浏览器版权归 Microsoft 所有
- Chrome++ 组件版权归原作者所有

***

本项目采用 GitHub Actions 自动检查更新，版本号与 Edge 官方 Stable 分支保持一致。查看 [Releases](https://github.com/betacola/Edge_Portable/releases) 获取历史版本。
