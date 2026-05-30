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

## 技术架构

```text
React + TypeScript + Ant Design
          |
       REST API
          |
Python FastAPI
          |
PostgreSQL
          |
Python pandas / openpyxl
```

- 前端：`apps/frontend`，使用 React、TypeScript、Ant Design 构建运营端和用户端。
- 接口：前后端通过 `/api/*` REST API 通信，所有业务请求携带 `X-Request-ID`。
- 后端：`apps/backend`，使用 FastAPI 提供认证、权限、上传、任务、审计日志接口。
- 数据库：PostgreSQL 保存导入任务、账号、角色、审计日志和后续业务数据。
- 表格解析：后端使用 pandas、openpyxl 解析 Excel/CSV，`.xls` 兼容依赖 `xlrd`。

## 本地启动

```bash
cp .env.example .env
docker compose up --build
```

启动后访问：

- Web 入口: http://localhost:3000
- 运营端: http://localhost:3000/ops
- 用户端: http://localhost:3000/portal
- API: http://localhost:8000/api/health

默认账号：

- 平台管理员：admin / admin123
- 业务管理员：manager / manager123
- 业务员：sales / sales123

## 当前功能

- 平台分为运营端和用户端两个 Web 入口。
- 运营端支持数据上传、导入任务状态查看、数据异常处理、用户账号管理、角色权限查看。
- 用户端支持账号密码登录，并根据角色权限展示“数据查询”“数据看板”菜单。
- 前端支持上传 `.xlsx`、`.xls`、`.csv` 表格文件。
- 每次上传会创建一个唯一导入编号，并在任务列表显示解析状态。
- 解析成功显示绿色状态，解析失败显示红色状态；鼠标悬停红色状态可查看异常信息。
- 前端业务请求会发送 `X-Request-ID` 和 `X-User-ID`，后端响应也会返回 `X-Request-ID`。
- 账号、角色、导入任务和审计日志均持久化到 PostgreSQL。
- 审计日志可按 requestID 或 userID 查询：

```bash
curl "http://localhost:8000/api/audit-logs?request_id=<requestID>"
curl "http://localhost:8000/api/audit-logs?user_id=<userID>"
```

## Kubernetes

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/
```

K8s 镜像地址需要在 `deploy/k8s/backend.yaml` 和 `deploy/k8s/frontend.yaml` 中替换为实际镜像仓库。
