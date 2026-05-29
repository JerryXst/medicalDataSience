# Docker 部署

根目录 `docker-compose.yml` 是本地开发和单机部署入口。

## 基础服务

```bash
docker compose up --build
```

## 启动 RPA worker

```bash
docker compose --profile automation up --build
```
