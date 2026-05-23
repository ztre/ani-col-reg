# 番剧收藏登记系统

这是一个基于 SQLite 的全栈番剧收藏工具，用于按季度检索动画条目、把来源站封面缓存到本地，并维护自己的收藏整理记录。

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、HTTPX、BeautifulSoup
- 前端：Vue 3、Vite、Element Plus
- 测试：Pytest

## Docker 快速启动

项目当前面向 Linux 容器环境部署。

```bash
cp .env.example .env
docker compose up --build
```

启动后可以访问：

- App: `http://localhost:8060`
- Health check: `http://localhost:8060/health`
- API docs: `http://localhost:8060/docs`

容器运行数据会保存在 `${ANI_COL_ROOT_DIR}/data`，并挂载到容器内的 `/app/data`。

## 本地 Linux 开发

首次开发时，先复制一份共享默认配置：

```bash
cp .env.example .env
```

默认本地端口：

- Backend: `http://localhost:8060`
- Frontend dev server: `http://localhost:5173`
- Vite proxy target: `http://localhost:8060`

根目录 `.env` 中与 Docker 相关的常用字段：

- `PUID` / `PGID`：容器运行时用户和用户组映射
- `ANI_COL_ROOT_DIR`：宿主机运行目录根路径，默认是 `./runtime`
- `ANI_COL_PORT`：本地后端和 Docker 端口映射共用的应用端口

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python run.py
```

默认数据库会创建在 `backend/data/ani_col_reg.sqlite3`。

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器端口由 `VITE_DEV_SERVER_PORT` 控制，默认值是 `5173`。
`/api` 和 `/health` 的代理目标优先读取 `VITE_API_BASE_URL`，未设置时回退到 `http://localhost:${ANI_COL_PORT}`。


## API

- `GET /api/anime`
- `POST /api/anime/search`
- `GET /api/anime/{id}`
- `POST /api/collection`
- `PATCH /api/collection/{id}`
- `POST /api/mapping/mgr-ani-ml`

更多接口和数据结构说明可查看 `doc/api.md` 与 `doc/database.md`。
