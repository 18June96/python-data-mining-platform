# Python数据挖掘实战平台技术文档
## 一、项目概括
### 1.1 项目简介
　　Python数据挖掘实战平台是一个基于Streamlit构建的交互式学习环境，目的是为Python数据挖掘学习者提供代码学习、实践运行和AI辅助教学功能。平台支持多章节组织、代码编辑运行、知识点AI生成和智能问答等功能。
### 1.2 核心功能
　　1. 多章节管理：自动识别和展示章节文件夹结构；  
　　2. 代码展示与编辑：实时查看和编辑Python代码；   
　　3. AI辅助教学：自动生成知识点总结和智能问答；  
　　4. 在线代码执行：直接在浏览器中运行Python代码；  
　　5. 数据文件预览：支持CSV、Excel、TXT等数据文件预览；  
　　6. 交互式学习：提供代码修改、运行、重置等交互功能。  
## 二、技术架构
　　核心框架: Streamlit (Web界面构建与交互)；  
　　AI服务: 硅基流动API (用于知识点生成和智能问答)；  
　　数据处理: Pandas、NumPy (数据操作与计算)；  
　　文件管理: Python内置os模块 (目录遍历与文件操作)；  
　　代码执行: Python exec()函数配合contextlib (沙箱式代码运行环境)。  
## 三、核心功能模块
该系统的执行流程分为五个主要阶段：**章节发现、代码加载、AI知识点生成、交互式编辑运行和智能问答。**
### 3.1 章节发现与文件管理模块  
**功能:** 自动识别和组织学习章节及对应文件  
实现逻辑:  
　　目录扫描: 使用os.listdir()遍历当前工作目录；  
　　章节筛选: 通过文件名匹配规则（包含"第"和"章"字符或以数字开头）识别章节文件夹；  
　　文件获取: 在每个章节文件夹内筛选.py扩展名的教学文件；  
　　内容读取: 使用UTF-8编码读取Python文件内容。  
### 3.2 AI知识点生成模块  
**功能:** 调用AI服务自动分析代码并生成知识点总结  
实现逻辑:  
　　API配置: 连接硅基流动平台，使用glm-4-9b-chat模型；  
　　内容分析: 将代码片段（前3000字符）发送给AI模型；  
　　结构化输出: 要求AI按"功能概述-核心知识点-扩展应用"结构生成教学内容；  
　　缓存机制: 使用@st.cache_data和st.session_state双重缓存减少API调用。  
```python
# 使用硅基流动API生成知识点
def generate_knowledge_with_ai(py_content, py_file, chapter_folder):  
    import requests
    
    # 硅基流动平台的API配置
    api_key = "你的API密钥"  # API密钥
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建分析请求
    prompt = f"""作为Python数据挖掘教学助手，请分析以下Python代码，生成详细的知识点讲解：
        - 文件名称：{py_file}
        - 所属章节：{chapter_folder}
        {py_content[:3000]}  # 限制代码长度，避免超出token限制
        请按照以下结构生成知识点讲解：
        代码功能概述：简要说明这段代码的主要功能
        核心知识点：列出代码中涉及的主要Python/数据挖掘知识点
        扩展应用：说明这些知识在实际项目中的应用场景
        要求：
        使用中文回答，语言简洁明了，适合初学者理解，重点突出，结构清晰
        """
    data = {
        "model": "THUDM/glm-4-9b-chat",  # 硅基流动上的模型
        "messages": [
            {
                "role": "system", 
                "content": "你是一位资深的Python数据挖掘教学专家，擅长用简洁易懂的语言整理代码知识点，生成的内容美观，文本在不超过500字"
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        }
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content']
            return ai_content
        else:
            return f"#调用失败 (状态码: {response.status_code})\n响应内容: {response.text[:500]}"
    except requests.exceptions.Timeout:
        return "## ⏰ 请求超时，请稍后重试"
    except requests.exceptions.ConnectionError:
        return "## 🔌 网络连接失败，请检查网络"
    except Exception as e:
        return f"## ❌ AI生成失败: {str(e)}"    
```
### 3.3 代码执行环境模块  
**功能:** 提供安全的在线代码编辑和运行环境  
实现逻辑:  
　　沙箱准备: 临时切换工作目录到对应章节文件夹；  
　　环境配置: 创建包含pandas、numpy等库的安全执行环境；  
　　代码执行: 使用exec()函数在受限环境中运行用户代码；  
　　输出捕获: 通过contextlib.redirect_stdout捕获所有标准输出和错误信息；  
　　目录恢复: 执行完成后恢复原始工作目录。   
### 3.4 智能问答模块  
**功能:** 基于当前代码内容提供上下文感知的AI问答  
实现逻辑:  
　　上下文构建: 将当前代码内容、AI生成的知识点和用户问题组合为提示词；  
　　API调用: 发送到硅基流动API获取针对性回答；  
　　对话管理: 维护最近5条对话历史，支持对话清空；  
　　缓存优化: 基于代码内容的MD5哈希值缓存问答结果。  
```python
def ask_ai_question(py_content, knowledge, question, chapter_folder, py_file):
    """
    基于代码上下文进行智能问答
    """
    import requests
    
    # 系统提示词定义AI角色
    system_prompt = """你是一位Python数据挖掘教学助手，专门帮助学生理解代码和解答问题。
    基于提供的代码内容和知识点，回答用户的问题。
    
    要求：
    1. 回答要具体，结合代码示例
    2. 用简洁易懂的中文解释
    3. 如果涉及代码修改，提供可运行的代码片段
    4. 鼓励学生思考和动手实践
    5. 如果问题不清晰，可以请求澄清
    """
    
    # 构建包含上下文的用户提示词
    user_prompt = f"""请基于以下信息回答我的问题：
    【代码信息】
    - 文件：{py_file}
    - 章节：{chapter_folder}
    
    【代码内容】
    {py_content[:2000]}
    
    【知识点总结】
    {knowledge[:1000]}
    
    【我的问题】
    {question}
    
    请给出详细、具体的回答，可以结合代码示例解释。"""
    
    data = {
        "model": "THUDM/glm-4-9b-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 800,  # 问答可以更长一些
    }
    
    # 发送请求并处理响应（类似知识点生成）
    # ...
```
### 3.5 数据文件预览模块  
**功能:** 动态预览章节配套的数据文件内容  
实现逻辑:  
　　文件发现: 扫描章节文件夹内的CSV、Excel、TXT文件；  
格式适配:  
　　CSV文件: 尝试utf-8和gbk两种编码；  
　　Excel文件: 使用pandas.read_excel读取；  
　　文本文件: 直接读取文本内容。  
内容展示:  
　　表格数据: 显示前10行及数据形状；  
　　文本数据: 显示前1000字符；  
　　交互控制: 使用可折叠面板和会话状态管理预览开关。  
## 四、界面设计效果
<img width="1860" height="909" alt="image" src="https://github.com/user-attachments/assets/73708bde-06b9-4908-953b-483c06eb5853" />

## 五、注意事项  
### 5.1 配置  
　　安装依赖：pip install streamlit pandas numpy requests；  
　　配置API密钥：在代码中填入硅基流动API密钥；  
### 5.2 文件要求   
　　章节文件夹：命名为 **"第1章_xxx"** 或数字开头；  
　　代码文件：**.py** 格式，包含完整可执行代码；  
　　数据文件：支持.csv、.xlsx、.txt格式；  
### 5.3 常见问题  
　　AI生成慢：**首次生成需10-30秒**；  
　　无代码输出：确保代码中有print语句；  
　　中文乱码：数据文件尝试UTF-8或GBK编码；  
### 5.4 重要提示  
　　保持网络连接（需调用AI服务）；  
　　生产环境建议配置环境变量存储API密钥；  
## 六、总结
　　本Python数据挖掘实战平台是一个基于Streamlit的交互式学习系统，它通过自动化章节管理、AI智能辅助和在线代码执行，实现了 **“代码展示-知识点解析-实践运行”** 的一体化学习体验。系统能够自动识别章节结构，实时分析Python代码并生成知识点总结，提供安全的在线编辑运行环境，并支持基于上下文的智能问答，有效解决了传统编程学习中理论与实践脱节的问题，为数据挖掘学习者提供了一个高效、直观且可交互的全新学习平台。
