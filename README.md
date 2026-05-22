# prdkit

B 端 PRD 工作流套件：5 个 Cursor Agent Skills + Hook 状态机 + 内置设计规范与 HTML 模板。

## 安装

需已安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。

### 方式 A：克隆仓库后本地安装（适合贡献者 / 想用最新代码）

```bash
git clone https://github.com/gaogep/prdkit.git
cd prdkit

# 可编辑安装：改仓库内代码会立刻反映到 CLI（推荐）
uv tool install -e .

# 安装 Skill 到 ~/.cursor/skills/
prdkit install

# 重启 Cursor 后使用 /prd-init、/prd-clarify、/prd-create、/prd-modify、/prd-check
```

更新代码后：

```bash
cd prdkit
git pull
# Python / data 变更：-e 安装一般无需重装
# Skill 变更：prdkit install --force（会在 SKILL frontmatter 写入 prdkit-bundle-version）
```

### 方式 B：不克隆，直接从 GitHub 安装（适合普通用户）

```bash
uv tool install git+https://github.com/gaogep/prdkit
prdkit install
```

指定版本（打了 tag 时）：

```bash
uv tool install "prdkit @ git+https://github.com/gaogep/prdkit@v0.1.0"
prdkit install
```

### 方式 C：克隆但不开发（一次性本地路径安装）

```bash
git clone https://github.com/gaogep/prdkit.git
cd prdkit
uv tool install .          # 无 -e：代码打进 tool 环境，改仓库不会自动生效
prdkit install
```

### 安装后自检

```bash
which prdkit prdkit-hook
prdkit version
prdkit path reference/prd-writing-spec.md
prdkit path reference/design-spec.md
prdkit path assets/文档输出模板.html
```

若 `which` 无输出，执行 `uv tool update-shell` 后**新开终端**，或确认 `~/.local/bin` 在 `PATH` 中。

## CLI 命令

| 命令 | 说明 |
|------|------|
| `prdkit install [--force]` | 复制 Skills 到 `~/.cursor/skills/` |
| `prdkit path <资源键>` | 输出内置文件绝对路径（供 Agent Read） |
| `prdkit path --list` | 列出全部内置资源键 |
| `prdkit-html init` / `set-toc` / `set-spec` / `set-proto-page` / `set-proto-slot` / `validate` | 合并片段进 PRD HTML（Agent **禁止**手写 Python 拼接）；原型规则见 `reference/prototype-authoring.md` |
| `prdkit-hook check <stage>` | 阶段门禁：`init` / `clarify` / `create` / `modify` |
| `prdkit-hook transit <action>` | 状态流转（见各 Skill 文档） |
| `prdkit-create-md <path>` | 在项目根创建空 `.md` 文件 |

所有 Hook / 创建命令均在**用户项目根目录**下执行。

## 用户项目结构（示例）

```text
my-product-repo/
├── .memory/
│   ├── workflow_state.json   # 仅由 prdkit-hook 写入
│   ├── prd_output.json       # 输出目录与 basename（init 询问，create 使用）
│   ├── product_brief.md
│   └── prd_fragments/        # 可选：章节 HTML 片段
└── prds/                     # 默认输出目录（可自定义）
    └── 催收后台_xxx_prd.html
```

## 开发

与「方式 A」相同；改 Skill 后记得 `prdkit install --force`。

## 许可证

MIT
