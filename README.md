# A股主题热度分析

一个完整可运行的全栈项目，用于追踪 A 股行业板块与概念板块的周度热度。后端通过 AKShare 获取板块成分和个股行情，按周计算主题评分；前端提供产品化看板展示排行榜、评分趋势和成分股表现。

## 技术栈

- 前端：Next.js 14 + App Router + TailwindCSS + ECharts
- 后端：FastAPI + SQLAlchemy + APScheduler
- 数据库：PostgreSQL
- 数据源：AKShare
- 部署：Docker + Docker Compose + Nginx

## 目录结构

```text
.
├─ backend
│  ├─ app
│  │  ├─ api
│  │  ├─ core
│  │  ├─ db
│  │  ├─ models
│  │  ├─ schemas
│  │  ├─ services
│  │  └─ tasks
│  ├─ Dockerfile
│  └─ requirements.txt
├─ frontend
│  ├─ app
│  ├─ components
│  ├─ lib
│  └─ Dockerfile
├─ nginx
│  └─ default.conf
├─ .env.example
├─ deploy.sh
├─ docker-compose.yml
└─ README.md
```

## 核心功能

- 支持行业板块与概念板块双类型主题管理
- 自动同步板块成分股
- 拉取个股日行情：收盘价、涨跌幅、成交额
- 周度主题热度评分：
  - 成交额占比
  - 平均涨幅
  - 中位数涨幅
  - 上涨股票占比
  - 连续强势周数
- REST API：
  - `GET /api/themes`
  - `GET /api/themes/{id}`
  - `GET /api/rankings`
  - `POST /api/compute`
  - `GET /api/compute`
  - `GET /api/compute/{job_id}`
- 前端首页看板与详情页图表
- 每周定时计算一次评分
- 支持分批同步、后台任务与断点续跑

## 评分逻辑

每周按主题对成分股最新周内表现做汇总，输出 `0-100` 综合评分。第一版采用可解释的固定权重：

- 资金强度 `30%`
- 涨幅表现 `30%`
- 上涨占比 `20%`
- 连续强势 `20%`

状态分层：

- `surging`：`>= 80`
- `hot`：`>= 65`
- `warm`：`>= 50`
- `cold`：`< 50`

## 快速启动

### 1. 准备环境变量

```bash
cp .env.example .env
```

### 2. 启动全部服务

```bash
docker compose up --build
```

启动完成后访问：

- 前端看板：`http://localhost`
- API 健康检查：`http://localhost/health`

## 初始化数据

首次启动后数据库为空，需要触发一次后台同步任务：

```bash
curl -X POST http://localhost/api/compute
```

查看任务状态：

```bash
curl http://localhost/api/compute
```

说明：

- 首次同步会按批次在后台逐步抓取，接口会立即返回任务状态。
- 服务重启后会自动恢复未完成任务。
- AKShare 数据接口存在外部波动时，部分板块可能同步失败，但不会阻塞整体任务。

## 定时任务

后端内置 APScheduler，每周执行一次评分计算。默认配置：

- 星期日
- `18:00`
- 时区：`Asia/Shanghai`

可通过 `.env` 修改：

- `SCHEDULER_CRON_DAY_OF_WEEK`
- `SCHEDULER_CRON_HOUR`
- `SCHEDULER_CRON_MINUTE`
- `COMPUTE_BATCH_SIZE`
- `COMPUTE_BATCH_PAUSE_SECONDS`

## 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`

## Docker 服务说明

- `db`：PostgreSQL 16
- `backend`：FastAPI 服务
- `frontend`：Next.js 服务
- `nginx`：统一入口，代理 `/api` 和页面请求

## 部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动：

- 检查 `.env`
- 构建镜像
- 启动全部服务

## 注意事项

- 本项目优先保证“可跑通”，没有引入 Celery、Redis 等额外依赖。
- 周度评分当前基于每只成分股在周内最新交易日数据计算，适合做第一版主题热度看板。
- 如果后续要增强准确性，可以继续加入更多因子，例如换手率、龙头股权重、连板强度等。
