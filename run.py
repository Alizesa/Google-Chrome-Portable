import os
import shutil
import xml.dom.minidom
from datetime import datetime

import requests

# ============================================================
# Step 0: 准备环境
# ============================================================
os.system("chmod +x ./7zzs")

# ============================================================
# Step 1: 自动拉取最新 chrome_plus (version.dll)
# ============================================================
CHROME_PLUS_API = "https://api.github.com/repos/Bush2021/chrome_plus/releases/latest"
chrome_plus_version = "unknown"


def get_latest_chrome_plus():
    """通过 GitHub API 获取 chrome_plus 最新 release 中的 version.dll（必须成功）"""
    global chrome_plus_version

    # 1. 获取最新 release 信息
    print("[chrome_plus] 查询最新版本...")
    resp = requests.get(
        CHROME_PLUS_API,
        timeout=30,
        headers={"Accept": "application/vnd.github.v3+json"},
    )
    print(f"[chrome_plus] API 状态: {resp.status_code}")
    resp.raise_for_status()
    release = resp.json()
    tag = release["tag_name"]
    print(f"[chrome_plus] 最新版本: {tag}")

    # 2. 查找资产
    asset_url = None
    for asset in release["assets"]:
        name = asset["name"]
        if "x86_x64_arm64" in name and name.endswith(".7z"):
            asset_url = asset["browser_download_url"]
            print(f"[chrome_plus] 资产: {name}")
            break
    if not asset_url:
        available = [a["name"] for a in release["assets"]]
        raise RuntimeError(f"未找到匹配资产, 可用: {available}")

    # 3. 下载
    print(f"[chrome_plus] 下载中...")
    resp = requests.get(asset_url, timeout=120)
    resp.raise_for_status()
    with open("chrome_plus.7z", "wb") as f:
        f.write(resp.content)
    print(f"[chrome_plus] 下载完成 ({len(resp.content)} bytes)")

    # 4. 列出内容 + 解压
    print("[chrome_plus] 7z 包内容:")
    os.system("./7zzs l chrome_plus.7z")
    ret = os.system("./7zzs x chrome_plus.7z")
    print(f"[chrome_plus] 7zzs 返回码: {ret}")
    if ret != 0:
        raise RuntimeError(f"7z 解压失败 (返回码: {ret})")

    # 5. 打印解压后目录树（调试用）
    print("[chrome_plus] 解压后目录结构:")
    os.system("find . -maxdepth 3 -not -path './.git/*' -not -path './.github/*' | sort | head -40")

    # 6. 用 os.walk 查找 x64/version.dll
    found = None
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "build", ".github")]
        if "version.dll" in files:
            path = os.path.normpath(os.path.join(root, "version.dll"))
            print(f"[chrome_plus]  发现: {path}")
            if "x64" in path.replace("\\", "/").split("/"):
                found = path
                break
    if not found:
        raise RuntimeError("未找到 x64/version.dll")

    # 7. 移动到根目录
    print(f"[chrome_plus] 选用: {found}")
    shutil.move(found, "version.dll")

    # 8. 清理临时文件
    os.remove("chrome_plus.7z")
    for item in os.listdir("."):
        item_path = os.path.join(".", item)
        if os.path.isdir(item_path) and item not in ("build", ".git", ".github"):
            shutil.rmtree(item_path, ignore_errors=True)

    chrome_plus_version = tag
    print(f"[chrome_plus] ✓ version.dll 已更新到 {tag}")
    return True


print("[chrome_plus] 开始拉取最新 version.dll...")
try:
    get_latest_chrome_plus()
except Exception as e:
    print(f"[chrome_plus] 致命错误: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================
# Step 2: 通过 Google Omaha API 获取最新 Chrome 离线包
# ============================================================
url = "https://tools.google.com/service/update2"

# https://github.com/google/omaha/blob/master/doc/ServerProtocolV3.md
data = """<?xml version="1.0" encoding="UTF-8"?>
<request protocol="3.0" updater="Omaha" updaterversion="1.3.36.112" shell_version="1.3.36.111"
	installsource="update3web-ondemand" dedup="cr" ismachine="0" domainjoined="0">
	<os platform="win" version="10.0.22000.282" arch="x64"/>
	<app appid="{8A69D345-D564-463C-AFF1-A69D9E530F96}" ap="x64-stable-multi-chrome" lang="en-us">
		<updatecheck />
	</app>
</request>"""

response = requests.post(url, data=data)

dom = xml.dom.minidom.parseString(response.text)

print(dom.toprettyxml(indent="  "))

url = dom.getElementsByTagName("url")[0].getAttribute("codebase")
name = dom.getElementsByTagName("action")[0].getAttribute("run")

print(url, name)

response = requests.get(url + name)

with open("chrome.7z.exe", "wb") as file:
    file.write(response.content)

os.system("./7zzs x chrome.7z.exe")
os.system("./7zzs x chrome.7z")

# ============================================================
# Step 3: 组装 Chrome + chrome_plus -> 便携版
# ============================================================
version = "0.0.0.0"
path = "Chrome-bin"
for i in os.listdir(path):
    if os.path.isdir(os.path.join(path, i)):
        version = i
        break

print(f"Chrome 版本: {version}")
if version == "0.0.0.0":
    print("错误：未能解析 Chrome 版本号")
    exit(1)

# 将 version.dll 和 chrome++.ini 放入 Chrome 目录
shutil.move(r"version.dll", "Chrome-bin")
shutil.move(r"chrome++.ini", "Chrome-bin")

os.rename(r"Chrome-bin", "Chrome")
shutil.move(r"Chrome", "build/release/Chrome")

# ============================================================
# Step 4: 写入构建名称（供 GitHub Actions artifact 命名）
# ============================================================
env = os.getenv("GITHUB_ENV")
with open(env, "a") as f:
    date_str = datetime.now().strftime("%Y-%m-%d")
    build_name = f"Win64_{version}_cp{chrome_plus_version}_{date_str}"
    f.write(f"BUILD_NAME={build_name}")

print(f"构建完成: {build_name}")
