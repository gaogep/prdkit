# prdkit

B 端 PRD 工作流套件：5 个 Cursor Agent Skills + Hook 状态机 + 内置设计规范与 HTML 模板。

**本仓库即完整安装包**：克隆后进入目录执行 `uv tool install -e .` 与 `prdkit install` 即可，无需再嵌套其他父项目。

## 快速开始（3 步）

```bash
git clone https://github.com/gaogep/prdkit.git
cd prdkit

uv tool install -e .
prdkit install
```

重启 Cursor 后使用：`/prd-init` → `/prd-clarify` → `/prd-create` → `/prd-modify` → `/prd-check`。

安装后自检：

```bash
prdkit version
prdkit path reference/design-spec.md
which prdkit-html prdkit-hook
```

若命令找不到：执行 `uv tool update-shell` 后**新开终端**，或确认 `~/.local/bin` 在 `PATH` 中。

## 仓库结构

```text
prdkit/                    # 克隆得到的根目录（与 GitHub 仓库同名）
├── README.md
├── LICENSE
├── pyproject.toml         # 安装入口：uv / pip 读此文件
├── prdkit/                # Python 包（CLI、资源、Skills 源码）
│   ├── cli.py
│   ├── html_tool.py
│   ├── data/
│   │   ├── assets/        # HTML 模板、原型壳、CSS/JS
│   │   └── reference/     # design-spec、撰写规范
│   └── skills/            # Cursor Skill（由 prdkit install 复制到 ~/.cursor/skills/）
├── tests/
└── scripts/               # 可选开发脚本（非安装必需）
```

在你的**业务项目**里使用 prdkit 时，只需另建工作区目录，例如：

```text
my-product-repo/
├── .memory/               # workflow、brief、prd_output.json
└── prds/                  # 生成的 PRD HTML
```

## 安装方式

需已安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

### 方式 A：克隆后可编辑安装（推荐）

```bash
git clone https://github.com/gaogep/prdkit.git
cd prdkit
uv tool install -e .
prdkit install
```

更新代码：`git pull`；Skill 变更后执行 `prdkit install --force`。

### 方式 B：不克隆，从 GitHub 安装

```bash
uv tool install git+https://github.com/gaogep/prdkit
prdkit install
```

指定版本（已打 tag 时）：

```bash
uv tool install "prdkit @ git+https://github.com/gaogep/prdkit@v0.1.0"
prdkit install
```

### 方式 C：克隆后非可编辑安装

```bash
git clone https://github.com/gaogep/prdkit.git
cd prdkit
uv tool install .
prdkit install
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `prdkit install [--force]` | 将内置 Skills 复制到 `~/.cursor/skills/` |
| `prdkit path <资源键>` | 输出内置文件绝对路径（供 Agent Read） |
| `prdkit path --list` | 列出全部内置资源键 |
| `prdkit-html init` / `set-toc` / `set-spec` / `set-proto-page` / `validate` / `check-consistency` | 合并 PRD HTML 片段；规则见 `reference/prototype-authoring.md` |
| `prdkit-hook check <stage>` | 阶段门禁：`init` / `clarify` / `create` / `modify` |
| `prdkit-hook transit <action>` | 状态流转（见各 Skill） |
| `prdkit-create-md <path>` | 在用户项目根创建空 `.md` |

Hook / 创建类命令在**你的业务项目根目录**执行（含 `.memory/` 的那一层），不是在 prdkit 仓库目录内。

## 开发

```bash
git clone git@github.com:gaogep/prdkit.git
cd prdkit
uv tool install -e .
PYTHONPATH=. python -m pytest tests/ -q
```

改 Skill 后：`prdkit install --force`。

## 许可证

MIT — 见 [LICENSE](LICENSE)。
