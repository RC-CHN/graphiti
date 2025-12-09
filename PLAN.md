# Graphiti 可视化与服务化改造计划

## 1. 项目背景与目标

Graphiti 目前是一个强大的 Python 知识图谱构建库，并包含一个基础的 FastAPI 服务。为了使其更易于使用和展示，我们计划将其改造为一个功能完备的独立服务，并添加一个现代化的 Web UI。

**核心目标：**
1.  **后端增强**：完善 REST API，暴露更多核心能力（如高级搜索、社区发现、批量导入），并增加鉴权机制。
2.  **前端可视化**：开发一个 Web UI，支持知识图谱的力导向图展示、节点交互与编辑、以及数据管理。

## 2. 架构设计

### 2.1 技术栈

*   **后端**: Python (FastAPI)
    *   基于现有的 `server/` 目录进行扩展。
    *   核心依赖：`graphiti-core`, `neo4j-driver`, `pydantic`.
*   **前端**: React (Vite)
    *   UI 组件库：shadcn/ui 或 Ant Design。
    *   图可视化库：`react-force-graph` (推荐，基于 ThreeJS/D3，性能好且效果酷炫) 或 `cytoscape.js`。
    *   状态管理：Zustand 或 React Context。
    *   网络请求：Axios / TanStack Query。

### 2.2 系统架构图

```mermaid
graph TD
    User[用户] --> WebUI[Web UI (React)]
    WebUI --> API[API Gateway (FastAPI)]
    
    subgraph "Backend (Graph Service)"
        API --> Auth[鉴权中间件]
        Auth --> Router[路由层]
        Router --> Controller[控制器层]
        Controller --> Graphiti[Graphiti Core]
    end
    
    Graphiti --> LLM[LLM (OpenAI/Gemini)]
    Graphiti --> DB[(Neo4j / FalkorDB)]
```

## 3. 详细实施计划

### 阶段一：后端服务增强 (Backend Enhancement)

**目标**：打造一个功能完备、安全可用的 RESTful API 服务。

1.  **鉴权机制 (Authentication)**
    *   [ ] 实现 API Key 验证中间件。
    *   [ ] 在 `.env` 中添加 `GRAPHITI_API_KEY` 配置。
    *   [ ] 为所有敏感接口添加依赖注入验证。

2.  **API 扩展 (API Expansion)**
    *   [ ] **高级搜索 (`/search/advanced`)**: 暴露 `graphiti.search_()`，支持返回完整的节点和边对象，支持过滤器。
    *   [ ] **社区发现 (`/communities/build`)**: 暴露 `graphiti.build_communities()`，支持触发社区聚类。
    *   [ ] **批量导入 (`/ingest/batch`)**: 实现真正的批量导入接口，调用 `add_episode_bulk`。
    *   [ ] **节点管理 (`/nodes`)**:
        *   `GET /nodes/{uuid}`: 获取节点详情。
        *   `GET /nodes/search`: 搜索节点（不仅是搜边）。
        *   `PATCH /nodes/{uuid}`: 更新节点属性（如手动修正消歧错误）。

3.  **CORS 配置**
    *   [ ] 配置 FastAPI 的 CORS 中间件，允许前端跨域调用。

### 阶段二：前端 Web UI 开发 (Frontend Development)

**目标**：提供直观的数据管理和酷炫的图谱可视化界面。

1.  **项目初始化**
    *   [ ] 使用 Vite + React + TypeScript 初始化项目（建议放在 `web/` 目录下）。
    *   [ ] 配置 Tailwind CSS 和基础 UI 组件库。

2.  **核心功能模块**
    *   [ ] **仪表盘 (Dashboard)**: 展示图谱概览（节点数、边数、最近更新）。
    *   [ ] **数据导入 (Ingest)**: 提供文本输入框或文件上传，调用 `/ingest` 接口。
    *   [ ] **图谱浏览器 (Graph Explorer)**:
        *   使用 `react-force-graph` 实现力导向图。
        *   支持缩放、平移、节点点击高亮。
        *   支持右侧面板显示节点/边的详细信息（属性、摘要）。
        *   支持节点搜索和过滤。
    *   [ ] **搜索与问答 (Search & QA)**:
        *   提供搜索框，调用 `/search` 接口。
        *   展示搜索结果，并联动图谱高亮相关路径。

3.  **交互增强**
    *   [ ] **节点编辑**: 在详情面板中支持修改节点属性，调用后端更新接口。
    *   [ ] **社区视图**: 可视化展示社区聚类结果。

## 4. 任务清单 (Todo List)

### 后端 (Backend)
- [ ] 添加 API Key 鉴权中间件
- [ ] 实现 `/search/advanced` 接口
- [ ] 实现 `/communities/build` 接口
- [ ] 实现 `/ingest/batch` 接口
- [ ] 实现节点 CRUD 接口
- [ ] 配置 CORS

### 前端 (Frontend)
- [ ] 初始化 React 项目结构
- [ ] 实现 API Client 封装
- [ ] 开发 Force Graph 可视化组件
- [ ] 开发节点详情侧边栏
- [ ] 开发数据导入页面
- [ ] 开发搜索页面

## 5. 预期成果

*   一个可以独立部署的 Docker 容器，包含后端服务。
*   一个现代化的 Web 界面，用户可以通过它直观地看到知识图谱的生长过程，并进行交互式探索。