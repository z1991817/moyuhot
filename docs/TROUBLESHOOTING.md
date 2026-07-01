# 故障排查

## 容器启动后页面空白或热榜为空

先检查入口和后端健康状态：

```bash
curl http://127.0.0.1:18081/healthz
curl http://127.0.0.1:18081/api/home
```

如果 `/healthz` 正常但 `/api/home` 返回空数据，通常是 SeeSea 没准备好或上游平台临时不可用。

全家桶部署时查看服务状态：

```bash
docker compose -f ops/docker-compose.yml -f ops/docker-compose.full.yml ps
```

外接 SeeSea 时确认 SeeSea 健康检查：

```bash
curl http://127.0.0.1:18080/api/health
```

## 端口被占用

默认端口：

- `18081`：Nginx 入口
- `18000`：FastAPI 调试端口
- `14321`：Astro 前端调试端口
- `18080`：全家桶部署中的 SeeSea 服务

可以复制 `ops/.env.example` 为 `ops/.env` 后改端口：

```dotenv
MOYU_NGINX_PORT=127.0.0.1:28081
MOYU_API_PORT=127.0.0.1:28000
MOYU_FRONTEND_PORT=127.0.0.1:24321
SEESEA_PORT=127.0.0.1:28080
```

## 全家桶构建很慢

第一次构建会安装 Node、Python 和 SeeSea 相关依赖，耗时较长是正常的。后续构建会复用 Docker 缓存。

全家桶里的 SeeSea 镜像通过 PyPI 包构建，版本固定在 [ops/seesea.Dockerfile](../ops/seesea.Dockerfile)。镜像使用 `python:3.12-slim`，用于满足 SeeSea 上游 wheel 的 glibc 版本要求。如果 SeeSea 上游接口或健康检查路径变化，可以先确认容器内服务：

```bash
docker compose -f ops/docker-compose.yml -f ops/docker-compose.full.yml logs seesea
curl http://127.0.0.1:18080/api/health
```

如果只想更新摸鱼热榜本身，并且已有外部 SeeSea 服务，可以改用：

```bash
docker compose -f ops/docker-compose.yml up -d --build
```

## A 股行情为空

A 股行情依赖 OpenTDX 和公开行情网络环境，非交易时段或网络不稳定时可能返回旧快照或空结果。页面会标记 stale 状态，避免把不完整数据伪装成实时行情。

## SeeSea 服务不要直接暴露公网

生产环境建议只开放 Nginx 入口端口。SeeSea、FastAPI 调试端口和数据库卷都应保持内网访问。
