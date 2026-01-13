# streamlit run 03谢卓君.py
import streamlit as st
import os
import pandas as pd
import numpy as np
import io
import contextlib
import hashlib
from datetime import datetime

# =页面配置 
st.set_page_config(
    page_title="03谢卓君_Python数据挖掘实战",
    page_icon="❀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    h1, h2, h3 { color: #2E4057; font-family: "Microsoft YaHei", sans-serif; }
    .sidebar .sidebar-content { background-color: #F8F9FA; padding-top: 1rem; }
                               
    /* 添加淡紫色背景 */
    .stApp {
        background-color: #E6E6FA;
    }
    </style>
    """, unsafe_allow_html=True)

# 定义核心函数
# 获取所有章节文件夹
def get_chapter_folders():
    folders = []
    current_dir = os.getcwd()
    try:
        # 查找所有以"第"开头或以数字开头的文件夹
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path):
                # 匹配章节文件夹：如"第三章"、"第2章"、"Chapter 3"、"3. xxx"等
                if ("第" in item and "章" in item) or item[0].isdigit():
                    folders.append(item)
    except Exception as e:
        st.error(f"读取目录失败: {e}")
    return sorted(folders)

# 获取章节文件夹下的所有.py文件
def get_chapter_files(chapter_folder):
    files = []
    chapter_path = os.path.join(os.getcwd(), chapter_folder)
    
    if os.path.exists(chapter_path):
        try:
            for item in os.listdir(chapter_path):
                if item.endswith('.py'):
                    files.append(item)
        except:
            pass
    return sorted(files)

# 读取Python文件内容
def read_python_file(chapter_folder, file_name):
    file_path = os.path.join(os.getcwd(), chapter_folder, file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "# 读取文件失败"
    return "# 文件不存在"

# 缓存AI生成的知识点，避免重复调用
@st.cache_data(ttl=3600, show_spinner=False)  # 缓存1小时
def generate_knowledge_with_ai_cached(py_content, py_file, chapter_folder):
    """带缓存的AI知识点生成"""
    try:
        return generate_knowledge_with_ai(py_content, py_file, chapter_folder)
    except Exception as e:
        return f"# AI知识点生成失败: {str(e)}"

# 获取知识点：直接调用AI生成
def get_knowledge(chapter_folder, py_file):
    if not py_file:
        return "# 未选择文件"
    
    # 创建唯一的缓存键
    cache_key = f"knowledge_{chapter_folder}_{py_file}"
    
    # 检查是否已生成过知识点（优先使用session_state缓存）
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # 直接调用AI生成知识点
    try:
        # 读取Python文件内容
        py_content = read_python_file(chapter_folder, py_file)
        if not py_content or py_content.startswith("# 文件不存在") or py_content.startswith("# 读取文件失败"):
            error_msg = "# 无法读取Python文件内容"
            st.session_state[cache_key] = error_msg
            return error_msg
        
        # 使用缓存的AI生成（避免重复调用）
        with st.spinner("🤖正在总结知识点..."):
            ai_content = generate_knowledge_with_ai_cached(py_content, py_file, chapter_folder)
            
        # 存储到session_state
        st.session_state[cache_key] = ai_content
        return ai_content
    
    except Exception as e:
        error_msg = f"# 知识点生成失败: {str(e)}\n请确保已安装requests库: pip install requests"
        st.session_state[cache_key] = error_msg
        return error_msg

# 使用硅基流动API生成知识点
def generate_knowledge_with_ai(py_content, py_file, chapter_folder):  
    import requests
    
    # 硅基流动平台的API配置
    api_key = "sk-hmzcxvovibmlguvhozdrrnbzpxmgyoxxgkwvsbydmxrfxdmf"  # API密钥
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

# 运行代码        
def run_code(code, chapter_folder):
    output = io.StringIO()
    original_dir = os.getcwd()
    
    try:
        # 切换到章节目录
        chapter_path = os.path.join(original_dir, chapter_folder)
        if os.path.exists(chapter_path):
            os.chdir(chapter_path)
        
        # 执行代码
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            # 创建一个包含常用库的全局环境
            exec_globals = {
                'pd': pd,
                'np': np,
                '__builtins__': __builtins__
            }
            
            # 执行代码
            exec(code, exec_globals)
        
        output_text = output.getvalue()
        # 如果没有输出，添加提示
        if not output_text.strip():
            output_text = "代码执行成功，但没有任何输出，有以下原因可追溯：\n\n1. 代码只定义了变量/函数但没有调用print，你可以自行定义并利用print打印结果，也可以借助AI代码助手!\n\n2. 代码直接修改了数据但没有显示结果；\n\n3. 代码执行了计算但没有输出。"
        
        return {"success": True, "output": output_text}
    except Exception as e:
        error_msg = output.getvalue()
        if error_msg:
            full_error = f"{error_msg}\n\n错误: {str(e)}"
        else:
            full_error = f"错误: {str(e)}"
        return {"success": False, "output": full_error}
    finally:
        os.chdir(original_dir)

# 缓存AI问答，避免重复请求
@st.cache_data(ttl=600, show_spinner=False)  # 缓存10分钟
def ask_ai_question_cached(py_content_hash, knowledge_hash, question, chapter_folder, py_file):
    try:
        # 从session_state获取原始内容
        py_content_key = f"py_content_{chapter_folder}_{py_file}"
        knowledge_key = f"knowledge_{chapter_folder}_{py_file}"
        
        if py_content_key not in st.session_state or knowledge_key not in st.session_state:
            return "抱歉，无法获取相关上下文信息。"
        
        py_content = st.session_state[py_content_key]
        knowledge = st.session_state[knowledge_key]
        
        return ask_ai_question(py_content, knowledge, question, chapter_folder, py_file)
    except Exception as e:
        return f"AI问答失败: {str(e)}"

# 使用AI回答关于代码的问题
def ask_ai_question(py_content, knowledge, question, chapter_folder, py_file):
    import requests    
    # 硅基流动平台的API配置
    api_key = "sk-hmzcxvovibmlguvhozdrrnbzpxmgyoxxgkwvsbydmxrfxdmf"  # API密钥
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建提示词，包含代码、知识点和用户问题
    system_prompt = """你是一位Python数据挖掘教学助手，专门帮助学生理解代码和解答问题。
    基于提供的代码内容和知识点，回答用户的问题。
    要求：
    1. 回答要具体，结合代码示例
    2. 用简洁易懂的中文解释
    3. 如果涉及代码修改，提供可运行的代码片段
    4. 鼓励学生思考和动手实践
    5. 如果问题不清晰，可以请求澄清
    """
    
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
            {
                "role": "system", 
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": user_prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=45)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"抱歉，AI回答失败 (状态码: {response.status_code})。请稍后再试。"
    except requests.exceptions.Timeout:
        return "⏰ 请求超时，请稍后重试。"
    except requests.exceptions.ConnectionError:
        return "🔌 网络连接失败，请检查网络连接。"
    except Exception as e:
        return f"❌ AI回答失败: {str(e)}"

# 显示AI问答区域 - 独立的区域        
def display_ai_section(chapter, py_file, code_content, knowledge_content):
    # 使用expander展开器，避免占用太多空间
    st.markdown("#### 🤖 AI代码助手")
    with st.expander("点击使用", expanded=False): # expanded=False----控制扩展器默认是否展开
        st.caption("💡 可以针对代码功能、逻辑、修改等进行提问")
        
        # 初始化对话历史
        chat_key = f"chat_history_{chapter}_{py_file}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []
        
        # 显示对话历史
        if st.session_state[chat_key]:
            st.markdown("#### 📝 对话历史")
            
            # 只显示最近5条对话，避免太长
            recent_messages = st.session_state[chat_key][-5:]
            
            for message in recent_messages:
                if message["role"] == "user":
                    st.markdown(f"**👤 你 ({message['time']})：** {message['content']}")
                else:
                    st.markdown(f"**🤖 AI ({message['time']})：** {message['content']}")
                st.markdown("---")
        
        # 自定义提问
        question_input_key = f"question_input_{chapter}_{py_file}"
        if question_input_key not in st.session_state:
            st.session_state[question_input_key] = ""
        
        col_input1, col_input2 = st.columns([5, 1])
        with col_input1:
            question = st.text_area(
                "输入你的问题：",
                value=st.session_state[question_input_key],
                height=80,
                placeholder="例如：如何修改代码来实现XX功能？这个函数有什么作用？",
                key=f"textarea_{chapter}_{py_file}",
                label_visibility="collapsed"
            )
        
        with col_input2:
            ask_button = st.button("发送", key=f"send_{chapter}_{py_file}_4", use_container_width=True)
        
        # 按钮区域
        col_actions = st.columns(3)
        with col_actions[0]:
            if st.session_state[chat_key]:
                if st.button("🗑️ 清空历史对话", key=f"clear_{chapter}_{py_file}_5", use_container_width=True):
                    st.session_state[chat_key] = []
                    st.session_state[question_input_key] = ""
                    st.rerun()
        
        # 处理提问
        if ask_button and question.strip():
            # 清空输入框
            st.session_state[question_input_key] = ""
            
            # 添加用户问题到历史
            current_time = datetime.now().strftime("%H:%M:%S")
            st.session_state[chat_key].append({
                "role": "user",
                "content": question,
                "time": current_time
            })
            
            # 显示正在处理的提示
            with st.spinner("小助手正在思考中..."):
                try:
                    # 存储代码和知识点内容到session_state，供缓存函数使用
                    py_content_key = f"py_content_{chapter}_{py_file}"
                    knowledge_key = f"knowledge_{chapter}_{py_file}"
                    
                    st.session_state[py_content_key] = code_content
                    st.session_state[knowledge_key] = knowledge_content
                    
                    # 创建缓存键（使用内容的哈希值）
                    py_content_hash = hashlib.md5(code_content.encode()).hexdigest()
                    knowledge_hash = hashlib.md5(knowledge_content.encode()).hexdigest()
                    
                    # 使用缓存的AI问答
                    answer = ask_ai_question_cached(
                        py_content_hash,
                        knowledge_hash,
                        question,
                        chapter,
                        py_file
                    )
                    
                    # 添加AI回答到历史
                    current_time = datetime.now().strftime("%H:%M:%S")
                    st.session_state[chat_key].append({
                        "role": "assistant",
                        "content": answer,
                        "time": current_time
                    })
                    
                    # 重新运行以显示新消息
                    st.rerun()
                except Exception as e:
                    st.error(f"提问失败: {str(e)}")

# 显示单个文件的内容：上方显示代码和知识点，下方可编辑运行
def display_file_content(chapter, py_file, tab_idx):
    # 读取代码
    code = read_python_file(chapter, py_file)
    
    # 创建两个主要区域：学习区和编辑运行区
    st.markdown(f"### 📄 {py_file}")
    
    # 代码和知识点（上下布局）
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**📝 代码展示**")
            st.code(code, language='python')
        
        with col2:
            st.markdown("**📚 知识点**")
            # 这里调用get_knowledge函数，它会自动缓存结果
            knowledge = get_knowledge(chapter, py_file)
            st.markdown(knowledge)

    # AI问答区域 - 传入当前的代码和知识点内容
    display_ai_section(chapter, py_file, code, knowledge)
    
    # 编辑运行区：可编辑代码和运行结果
    st.markdown("#### ✏️ 编辑与运行")
    
    # 使用session state保存每个文件的编辑状态
    file_key = f"{chapter}_{py_file}_{tab_idx}"
    if file_key not in st.session_state:
        st.session_state[file_key] = code
    
    # 可编辑的代码区域
    edited_code = st.text_area(
        "修改代码（可在此处编辑后运行）",
        value=st.session_state[file_key],
        height=300,
        key=f"editor_{file_key}",
        label_visibility="collapsed"
    )
    
    # 更新session state
    st.session_state[file_key] = edited_code
    
    # 按钮行
    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("▶️ 运行代码", key=f"run_{file_key}"):
            with st.spinner("正在运行代码..."):
                result = run_code(edited_code, chapter)
                st.session_state[f"result_{file_key}"] = result
    
    with col_btn2:
        if st.button("↩️ 重置代码", key=f"reset_{file_key}"):
            st.session_state[file_key] = code
            st.rerun()
    
    # 显示运行结果
    if f"result_{file_key}" in st.session_state:
        result = st.session_state[f"result_{file_key}"]
        
        if result["success"]:
            st.success("✅ 运行成功")
            # 添加唯一的key
            output_key = f"output_{file_key}"
            st.text_area("运行结果", 
                        value=result["output"], 
                        height=250, 
                        disabled=False,
                        key=output_key)
        else:
            st.error("❌ 运行失败")
            # 添加唯一的key
            error_key = f"error_{file_key}"
            st.text_area("错误信息", 
                        value=result["output"], 
                        height=250, 
                        disabled=False,
                        key=error_key)
    else:
        st.info("点击'运行代码'按钮执行代码，查看运行结果")
    
    # 显示章节下的数据文件
    with st.expander("### 📁 本章节数据文件预览", expanded=False):
        chapter_path = os.path.join(os.getcwd(), chapter)
        data_files = []
        if os.path.exists(chapter_path):
            # 筛选指定类型的文件，排除当前py_file
            for item in os.listdir(chapter_path):
                if item.endswith(('.xlsx', '.csv', '.txt')) and item != py_file:
                    data_files.append(item)
        
        if data_files:
            # 按文件名排序
            for data_file in sorted(data_files):

                # 创建唯一的预览键（避免按钮key重复）
                preview_key = f"preview_{hashlib.md5(f'{chapter}_{py_file}_{data_file}'.encode()).hexdigest()[:8]}"
                # 会话状态：跟踪文件是否被预览
                preview_state_key = f"preview_state_{preview_key}"
                if preview_state_key not in st.session_state:
                    st.session_state[preview_state_key] = False
                
                # 预览按钮
                if st.button(f" {data_file}", key=preview_key):
                    st.session_state[preview_state_key] = not st.session_state[preview_state_key]
                
                # 显示预览内容
                if st.session_state[preview_state_key]:
                    file_path = os.path.join(chapter_path, data_file)
                    try:
                        if data_file.endswith('.xlsx'):
                            df = pd.read_excel(file_path)
                            st.dataframe(df.head(10), use_container_width=True)
                            st.caption(f"数据形状: {df.shape}")
                        elif data_file.endswith('.csv'):
                            # 兼容gbk编码的csv文件
                            try:
                                df = pd.read_csv(file_path, encoding='utf-8')
                            except UnicodeDecodeError:
                                df = pd.read_csv(file_path, encoding='gbk')
                            st.dataframe(df.head(10), use_container_width=True)
                            st.caption(f"数据形状: {df.shape}")
                        elif data_file.endswith('.txt'):
                            # 兼容gbk编码的txt文件
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                            except UnicodeDecodeError:
                                with open(file_path, 'r', encoding='gbk') as f:
                                    content = f.read()
                            # 用st.text_area或st.markdown(pre标签)保留格式，比st.text更友好
                            st.text_area(
                                "文件内容",
                                content[:1000] + ("..." if len(content) > 1000 else ""),
                                height=300,
                                key=f"text_{preview_key}"
                            )
                    except Exception as e:
                        st.error(f"预览失败: {str(e)}")
        else:
            st.caption("暂无其他数据文件")
            
# 侧边栏
with st.sidebar:
    st.header("Python数据挖掘实战")
    
    # 显示所有章节
    st.markdown("### 📚 章节选择")
    
    # 获取所有章节文件夹
    chapter_folders = get_chapter_folders()

    # 初始化session state
    if 'selected_chapter' not in st.session_state:
        st.session_state.selected_chapter = chapter_folders[0] if chapter_folders else None
    
    for i, chapter in enumerate(chapter_folders):
        # 创建唯一的导航键
        nav_key = f"nav_{hashlib.md5(f'nav_{chapter}_{i}'.encode()).hexdigest()[:8]}"
        
        # 如果这是当前选中的章节，用不同的样式显示
        is_selected = (st.session_state.selected_chapter == chapter)
        
        if st.button(f"{'▶️' if is_selected else '·'} {chapter}", 
                    key=nav_key, 
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"):
            # 更新选中的章节
            st.session_state.selected_chapter = chapter
            st.rerun()
    
    st.markdown("---")
    st.markdown("### ⚙️ 使用说明")
    st.info("""
    📚 **AI操作**：
    - 代码展示的右侧是AI总结知识点
    - AI代码助手点击展开即可进行代码问答
    - 这个部分需要耐心等待噢~
    
    💡 **运行提示**：
    - 确保代码中有print语句输出结果
    - 数据文件会自动加载到当前目录
    - 可编辑代码并实时查看运行效果
    """)

# 主界面-显示当前选中的章节
current_chapter = st.session_state.selected_chapter
st.markdown(f"## {current_chapter}")

# 获取该章节的所有Python文件
chapter_files = get_chapter_files(current_chapter)

if not chapter_files:
    st.warning(f"章节 '{current_chapter}' 中没有找到Python文件")
    st.stop()

# 为该章节创建子Tab页 - 每个Python文件一个子Tab
if len(chapter_files) > 1:
    # 如果有多个文件，创建子标签页
    sub_tabs = st.tabs([f"📄 {file}" for file in chapter_files])
    
    for sub_idx, py_file in enumerate(chapter_files):
        with sub_tabs[sub_idx]:
            # 传递tab_idx确保每个显示的内容有唯一标识
            display_file_content(current_chapter, py_file, f"{sub_idx}")
else:
    # 如果只有一个文件，直接显示
    display_file_content(current_chapter, chapter_files[0], "0")
