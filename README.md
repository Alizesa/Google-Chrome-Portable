# 功能

- ~~双击关闭标签页~~
- ~~保留最后标签页（防止关闭最后一个标签页时关闭浏览器，点X不行）~~
- 根据个人习惯取消了双击关闭，避免误触带来的麻烦
- 鼠标悬停标签栏滚动
- 按住右键时滚轮滚动标签栏
- ~~便携设计，程序放在App目录，数据放在Data目录（不兼容原版数据，可以重装系统换电脑不丢数据）~~
- 便携设计，程序放在Chrome目录，数据和缓存放在同级目录Data\Cache下，不会在%User%/AppData中建立目录（不兼容原版数据，可以重装系统换电脑不丢数据）
- 移除更新错误警告，移除不必要的显示（因为是绿色版没有自动更新功能）

以上配置都可以在chrome++.ini中进行修改.
https://github.com/Bush2021/chrome_plus

# 获取

全自动无人管理项目，每周定时拉取最新Chrome离线包和最新[chrome_plus](https://github.com/Bush2021/chrome_plus)的`version.dll`，封装为便携版。chrome_plus 不再依赖手动更新。

采用 GitHub Actions 自动构建，并在主分支构建成功后自动发布 GitHub Release，长期保存各次构建的版本。

- [下载最新发行版](https://github.com/Alizesa/Google-Chrome-Portable/releases/latest)
- [查看和下载历史版本](https://github.com/Alizesa/Google-Chrome-Portable/releases)
- [下载临时构建产物](https://nightly.link/Alizesa/Google-Chrome-Portable/workflows/build/main)（Actions artifact 保留 15 天）

每个 Release 都包含 Windows x64 便携版 ZIP 和 `SHA256SUMS.txt` 校验文件，并记录 Chrome 版本、chrome_plus 版本及构建来源。解压 ZIP 后即可得到 `Chrome` 文件夹。

推送到 `main`、每周一北京时间 16:00 的定时任务，以及在 `main` 上手动运行工作流，都会在构建成功后发行；Pull Request 仅执行构建检查。发行标签采用 `v<Chrome版本>-build.<构建序号>.<重试序号>`，同一版本的再次构建也会单独保存。发行使用工作流自带的 `GITHUB_TOKEN`，无需新增 Secret。

[![build status](https://github.com/Alizesa/Google-Chrome-Portable/actions/workflows/build.yml/badge.svg)](https://github.com/Alizesa/Google-Chrome-Portable/actions/workflows/build.yml)

# 安装

**解压Chrome文件夹，为Chrome.exe建立桌面快捷方式即可**

# 更新

无法自动更新，未来可以建立独立的绿色升级软件，原Chrome每4周发布一次新版本，定时为每周，会出现最新的版本相同的情况，平时不需要频繁升级。

**保留Chrome文件夹中的Data和Cache,其他文件删除后解压新压缩包即可，单纯的文件替换。**

# 卸载

删除Chrome文件夹，删除快捷方式即可，无残留。**注意提前保存Data，避免自己的个人浏览数据清空（可谷歌账号同步，但不如Data全面）。**
