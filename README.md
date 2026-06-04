# 摸鱼热榜

> 公开榜单链接聚合站点。只展示标题、平台、排名、热度、更新时间与原站链接，不转载正文、不缓存图片、不做 AI 摘要。

摸鱼热榜负责把多个公开热榜和行情数据清洗成统一页面与 API。热榜上游数据来自外部运行的 [SeeSea](https://github.com/nostalgiatan/SeeSea) 服务，本仓库不内置、不复制 SeeSea 源码。

项目仓库：[z1991817/moyuhot](https://github.com/z1991817/moyuhot)

## 功能范围

- 热榜聚合：微博、知乎、B 站、抖音、V2EX、GitHub Trending 等公开榜单。
- 页面版本：默认简约版 `/`，大胆版 `/bold`，新版页面 `/ui-new/*`。
- 行情展示：美股指数、热门美股、A 股市场快照。
- AI 助手：可选接入 OpenAI-compatible 聊天网关；不配置密钥时聊天功能不可用。
- 缓存兜底：后端使用 SQLite 缓存，外部数据源短时不可用时尽量返回旧快照。

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 前端 | Astro 5、TypeScript、原生 CSS、pnpm |
| 后端 | FastAPI、Pydantic v2、httpx、APScheduler、SQLite |
| 热榜上游 | SeeSea HTTP API |
| 美股数据 | 新浪财经 / 腾讯财经公开行情接口 |
| A 股数据 | OpenTDX |
| 部署 | Docker Compose、Nginx |

## 环境要求

推荐使用 Docker 部署，避免本机 Python / Node 环境差异。

- Docker 24+ 与 Docker Compose v2
- 可访问互联网，用于拉取镜像、安装依赖和访问公开数据源
- 一个已经启动的 SeeSea HTTP 服务

仅本地开发时还需要：

- Node.js 22+
- pnpm 10+
- Python 3.11+

SeeSea 自身的运行环境请以其上游仓库为准。SeeSea README 中说明其默认 API 服务监听 `127.0.0.1:8888`，也可以用参数改成自定义端口。本项目示例统一使用宿主机 `18080` 端口，便于和 Docker Compose 对接。

## 快速部署

先拉取本项目源码：

```bash
git clone https://github.com/z1991817/moyuhot.git
cd moyuhot
```

### 1. 启动 SeeSea

先拉取并启动 SeeSea。下面只是常见示例，完整安装方式请看 [nostalgiatan/SeeSea](https://github.com/nostalgiatan/SeeSea)。

```bash
git clone https://github.com/nostalgiatan/SeeSea.git
cd SeeSea
```

如果 SeeSea 已经安装了 CLI，可以直接启动 API 服务：

```bash
seesea server --host 0.0.0.0 --port 18080
```

确认 SeeSea 健康检查可访问：

```bash
curl http://127.0.0.1:18080/api/health
```

如果你使用 SeeSea 默认端口 `8888`，后续把本项目的 `SEESEA_BASE_URL` 改成对应地址即可。

### 2. 配置摸鱼热榜

复制环境变量示例：

```bash
cp ops/.env.example ops/.env
```

Windows PowerShell：

```powershell
Copy-Item ops\.env.example ops\.env
```

编辑 `ops/.env`。Docker Compose 部署时，如果 SeeSea 跑在宿主机，推荐这样写：

```dotenv
SEESEA_BASE_URL=http://host.docker.internal:18080
PUBLIC_SITE_URL=http://127.0.0.1:18081
```

如果后端不是跑在 Docker 容器里，而是直接跑在宿主机，可以写：

```dotenv
SEESEA_BASE_URL=http://127.0.0.1:18080
```

### 3. 启动本项目

```bash
docker compose -f ops/docker-compose.yml up -d --build
```

访问：

```text
http://127.0.0.1:18081/
```

健康检查：

```bash
curl http://127.0.0.1:18081/healthz
```

Windows 也可以使用脚本：

```powershell
.\ops\restart.ps1 -Mode docker -Build
```

停止服务：

```bash
docker compose -f ops/docker-compose.yml down --remove-orphans
```

## `.env` 配置

`ops/docker-compose.yml` 会读取 `ops/.env`。常用配置如下：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `MOYU_NGINX_PORT` | `127.0.0.1:18081` | Nginx 入口端口，浏览器访问这个地址。 |
| `MOYU_FRONTEND_PORT` | `127.0.0.1:14321` | Astro 前端容器端口，一般不需要直接访问。 |
| `MOYU_API_PORT` | `127.0.0.1:18000` | FastAPI 容器端口，可用于调试 API。 |
| `SEESEA_BASE_URL` | `http://host.docker.internal:18080` | SeeSea HTTP 服务地址。 |
| `PUBLIC_SITE_URL` | `https://moyuhot.com` | 站点公开地址，用于 SEO canonical 等前端元信息；部署自己的站点时请改成你的域名。 |
| `CHAT_GATEWAY_BASE_URL` | `https://api.freetheai.xyz/v1` | OpenAI-compatible 聊天网关示例地址；可替换为自己的兼容网关。 |
| `CHAT_GATEWAY_API_KEY` | 空 | 聊天网关密钥；为空时 AI 助手不可用。 |
| `CHAT_GATEWAY_DEFAULT_MODEL` | `fee/deepseek-v4-pro` | 默认聊天模型。 |
| `CHAT_GATEWAY_MODELS` | 多模型逗号分隔 | 前端可选模型列表。 |
| `CHAT_GATEWAY_WEB_SEARCH_ENABLED` | `false` | 是否允许聊天网关启用联网搜索。 |

注意：

- 不要提交真实的 `ops/.env`。
- 如果你把 Nginx 暴露到公网，建议只开放 Nginx 端口，不要直接暴露 SeeSea、SQLite 或内部管理端口。
- `PUBLIC_SITE_URL` 部署到正式域名后再改成你的真实域名。
- AI 助手是可选功能；不想启用时保持 `CHAT_GATEWAY_API_KEY` 为空即可。

## 数据来源

### 热榜数据

热榜数据来自外部 [SeeSea](https://github.com/nostalgiatan/SeeSea) 服务。SeeSea 是一个隐私优先的数据聚合与 AI 工具项目，提供搜索、RSS、股票、热点、数据清洗、MCP 等能力。本项目只使用其中的热点 HTTP API，并通过 FastAPI 做字段清洗和统一映射。

本项目当前调用的 SeeSea 接口包括：

- `GET /api/hot/platforms`
- `GET /api/hot/{platform}`
- `GET /api/hot/multiple`

前端不会直连 SeeSea。所有热榜数据都先经过 `backend/app/clients/seesea.py`，再映射成统一字段：

```text
platform / platformName / title / url / rank / heat / source / updatedAt
```

### 行情数据

- 美股指数与热门美股：来自新浪财经、腾讯财经公开行情接口。
- A 股市场快照：通过 OpenTDX 获取指数、个股、市场宽度与板块数据。

行情数据仅供信息展示，不构成投资建议。

## API

默认经 Nginx 代理后，API 地址为 `http://127.0.0.1:18081/api`。

| 路径 | 说明 |
| --- | --- |
| `GET /healthz` | 服务健康检查 |
| `GET /api/home` | 首页聚合数据 |
| `GET /api/trends?platform=weibo` | 单个平台热榜 |
| `GET /api/sources` | 可用热榜来源 |
| `GET /api/market/us` | 美股指数 |
| `GET /api/market/us/stocks` | 热门美股 |
| `GET /api/market/cn` | A 股市场快照 |
| `GET /api/chat/models` | 聊天模型列表 |
| `POST /api/chat/completions` | 聊天补全 |

## 目录结构

```text
moyuhot/
├── frontend/              # Astro 前端
├── backend/               # FastAPI 后端
├── docs/                  # README 图片等文档资源
├── ops/                   # Docker Compose / Nginx / 启停脚本
├── .dockerignore
├── .gitignore
└── README.md
```

## 开发命令

前端：

```bash
cd frontend
pnpm install
pnpm check
pnpm build
```

后端：

```bash
cd backend
python -m venv .venv
pip install -e ".[dev]"
ruff check .
ruff format --check .
pyright
pytest -q
```

联调和最终验证仍建议使用 Docker Compose：

```bash
docker compose -f ops/docker-compose.yml up -d --build
```

## 数据边界与合规

- 只聚合公开榜单链接和必要展示字段。
- 不抓取正文、图片、视频、评论或用户数据。
- 不绕过登录、付费墙或平台访问限制。
- 不提供投资建议、荐股、收益预测。
- 前端不直连 SeeSea，不暴露 SeeSea 原始字段。
- 错误信息应脱敏，不向前端暴露内部路径、容器名或上游细节。


## 致谢

感谢 [nostalgiatan/SeeSea](https://github.com/nostalgiatan/SeeSea) 提供强大的上游数据聚合能力。摸鱼热榜的热榜数据取得依赖外部运行的 SeeSea 服务，本项目在其基础上做面向公开榜单链接聚合站的展示、缓存、字段映射和页面体验。

使用 SeeSea 时请遵守其许可证和上游网站规则。SeeSea 当前采用 AGPL-3.0 License，本项目不会将 SeeSea 源码并入仓库，也不会修改后重新分发 SeeSea。

## License

本项目采用 MIT License，详见仓库根目录 [LICENSE](./LICENSE) 文件。

## 支持 & 赞助

如果觉得有所帮助，欢迎扫码赞助☕、点击项目主页顶部的 ⭐ Star 按钮支持！

🚀 这将是我们持续更新的动力源泉！同时，你也能第一时间获取到最新的更新动态。💡❤️

<p align="center">
  <img src="./docs/images/sponsor-qr.jpg" alt="赞助二维码" width="320" />
</p>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=z1991817/moyuhot&type=Date)](https://www.star-history.com/#z1991817/moyuhot&Date)
