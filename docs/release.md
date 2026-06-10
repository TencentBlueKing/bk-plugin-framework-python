# Release Guide

本文档记录 `bk-plugin-framework-python` 的 Python 包发布流程。文档只描述公开的仓库路径、版本规则和验证方式，不记录任何账号、令牌、密钥、私有索引凭据或内部环境地址。

## 包划分

仓库内有两个独立发布的 Poetry 包：

| 包 | 目录 | 版本文件 | Tag 前缀 |
| --- | --- | --- | --- |
| `bk-plugin-runtime` | `runtime/bk-plugin-runtime` | `runtime/bk-plugin-runtime/pyproject.toml`、`runtime/bk-plugin-runtime/bk_plugin_runtime/__version__.py` | `bk-plugin-runtime-v` |
| `bk-plugin-framework` | `bk-plugin-framework` | `bk-plugin-framework/pyproject.toml`、`bk-plugin-framework/bk_plugin_framework/__version__.py` | `bk-plugin-framework-v` |

`bk-plugin-framework` 会在 `pyproject.toml` 中依赖一个明确版本的 `bk-plugin-runtime`。如果 runtime 也要发布新版本，先发布 runtime，再把 framework 的 runtime 依赖更新到新版本后发布 framework。

## 什么时候发布哪个包

- 只改了 `bk-plugin-framework/` 下的 framework 代码或资源：只发布 `bk-plugin-framework`。
- 只改了 `runtime/bk-plugin-runtime/` 下的 runtime 代码或资源：发布 `bk-plugin-runtime`；如果 framework 需要依赖这个新 runtime，再继续发布 `bk-plugin-framework`。
- 两边都有改动：先发布 `bk-plugin-runtime`，再发布 `bk-plugin-framework`。
- 只改文档、示例或不进入包产物的内容：通常不需要发布包。

发布前用最近一个已发布 tag 到目标提交的 diff 判断影响范围，例如：

```bash
git diff --name-status <last-framework-tag>..origin/master -- bk-plugin-framework runtime
git diff --name-status <last-runtime-tag>..origin/master -- runtime
```

## 版本规则

正式版本使用普通语义化版本号，例如：

```text
2.3.13
```

rc 包使用 PEP 440 兼容的预发布版本号，不加横线，例如：

```text
2.3.13rc0
2.3.13rc1
```

版本号需要同时更新对应包的 `pyproject.toml` 和 `__version__.py`。如果 framework 依赖了新的 runtime 版本，还需要同步更新 `bk-plugin-framework/pyproject.toml` 中的 `bk-plugin-runtime` 版本。

## 发布前检查

1. 拉取远端分支和 tag：

```bash
git fetch origin --tags --prune
```

2. 确认目标版本的 tag 不存在：

```bash
git tag --list 'bk-plugin-framework-v<version>'
git tag --list 'bk-plugin-runtime-v<version>'
git ls-remote --tags origin 'bk-plugin-framework-v<version>'
git ls-remote --tags origin 'bk-plugin-runtime-v<version>'
```

3. 确认版本文件一致：

```bash
rg -n 'version = "|__version__' bk-plugin-framework/pyproject.toml bk-plugin-framework/bk_plugin_framework/__version__.py
rg -n 'version = "|__version__' runtime/bk-plugin-runtime/pyproject.toml runtime/bk-plugin-runtime/bk_plugin_runtime/__version__.py
```

4. 本地构建验证。若本机已安装 Poetry：

```bash
cd bk-plugin-framework
poetry build -vvv

cd ../runtime/bk-plugin-runtime
poetry build -vvv
```

也可以用临时隔离环境运行 CI 同款 Poetry 版本：

```bash
cd bk-plugin-framework
uv run --no-project --python 3.10 --with poetry==1.8.5 poetry build -vvv

cd ../runtime/bk-plugin-runtime
uv run --no-project --python 3.10 --with poetry==1.8.5 poetry build -vvv
```

只需要构建本次要发布的包。构建产生的 `dist/` 是本地临时产物，不要提交。

5. 检查 wheel 元数据中包名、版本号和关键依赖是否符合预期：

```bash
python - <<'PY'
from pathlib import Path
import zipfile

wheel = next(Path("dist").glob("*.whl"))
with zipfile.ZipFile(wheel) as zf:
    metadata = [name for name in zf.namelist() if name.endswith("METADATA")][0]
    for line in zf.read(metadata).decode().splitlines():
        if line.startswith(("Name:", "Version:", "Requires-Dist: bk-plugin-runtime")):
            print(line)
PY
```

## 发布步骤

以下命令以 framework 为例。runtime 发布时替换目录、版本文件和 tag 前缀即可。

1. 修改版本文件：

```text
bk-plugin-framework/pyproject.toml
bk-plugin-framework/bk_plugin_framework/__version__.py
```

2. 提交版本变更：

```bash
git add bk-plugin-framework/pyproject.toml bk-plugin-framework/bk_plugin_framework/__version__.py
git commit -m "minor: bump bk-plugin-framework version to v<version>"
```

3. 推送发布提交：

```bash
git push origin HEAD:master
```

4. 创建并推送轻量 tag：

```bash
git tag bk-plugin-framework-v<version>
git push origin bk-plugin-framework-v<version>
```

tag 推送后，仓库中的发布 workflow 会自动构建并发布对应包。发布凭据由仓库 CI 环境统一管理，文档、提交信息和命令记录里都不要写任何凭据内容。

## rc 包发布

rc 包和正式包使用同一套 tag 触发流程，差异只在版本号。

示例：

```text
bk-plugin-runtime-v2.2.0rc0
bk-plugin-framework-v2.4.0rc0
```

如果 framework rc 依赖 runtime rc，需要先发布 runtime rc，然后在 framework 的 `pyproject.toml` 中精确依赖该 runtime rc：

```toml
bk-plugin-runtime = "2.2.0rc0"
```

验证 rc 包时建议精确指定版本：

```bash
pip install bk-plugin-framework==<version>
pip install bk-plugin-runtime==<version>
```

不要只依赖宽松版本范围来验证 rc 包，因为 Python 包管理器默认通常不会在普通版本范围里自动选择预发布版本。

## 发布后验证

1. 确认远端 master 和 tag 指向预期提交：

```bash
git ls-remote origin refs/heads/master refs/tags/bk-plugin-framework-v<version>
git ls-remote origin refs/heads/master refs/tags/bk-plugin-runtime-v<version>
```

2. 确认发布 workflow 成功完成。可以在 GitHub Actions 页面查看对应 tag 触发的 run，或使用 GitHub CLI 查询。

3. 确认包索引可见：

```bash
python -m pip index versions bk-plugin-framework --pre
python -m pip index versions bk-plugin-runtime --pre
```

4. 如需安装验证，精确指定版本：

```bash
pip install bk-plugin-framework==<version>
pip install bk-plugin-runtime==<version>
```

## 不要写入文档或提交记录的信息

- PyPI、包索引、GitHub 或其他系统的账号、令牌、密钥、cookie。
- CI secrets 的具体值。
- 私有环境的上传地址、临时调试地址或带鉴权参数的 URL。
- 个人机器上的一次性路径、一次性 session、一次性 workflow 日志全文。

可以记录公开的仓库路径、workflow 文件路径、tag 规则、版本号规则、验证命令和失败排查结论。
