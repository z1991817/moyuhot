# 贡献指南

感谢你考虑为摸鱼热榜贡献代码或反馈。

## 提 Issue

- **Bug 报告**：描述复现步骤、实际行为、期望行为，以及你的部署方式（Docker / 本地）。
- **功能建议**：说明使用场景和动机，不需要附带实现方案。
- 提 issue 前请先搜索是否已有相同问题。

## 提交 Pull Request

1. Fork 仓库，基于 `main` 创建分支，分支名建议用 `fix/xxx` 或 `feat/xxx`。
2. 改动尽量聚焦，一个 PR 解决一件事。
3. 提交前在本地跑一遍检查（见下方命令），确保 lint / type check 通过。
4. PR 描述说明改了什么、为什么改，如有 UI 变化请附截图。

## 本地开发

环境要求：Node.js 22+、pnpm 10+、Python 3.11+、Docker（可选，用于联调）。

**前端**

```bash
cd frontend
pnpm install
pnpm check   # TypeScript 类型检查
pnpm build
```

**后端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check .
ruff format --check .
pyright
pytest -q
```

**完整联调**

```bash
cp ops/.env.example ops/.env
# 编辑 ops/.env，填写 SEESEA_BASE_URL
docker compose -f ops/docker-compose.yml up -d --build
```

## 代码风格

- **后端**：Ruff 格式化 + lint，Pyright strict 类型检查，符合 `pyproject.toml` 中的配置即可。
- **前端**：TypeScript strict 模式，`pnpm check` 不报错。
- 默认不写注释；只在逻辑非显而易见时加一行简短说明。

## 数据边界

新增数据来源或字段时，请确保符合项目的合规原则：只展示公开榜单链接和必要字段，不抓取正文、图片或用户数据，不绕过访问限制。详见 [README 数据边界与合规](README.md#数据边界与合规) 章节。

## License

提交代码即表示你同意以 MIT License 授权你的贡献。
