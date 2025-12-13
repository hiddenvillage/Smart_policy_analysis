# 保险团单解读系统

基于Django框架的保险团单解读Web服务，支持文件上传、异步处理和状态查询功能。

## 功能特性

1. **团单解读功能**
   - 支持PDF合同文件上传（1个）
   - 支持PNG报价单文件上传（最多30个）
   - 异步处理任务，实时更新进度
   - 支持进度状态查询（每2秒轮询）

2. **表单管理功能**
   - 创建、查询、更新、删除团单解读记录
   - 支持批量删除
   - 支持内容编辑和更新
   - 分页展示功能

3. **技术特点**
   - 使用PyMySQL替代Django原生ORM
   - Python原生异步任务处理（asyncio）
   - RESTful API设计
   - 响应式前端界面

## 系统要求

- Python 3.8+
- MySQL 5.7+

**注意：** 本项目使用Python内置的asyncio进行异步处理，不再需要Redis和Celery。

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

在项目根目录的 `config.ini` 文件中修改数据库配置：

```ini
[database]
host = localhost
port = 3306
user = root
password = password
database = insurance_db
charset = utf8mb4
```

### 3. 创建数据库

```sql
CREATE DATABASE insurance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**注意：** 项目现在从 `config.ini` 配置文件读取数据库参数，而不是硬编码在 settings.py 中。

### 4. 初始化数据库表

```bash
python3 manage.py init_db
```

或运行初始化脚本：

```bash
python init_database.py
```

### 5. 启动服务

方式一：使用Django命令

```bash
python3 manage.py runserver 0.0.0.0:8081
```

方式二：使用一键启动脚本（自动初始化数据库）

```bash
python3 run_server.py
```

### 6. 验证安装（可选）

运行测试脚本验证异步处理功能是否正常：

```bash
python test_async_implementation.py
```

**注意：** 异步任务会在后台线程中自动执行，无需手动启动额外的服务。

## API接口

### 1. 启动团单解读

**接口地址：** `POST /api/interpretation/start/`

**请求参数：**
- `task_name` (必填): 任务名称
- `company` (必填): 企业名称
- `scene` (必填): 场景类型
- `pdf_file` (必填): PDF合同文件
- `png_files` (可选): PNG报价单文件列表

**返回示例：**
```json
{
    "success": true,
    "task_id": "T2025121000001ABC",
    "message": "Group order interpretation task started successfully"
}
```

### 2. 查询任务状态

**接口地址：** `GET /api/interpretation/status/`

**查询参数：**
- `task_name` (必填): 任务名称
- `company` (必填): 企业名称
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页大小，默认10

**返回示例：**
```json
{
    "success": true,
    "data": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "data": [
            {
                "id": 1,
                "task_id": "T2025121000001ABC",
                "task_name": "团健险智配_20251210_001",
                "company": "北京某科技有限公司",
                "scene": "团健险解读与智配",
                "progress": "100%",
                "status": "完成",
                "llm_content": "{...}",
                "update_content": null,
                "create_time": "2025-12-10 10:30:00"
            }
        ]
    }
}
```

### 3. 更新表单内容

**接口地址：** `POST /api/forms/update/`

**请求参数：**
- `task_id` (必填): 任务ID
- `content` (必填): 更新内容

### 4. 删除表单

**接口地址：** `DELETE /api/forms/<task_id>/delete/`

### 5. 批量删除表单

**接口地址：** `DELETE /api/forms/delete-batch/`

**请求参数：**
- `task_ids` (必填): 任务ID列表

### 6. 获取表单详情

**接口地址：** `GET /api/forms/<task_id>/`

## 前端使用

访问 `http://localhost:8000` 即可使用前端界面。

### 主要功能页面

1. **场景选择页面**
   - 选择不同的保险场景（团健险、团寿险、团产险）

2. **创建任务页面**
   - 填写任务信息
   - 上传PDF和PNG文件
   - 启动解读任务

3. **任务列表页面**
   - 查看所有任务状态
   - 实时更新进度
   - 支持编辑、查看详情、导出等操作

4. **数据分析页面**
   - BadCase分析
   - 数据可视化展示

## 项目结构

```
Smart_policy_analysis/
├── insurance_project/          # Django项目主目录
│   ├── __init__.py
│   ├── settings.py            # Django配置文件
│   ├── urls.py                # 主路由配置
│   ├── wsgi.py                # WSGI配置
│   ├── asgi.py                # ASGI配置
│   ├── core/                  # 核心业务模块
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── database.py        # 数据库连接和SQL操作
│   │   ├── form_service.py    # 表单业务逻辑
│   │   └── management/
│   │       └── commands/
│   │           └── init_db.py # 数据库初始化命令
│   ├── api/                   # API模块
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py           # API视图
│   │   ├── urls.py            # API路由
│   │   └── tasks.py           # 异步任务模块
│   ├── templates/             # HTML模板
│   │   └── index.html         # 主页面
│   └── static/                # 静态文件
├── config.ini                 # 数据库配置文件
├── manage.py                  # Django管理脚本
├── init_database.py          # 数据库初始化脚本
├── run_server.py             # 一键启动脚本
├── test_async_implementation.py # 异步功能测试脚本
├── requirements.txt          # Python依赖
├── base.html                 # UI参考文件
└── README.md                 # 项目说明
```

## 注意事项

1. **文件上传限制**
   - PDF文件：1个，必填
   - PNG文件：最多30个，可选
   - 单个文件大小：不超过50MB

2. **数据库配置**
   - 数据库配置从 `config.ini` 文件读取，不再硬编码在代码中
   - 确保MySQL服务已启动
   - 数据库字符集使用utf8mb4
   - 创建数据库用户并授权

3. **异步处理**
   - 使用Python内置的asyncio进行异步任务处理
   - 异步任务在后台线程中执行，不阻塞主线程
   - LLM返回的JSON数据会自动保存到llm_content字段

## 故障排除

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 检查数据库配置是否正确
   - 确认数据库用户权限

2. **文件上传失败**
   - 检查MEDIA目录权限
   - 确认文件大小限制
   - 检查文件格式是否正确

3. **任务处理失败**
   - 查看Django日志
   - 检查异步任务执行状态
   - 运行测试脚本验证异步功能