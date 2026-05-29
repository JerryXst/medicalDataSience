# medicalDataSience

药品流向数据平台 V1 工程骨架。第一版目标是先跑通核心业务闭环：

```text
RPA/人工获取原始文件 -> 原始文件归档 -> 数据清洗入库 -> 异常池处理 -> Web 查询
```

## 目录结构

```text
apps/
  backend/       FastAPI 后端服务
  frontend/      React Web 前端
database/
  init/          PostgreSQL 初始化 SQL
deploy/
  docker/        容器运行配置
  k8s/           Kubernetes 部署清单
docs/            产品和技术文档
samples/         样本文件
scripts/         本地脚本
```

## 本地启动

```bash
cp .env.example .env
docker compose up --build
```

启动后访问：

- Web: http://localhost:3000
- API: http://localhost:8000/api/health

## Kubernetes

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/
```

K8s 镜像地址需要在 `deploy/k8s/backend.yaml` 和 `deploy/k8s/frontend.yaml` 中替换为实际镜像仓库。
