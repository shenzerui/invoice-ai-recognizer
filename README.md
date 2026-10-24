# 票据识别管理系统

> 本系统仅辅助识别，不对接国税查验接口，识别结果仅供参考。

本地运行的票据识别管理系统：**Vue3 + Element Plus 前端**、**Python FastAPI 后端**、**SQLite 本地数据库**。

---

## 功能清单

| # | 功能 | 说明 |
|---|------|------|
| 1 | 图片上传 | 支持 jpg/png，支持单张、批量上传 |
| 2 | AI 识别票据类型 | 增值税专票 / 普票、电子普票、定额发票、火车票、汽车票、通行费票据 |
| 3 | 结构化字段提取 | 区分不同票据模板，按类型填充特有字段（如火车票的车次席别） |
| 4 | 用户密钥配置 | 设置页面自行填入 OCR / LLM API Key，请求走用户自己的 Key |
| 5 | 金额逻辑校验 | 价税合计 = 金额 + 税额，异常自动标红提醒 |
| 6 | 重复检测 | 发票代码 + 号码 唯一索引，自动防止重复报销 |
| 7 | 本地存储 + 搜索 | 图片 + 识别结果保存本地，按时间/类型/关键词搜索历史 |
| 8 | 导出 | 支持导出 Excel（金额异常行标红）和 JSON |
| 9 | 标签 + 备注 | 给每张票据添加自定义标签、备注 |
| 10 | 免责声明 | 页面顶部显著位置提示"本系统仅辅助识别" |

---

## 技术栈

```
前端：Vue 3 + Vue Router 4 + Element Plus + Vite + Axios
后端：Python 3.10+ + FastAPI + SQLAlchemy (async) + aiossqlite
数据库：SQLite（单文件 data/invoices.db，无需额外服务）
OCR 适配：百度智能云 OCR / 通用 LLM（兼容 OpenAI 请求格式）
```

---

## 项目结构

```
invoice-recognizer/
├── backend/                      # FastAPI 后端
│   ├── main.py                   # 应用入口
│   ├── requirements.txt          # Python 依赖
│   ├── app/
│   │   ├── config.py             # 全局配置（路径、票据类型枚举）
│   │   ├── database.py           # SQLAlchemy 异步连接
│   │   ├── models/               # ORM 模型（Invoice）
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── api/                  # FastAPI 路由层
│   │   │   ├── settings.py       # /api/settings → 密钥配置
│   │   │   ├── upload.py         # /api/upload → 上传识别
│   │   │   └── invoices.py       # /api/invoices → CRUD/搜索/导出
│   │   ├── services/             # 业务逻辑层
│   │   │   ├── ocr_service.py    # 上传→OCR→解析→校验→入库 整条链路
│   │   │   └── invoice_service.py # 历史记录搜索/更新/删除/导出
│   │   ├── ocr/                  # OCR 适配器 + 票据解析
│   │   │   ├── adapter.py        # 抽象基类 + 工厂方法
│   │   │   ├── baidu_adapter.py  # 百度 OCR 实现
│   │   │   ├── llm_adapter.py    # 通用 LLM 实现（Vision）
│   │   │   ├── mock_adapter.py   # 未配密钥时的本地演示适配器
│   │   │   └── parser.py         # 不同票据类型的字段解析器
│   │   └── utils/                # 工具函数
│   │       ├── settings_manager.py # JSON 文件读写
│   │       ├── validator.py        # 金额逻辑校验
│   │       └── exporter.py         # Excel / JSON 导出
│   ├── uploads/                  # 票据图片本地存储
│   └── data/
│       ├── invoices.db           # SQLite 数据库（自动创建）
│       └── settings.json         # 用户 OCR / LLM 密钥（本地文件）
│
└── frontend/                     # Vue3 前端
    ├── package.json
    ├── vite.config.js            # 开发代理 /api → 后端 8000
    ├── index.html
    └── src/
        ├── main.js               # Vue 入口
        ├── App.vue               # 根组件（左侧菜单 + 顶部标题 + 主区域）
        ├── router/index.js       # 路由配置
        ├── api/                  # 后端 API 封装
        │   ├── index.js          # axios 实例 + 拦截器
        │   ├── upload.js
        │   ├── invoices.js
        │   └── settings.js
        └── views/                # 页面组件
            ├── Dashboard.vue      # 首页（统计概览 + 最近记录）
            ├── Upload.vue        # 上传识别（单张 / 批量）
            ├── History.vue       # 历史记录（搜索 / 编辑 / 删除 / 导出）
            ├── InvoiceDetail.vue # 票据详情
            └── Settings.vue      # 密钥配置
```

---

## 快速启动

### 🎯 方式一：一键启动（推荐）

双击项目根目录下的 `启动.bat`，脚本会自动：
1. 检测 Python / Node.js 环境
2. 首次运行自动安装前后端依赖（后续跳过）
3. 同时拉起后端（8000）和前端（5173）
4. 自动打开浏览器 http://localhost:5173

> 停止服务：关闭弹出的两个命令行窗口即可。

### 方式二：手动启动（开发者调试用）

#### 1. 启动后端（FastAPI）

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate        # Windows PowerShell
# source venv/bin/activate   # macOS / Linux

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 或：uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后访问：
- API 文档（Swagger UI）：http://localhost:8000/docs
- API 文档（ReDoc）：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/

### 2. 启动前端（Vue3）

```bash
cd frontend

# 安装依赖
npm install
# 如果网络慢，可以用国内镜像：
# npm install --registry https://registry.npmmirror.com

# 启动开发服务器
npm run dev
```

浏览器会自动打开 http://localhost:5173

> Vite 已配置开发代理，前端的 `/api/*` 和 `/uploads/*` 会自动转发到后端 `localhost:8000`，开发时无需处理跨域。

### 3. 配置 OCR（可选）

首次启动后直接可以用 —— 系统内置 **Mock 适配器**，未配置密钥时会返回模拟识别结果。

如需真实识别：
1. 进入"系统设置"页面
2. 选择 OCR 提供商（百度 OCR 或通用 LLM）
3. 填入 API Key / Secret Key
4. 保存即可

---

## API 接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload/single` | 单张图片识别 + 入库 |
| POST | `/api/upload/batch` | 批量图片识别 + 入库 |
| GET  | `/api/invoices` | 票据列表（分页 + 多条件筛选） |
| GET  | `/api/invoices/types` | 获取支持的票据类型枚举 |
| GET  | `/api/invoices/{id}` | 单条票据详情 |
| PUT  | `/api/invoices/{id}` | 更新票据（标签、备注、金额等） |
| DELETE | `/api/invoices/{id}` | 删除票据（连同图片） |
| GET  | `/api/invoices/{id}/image` | 获取票据图片 |
| GET  | `/api/invoices/export/excel` | 导出 Excel（金额异常行自动标红） |
| GET  | `/api/invoices/export/json` | 导出 JSON |
| GET  | `/api/settings` | 读取当前设置（密钥只返回是否已配置） |
| PUT  | `/api/settings` | 更新 OCR / LLM 密钥 |
| GET  | `/api/settings/test` | 测试当前 OCR 适配器 |

所有 `/api/*` 接口完整文档请访问 http://localhost:8000/docs

---

## 数据模型设计说明

### 为什么用一张表存所有票据类型？

```
invoices 表:
  ├── 公共字段（独立列）：id, ticket_type, invoice_code, invoice_number,
  │   amount, tax, total_amount, invoice_date, buyer, seller ...
  └── type_extra (JSON)：各票据类型特有字段
      ├── 火车票: {"起始站":"北京南", "到达站":"上海虹桥", "车次":"G123", "席别":"二等座"}
      ├── 定额发票: {"票面金额": 100, "收款单位": "..."}
      └── 通行费: {"入口": "高速入口", "出口": "高速出口"}
```

**好处**：
- 新增票据类型 → 只在 `parser.py` 里加一个解析函数，**不改数据库结构**
- 避免多表 JOIN，查询、搜索、导出都简单
- 答辩时容易讲清楚这个设计决策

### 为什么密钥存 JSON 文件而不是数据库？

- 密钥属于"配置"而非"业务数据"
- JSON 文件用户可以直接看到、手动备份
- 后端启动会自动兜底默认值，零配置也能跑起来演示

### 为什么 Mock 适配器重要？

- 答辩现场如果网络不好或 Key 过期，Mock 能保证全流程跑通
- Mock 的返回格式和真实 OCR 完全一致，前端不用做"演示模式"判断

---

## 常见问题

### Q: 没配密钥能识别吗？
A: 能。Mock 适配器会返回模拟数据，全流程（上传→识别→入库→查询→导出→校验）都能跑通。

### Q: 为什么识别结果金额校验标红了？
A: OCR 识别可能有误差（比如把 `1390.79` 识别成 `1390.70`），系统检测到价税合计 ≠ 金额 + 税额 就会标红。可以在"历史记录 → 编辑"里手动修正。

### Q: 图片和数据库存在哪里？
A: 都在 `backend/` 目录下 —— `uploads/` 存图片，`data/invoices.db` 存 SQLite，`data/settings.json` 存密钥。这三个目录整体打包就是完整数据备份。

### Q: 支持哪些票据类型？
A: 增值税专票、增值税普票、电子普通发票、定额发票、火车票、汽车票、通行费票据、未知（兜底）。扩展新类型见下方。

---

## 扩展指南

### 新增票据类型

1. `backend/app/config.py` → 在 `TICKET_TYPES` 里加一行（如 `"airline": "机票"`）
2. `backend/app/ocr/parser.py` → 写一个 `_parse_airline_extra(raw)` 函数，加到 `_TYPE_EXTRA_PARSERS`
3. 前端 Element Plus 的 tag type 映射加一下即可

### 新增 OCR 服务提供商（如腾讯 OCR）

1. 在 `backend/app/ocr/` 下新建 `tencent_adapter.py`，实现 `OCRAdapter` 抽象类的 `recognize()` 方法
2. 在 `adapter.py` 的 `get_adapter()` 工厂方法里加一个分支
3. 前端设置页的 `ocr_provider` 选项里加一个 radio

### 换数据库（如 MySQL / PostgreSQL）

SQLAlchemy 异步引擎只需换连接串，SQLAlchemy 的 ORM 不关心底层数据库。把 `config.py` 里的 `SQLALCHEMY_DATABASE_URL` 改成对应格式 + 安装驱动即可。

---

## 启动一键脚本（Windows PowerShell）

```powershell
# 后端
cd backend
pip install -r requirements.txt
Start-Process python -ArgumentList "main.py" -NoNewWindow
cd ..

# 前端
cd frontend
npm install
Start-Process npm.cmd -ArgumentList "run dev" -NoNewWindow
```

之后浏览器打开 http://localhost:5173 即可使用。

---

## License

MIT —— 本地学习 / 答辩演示用途。
