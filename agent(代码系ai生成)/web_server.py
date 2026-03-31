#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web服务器 - AI菜谱知识图谱生成器
"""

import os
import json
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from recipe_ai_agent import KimiRecipeAgent, RecipeKnowledgeGraphBuilder
from datetime import datetime

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# 全局变量
ai_agent = None
builder = None
processing_status = {
    'recipes': []
}

def load_config():
    """加载配置文件"""
    config_file = "config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def initialize_agent():
    """初始化AI Agent"""
    global ai_agent, builder
    
    try:
        config = load_config()
        api_key = config.get("kimi", {}).get("api_key", "")
        
        if not api_key or api_key == "sk-xxx":
            return False, "未配置有效的API密钥"
        
        base_url = config.get("kimi", {}).get("base_url", "https://api.moonshot.cn/v1")
        
        ai_agent = KimiRecipeAgent(api_key, base_url)
        
        output_dir = config.get("output", {}).get("directory", "./ai_output")
        batch_size = config.get("processing", {}).get("batch_size", 20)
        
        builder = RecipeKnowledgeGraphBuilder(ai_agent, output_dir, batch_size)
        
        return True, "初始化成功"
        
    except Exception as e:
        return False, f"初始化失败: {str(e)}"

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    global ai_agent, builder, processing_status
    
    is_initialized = ai_agent is not None and builder is not None
    
    return jsonify({
        'success': True,
        'initialized': is_initialized,
        'processing': processing_status
    })

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置"""
    if request.method == 'GET':
        config = load_config()
        # 隐藏API密钥
        if 'kimi' in config and 'api_key' in config['kimi']:
            config['kimi']['api_key'] = '***' if config['kimi']['api_key'] else ''
        return jsonify({'success': True, 'config': config})
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            # 重新初始化agent
            success, message = initialize_agent()
            
            return jsonify({'success': success, 'message': message})
        except Exception as e:
            return jsonify({'success': False, 'message': f"配置保存失败: {str(e)}"})



@app.route('/api/chat', methods=['POST'])
def chat():
    """AI问答接口"""
    global ai_agent
    
    if not ai_agent:
        return jsonify({'success': False, 'message': 'AI Agent未初始化，请先配置API密钥'})
    
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'success': False, 'message': '消息不能为空'})
        
        # 构建系统提示词
        system_prompt = """你是一个专业的菜谱助手，擅长回答各种与菜谱、烹饪相关的问题。

你可以帮助用户：
1. 回答菜系相关问题（如川菜、粤菜等特色菜）
2. 提供菜品制作方法
3. 推荐适合特定季节、节日的菜品
4. 解释烹饪技巧和食材搭配
5. 提供营养搭配建议

请用友好、专业的方式回答，回答要详细且实用。如果用户问的是具体菜谱，请提供详细的食材和步骤。"""

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 调用Kimi API
        response = ai_agent.call_kimi_api(messages)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f"AI回答失败: {str(e)}"})

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """测试API连接"""
    global ai_agent
    
    try:
        config = load_config()
        api_key = config.get("kimi", {}).get("api_key", "")
        
        if not api_key or api_key == "sk-xxx":
            return jsonify({'success': False, 'message': 'API密钥未配置'})
        
        # 测试调用
        test_agent = KimiRecipeAgent(api_key)
        test_content = "# 测试菜谱\n\n## 必备原料和工具\n- 鸡蛋\n- 盐"
        test_agent.extract_recipe_info(test_content, "test.md")
        
        return jsonify({'success': True, 'message': '连接测试成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f"连接测试失败: {str(e)}"})

def main():
    """主函数"""
    print("🍳 AI菜谱知识图谱生成器 - Web服务器")
    print("=" * 50)
    
    # 初始化AI Agent
    success, message = initialize_agent()
    if success:
        print(f"✅ {message}")
    else:
        print(f"⚠️  {message}")
        print("请在网页界面中配置API密钥")
    
    # 启动Flask服务器
    port = int(os.getenv('PORT', 5000))
    print(f"\n🌐 服务器启动: http://localhost:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    main()