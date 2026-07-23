import glob
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

        tag = release["tag_name"]
        print(f"[chrome_plus] 最新版本: {tag}")

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
            chrome_plus_version = "fallback"
            return False

        # 下载 7z 包
        resp = requests.get(asset_url, timeout=120)
        resp.raise_for_status()

        with open("chrome_plus.7z", "wb") as f:
            f.write(resp.content)

        # 先列出 7z 包内容（调试用）
        print("[chrome_plus] 7z 包内容:")
        os.system("./7zzs l chrome_plus.7z")

        # 解压
        ret = os.system("./7zzs x chrome_plus.7z -y")
        if ret != 0:
            print(f"[chrome_plus] 7z 解压失败 (返回码: {ret})，回退到本地 version.dll")
            os.remove("chrome_plus.7z")
            chrome_plus_version = "fallback"
            return False

        # 递归查找 x64/version.dll（兼容嵌套目录结构）
        dlls = glob.glob("**/version.dll", recursive=True)
        print(f"[chrome_plus] 找到的 version.dll: {dlls}")
        # 排除仓库根目录的静态 version.dll，只从解压产物中查找
        dlls = [d for d in dlls if d not in ("version.dll", "./version.dll")]
        x64_dll = [d for d in dlls if "x64" in d.replace("\\", "/").split("/")]
        if not x64_dll:
            # 宽松匹配：只要路径不含 x86/arm64 就取第一个
            x64_dll = [d for d in dlls if "x86" not in d and "arm64" not in d]
        if x64_dll:
            target = x64_dll[0]
            print(f"[chrome_plus] 选用: {target}")
            if os.path.exists("version.dll"):
                os.remove("version.dll")
            shutil.move(target, "version.dll")

            # 清理解压产物
            os.remove("chrome_plus.7z")
            for d in glob.glob("*", recursive=False):
                if os.path.isdir(d) and d not in ("build", ".git", ".github"):
                    shutil.rmtree(d, ignore_errors=True)

            chrome_plus_version = tag
            print(f"[chrome_plus] ✓ version.dll 已更新到 {tag}")
            return True
        else:
            print("[chrome_plus] 解压后未找到 version.dll，回退到本地 version.dll")
            if os.path.exists("chrome_plus.7z"):
                os.remove("chrome_plus.7z")
            chrome_plus_version = "fallback"
            return False

    except Exception as e:
        print(f"[chrome_plus] 获取失败: {e}，回退到本地 version.dll")
        chrome_plus_version = "fallback"
        return False


# 尝试获取最新 chrome_plus，失败则使用仓库中的静态 version.dll
get_latest_chrome_plus()

# ============================================================
# Step 1: 通过 Google Omaha API 获取最新 Chrome 离线包
# ============================================================
print(f"[chrome_plus] 实际使用的 version.dll: 版本={chrome_plus_version}, 大小={os.path.getsize('version.dll')} bytes")

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
