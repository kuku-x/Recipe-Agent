# AI菜谱知识图谱生成器 - Web界面

基于Kimi大模型的智能菜谱解析系统，提供友好的Web界面进行菜谱解析和批量处理。

## 🌟 功能特性

- **🤖 AI智能解析**: 使用Kimi大模型准确提取菜谱信息
- **📝 单个菜谱解析**: 支持粘贴Markdown格式的菜谱内容进行解析
- **📚 批量处理**: 支持大规模菜谱目录的批量转换
- **📊 实时进度**: 显示处理进度和状态
- **🔍 结果查看**: 查看和搜索已处理的菜谱
- **💾 多格式导出**: 支持Neo4j、CSV等多种输出格式
- **⚙️ 配置管理**: 通过Web界面配置API密钥和参数

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

有两种方式配置Kimi API密钥：

**方式一：通过Web界面**
1. 启动Web服务器（见下文）
2. 在浏览器中打开 http://localhost:5000
3. 进入"系统配置"页面
4. 输入您的Kimi API密钥并保存

### 3. 启动Web服务器

**Windows系统：**
```bash
start_web.bat
```


### 4. 访问Web界面

在浏览器中打开: http://localhost:5000

## 📖 使用指南

### 首页

- 查看系统功能介绍
- 快速访问各个功能模块

### 菜谱解析

1. 在"菜谱解析"页面
2. 粘贴Markdown格式的菜谱内容
3. 可选：输入文件路径（用于自动分类）
4. 点击"解析菜谱"按钮
5. 查看解析结果，包括：
   - 菜谱基本信息（名称、难度、分类等）
   - 食材列表（名称、用量、单位、分类）
   - 烹饪步骤（描述、方法、工具）
   - 标签和营养信息

### 批量处理

1. 在"批量处理"页面
2. 输入菜谱目录路径（例如：`/path/to/HowToCook-master/dishes`）
3. 选择处理选项：
   - 自动导出：处理完成后自动导出数据
   - 遇到错误继续：遇到错误时继续处理其他文件
4. 点击"开始处理"按钮
5. 实时查看处理进度：
   - 当前进度百分比
   - 当前处理的文件
   - 已处理数量
   - 失败数量
   - 总文件数量

### 处理结果

1. 在"处理结果"页面查看所有已处理的菜谱
2. 使用搜索功能查找特定菜谱
3. 使用筛选功能按分类或难度筛选
4. 导出数据：
   - Neo4j格式：用于导入Neo4j图数据库
   - CSV格式：标准CSV文件
   - RF2格式：RF2标准格式

### 系统配置

在"系统配置"页面可以配置：

**API配置：**
- Kimi API密钥
- API基础URL
- API模型名称

**处理配置：**
- 批次大小：每次处理的文件数量
- 请求间隔：API调用之间的延迟时间

**输出配置：**
- 输出目录：数据保存的路径
- 输出格式：默认的导出格式

## 📁 项目结构

```
agent(代码系ai生成)/
├── web_server.py              # Flask Web服务器！
├── recipe_ai_agent.py         # AI解析核心引擎！
├── run_ai_agent.py            # 命令行运行脚本！
├── batch_manager.py           # 批次管理工具！
├── amount_normalizer.py       # 用量标准化工具！
├── config.json                # 配置文件！
├── requirements.txt           # 依赖列表！
├── start_web.bat              # Windows启动脚本！
├── templates/                 # HTML模板！
│   └── index.html            # 主页面
├── static/                    # 静态文件！
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── js/
│       └── app.js            # JavaScript逻辑
└── ai_output/                 # 输出目录
    ├── nodes.csv             # Neo4j节点数据
    ├── relationships.csv     # Neo4j关系数据
    └── neo4j_import.cypher   # Neo4j导入脚本
```

## 🔌 API接口

Web服务器提供以下REST API接口：

### 系统状态
- `GET /api/status` - 获取系统状态
- `GET /api/config` - 获取配置信息
- `POST /api/config` - 保存配置信息

### 菜谱解析
- `POST /api/parse-recipe` - 解析单个菜谱
- `POST /api/batch-process` - 批量处理菜谱
- `GET /api/progress` - 获取处理进度
- `POST /api/stop` - 停止处理

### 数据管理
- `GET /api/recipes` - 获取已处理的菜谱列表
- `POST /api/export` - 导出数据
- `GET /api/categories` - 获取菜谱分类

### 连接测试
- `POST /api/test-connection` - 测试API连接

## 🎯 使用场景

### 1. 菜谱网站构建
- 自动分类和标签
- 智能推荐系统
- 营养分析

### 2. 烹饪应用开发
- 食材识别
- 步骤指导
- 工具推荐

### 3. 营养研究
- 食材营养分析
- 膳食搭配研究
- 健康饮食推荐

### 4. 餐饮业务
- 菜单优化
- 成本分析
- 客户偏好分析

## 🔍 故障排除

### 常见问题

1. **API密钥错误**
   ```
   错误: API调用失败: 401
   解决: 检查API密钥是否正确配置
   ```

2. **网络连接问题**
   ```
   错误: API调用超时
   解决: 检查网络连接，或增加timeout设置
   ```

3. **JSON解析错误**
   ```
   错误: JSON解析错误
   解决: AI响应格式异常，会自动使用备用解析方法
   ```

4. **菜谱格式问题**
   ```
   错误: 无法提取菜谱信息
   解决: 检查Markdown格式是否符合要求
   ```

### 调试模式

查看服务器控制台输出的详细日志信息。

## 📊 性能优化

### API调用优化

1. **合理的请求频率**: 默认每秒1次请求，避免API限制
2. **错误重试机制**: 自动重试失败的请求
3. **批量处理**: 分批处理大量菜谱文件

### 内存优化

1. **流式处理**: 逐个处理菜谱文件，避免内存溢出
2. **定期清理**: 处理完成后及时释放内存
3. **进度监控**: 实时显示处理进度

## 🌐 扩展开发

### 添加新的AI模型

```python
class CustomAIAgent(KimiRecipeAgent):
    def __init__(self, api_key, model_name="custom-model"):
        super().__init__(api_key)
        self.model_name = model_name
    
    def call_custom_api(self, messages):
        # 实现您的自定义AI调用逻辑
        pass
```

### 支持新的输出格式

```python
def export_to_custom_format(self, output_dir):
    """导出为自定义格式"""
    # 实现您的导出逻辑
    pass
```

## 📋 技术栈

- **后端**: Python + Flask
- **前端**: HTML5 + CSS3 + JavaScript
- **AI模型**: Kimi (Moonshot AI)
- **数据处理**: Pandas
- **图数据库**: Neo4j (可选)

## 📄 许可证

本项目遵循原项目的许可证。

## 🙏 致谢

感谢Kimi大模型提供的强大AI能力！

---

**享受AI驱动的菜谱知识图谱构建体验！** 🎉