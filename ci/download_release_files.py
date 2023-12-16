import requests
import os

HERE = os.path.dirname(__file__)
DIST_DIR = os.path.abspath(os.path.join(HERE, "..", "dist"))
REPO = "jrast/littlefs-python"

if not os.path.exists(DIST_DIR):
    os.mkdir(DIST_DIR)

resp = requests.get("https://api.github.com/repos/%s/releases/latest" % REPO)

if resp.status_code != 200:
    raise RuntimeError("Github API call failed!")

data = resp.json()

print("Release Tag:", data["tag_name"])

print("Assets:")
num_assets = len(data["assets"])
for nr, e in enumerate(data["assets"], 1):
    print("(%2d/%2d) Downloading %s" % (nr, num_assets, e["name"]))
    r = requests.get(e["browser_download_url"], allow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError("Downloading %s failed!" % e["name"])
    with open(os.path.join(DIST_DIR, e["name"]), "wb") as fh:
        fh.write(r.content)
