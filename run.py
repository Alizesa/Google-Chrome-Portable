import json
import os
import shutil
import xml.dom.minidom
from datetime import datetime

import requests

# ============================================================
# Step 0: 自动拉取最新 chrome_plus (version.dll)
# ============================================================
CHROME_PLUS_API = "https://api.github.com/repos/Bush2021/chrome_plus/releases/latest"

chrome_plus_version = "unknown"


def get_latest_chrome_plus():
    """通过 GitHub API 获取 chrome_plus 最新 release 中的 version.dll"""
    global chrome_plus_version
    try:
        resp = requests.get(
            CHROME_PLUS_API,
            timeout=30,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        resp.raise_for_status()
        release = resp.json()

        chrome_plus_version = release["tag_name"]
        print(f"[chrome_plus] 最新版本: {chrome_plus_version}")

        # 查找包含 version.dll 的资产（通常名为 Chrome++_v*_x86_x64_arm64.7z）
        asset_url = None
        for asset in release["assets"]:
            name = asset["name"]
            if "x86_x64_arm64" in name and name.endswith(".7z"):
                asset_url = asset["browser_download_url"]
                print(f"[chrome_plus] 下载: {name}")
                break

        if not asset_url:
            print("[chrome_plus] 未找到匹配的资产，回退到本地 version.dll")
            return False

        # 下载 7z 包
        resp = requests.get(asset_url, timeout=120)
        resp.raise_for_status()

        with open("chrome_plus.7z", "wb") as f:
            f.write(resp.content)

        # 解压
        os.system("./7zzs x chrome_plus.7z -y")

        # 提取 x64/version.dll
        if os.path.exists("x64/version.dll"):
            if os.path.exists("version.dll"):
                os.remove("version.dll")
            shutil.move("x64/version.dll", "version.dll")

            # 清理解压产物
            for d in ["x64", "x86", "arm64"]:
                if os.path.isdir(d):
                    shutil.rmtree(d)
            os.remove("chrome_plus.7z")

            print(f"[chrome_plus] ✓ version.dll 已更新到 {chrome_plus_version}")
            return True
        else:
            print("[chrome_plus] 解压后未找到 x64/version.dll，回退到本地 version.dll")
            if os.path.exists("chrome_plus.7z"):
                os.remove("chrome_plus.7z")
            return False

    except Exception as e:
        print(f"[chrome_plus] 获取失败: {e}，回退到本地 version.dll")
        return False


# 尝试获取最新 chrome_plus，失败则使用仓库中的静态 version.dll
get_latest_chrome_plus()

# ============================================================
# Step 1: 通过 Google Omaha API 获取最新 Chrome 离线包
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

os.system("chmod +x ./7zzs")
os.system("./7zzs x chrome.7z.exe")
os.system("./7zzs x chrome.7z")

# ============================================================
# Step 2: 组装 Chrome + chrome_plus -> 便携版
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
# Step 3: 写入构建名称（供 GitHub Actions artifact 命名）
# ============================================================
env = os.getenv("GITHUB_ENV")
with open(env, "a") as f:
    date_str = datetime.now().strftime("%Y-%m-%d")
    build_name = f"Win64_{version}_cp{chrome_plus_version}_{date_str}"
    f.write(f"BUILD_NAME={build_name}")

print(f"构建完成: {build_name}")
