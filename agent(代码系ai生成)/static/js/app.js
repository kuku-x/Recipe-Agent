let currentTab = 'home';


document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    loadCategories();
});

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const tab = this.getAttribute('data-tab');
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-tab') === tab) {
            item.classList.add('active');
        }
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const targetTab = document.getElementById(tab + 'Tab');
    if (targetTab) {
        targetTab.classList.add('active');
    }
    

}



async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        if (data.success && data.config) {
            const config = data.config;
            
            if (config.kimi) {
                document.getElementById('apiKey').value = config.kimi.api_key || '';
                document.getElementById('apiBaseUrl').value = config.kimi.base_url || 'https://api.moonshot.cn/v1';
                document.getElementById('apiModel').value = config.kimi.model || 'kimi-k2-0711-preview';
            }
            

            
            if (config.output) {
                document.getElementById('outputDirectory').value = config.output.directory || './ai_output';
                document.getElementById('outputFormat').value = config.output.format || 'neo4j';
            }
            
            showNotification('配置加载成功', 'success');
        }
    } catch (error) {
        console.error('加载配置失败:', error);
        showNotification('加载配置失败', 'error');
    }
}

async function saveConfig() {
    try {
        const config = {
            kimi: {
                api_key: document.getElementById('apiKey').value,
                base_url: document.getElementById('apiBaseUrl').value,
                model: document.getElementById('apiModel').value,
                max_retries: 3,
                timeout: 30
            },

            output: {
                format: document.getElementById('outputFormat').value,
                directory: document.getElementById('outputDirectory').value,
                include_nutrition: true,
                include_tags: true,
                available_formats: ['csv', 'neo4j', 'rf2']
            },
            categories: {
                "素菜": "710000000",
                "荤菜": "720000000",
                "水产": "730000000",
                "早餐": "740000000",
                "主食": "750000000",
                "汤类": "760000000",
                "甜品": "770000000",
                "饮料": "780000000",
                "调料": "790000000"
            },
            difficulty_mapping: {
                "1": "610000000",
                "2": "620000000",
                "3": "630000000",
                "4": "640000000",
                "5": "650000000"
            }
        };
        
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('配置保存成功', 'success');
        } else {
            showNotification(data.message || '配置保存失败', 'error');
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        showNotification('保存配置失败', 'error');
    }
}

async function testConnection() {
    try {
        showNotification('正在测试连接...', 'info');
        
        const response = await fetch('/api/test-connection', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('连接测试成功', 'success');
        } else {
            showNotification(data.message || '连接测试失败', 'error');
        }
    } catch (error) {
        console.error('测试连接失败:', error);
        showNotification('测试连接失败', 'error');
    }
}

async function parseRecipe() {
    const content = document.getElementById('recipeContent').value.trim();
    const filePath = document.getElementById('filePath').value.trim();
    
    if (!content) {
        showNotification('请输入菜谱内容', 'warning');
        return;
    }
    
    try {
        showNotification('正在解析菜谱...', 'info');
        
        const response = await fetch('/api/parse-recipe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                markdown_content: content,
                file_path: filePath
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayParseResult(data.recipe);
            showNotification('菜谱解析成功', 'success');
        } else {
            showNotification(data.message || '菜谱解析失败', 'error');
        }
    } catch (error) {
        console.error('解析菜谱失败:', error);
        showNotification('解析菜谱失败', 'error');
    }
}

function displayParseResult(recipe) {
    const resultDiv = document.getElementById('parseResult');
    const contentDiv = document.getElementById('parseResultContent');
    
    let html = `
        <div class="recipe-detail">
            <h4>${recipe.name}</h4>
            <div class="recipe-meta">
                <span class="recipe-badge badge-difficulty">难度: ${'★'.repeat(recipe.difficulty)}</span>
                <span class="recipe-badge badge-category">分类: ${recipe.category}</span>
                ${recipe.cuisine_type ? `<span class="recipe-badge">菜系: ${recipe.cuisine_type}</span>` : ''}
            </div>
            
            ${recipe.prep_time || recipe.cook_time ? `
            <div class="recipe-time">
                ${recipe.prep_time ? `<span>准备时间: ${recipe.prep_time}</span>` : ''}
                ${recipe.cook_time ? `<span>烹饪时间: ${recipe.cook_time}</span>` : ''}
                ${recipe.servings ? `<span>份量: ${recipe.servings}</span>` : ''}
            </div>
            ` : ''}
            
            ${recipe.ingredients && recipe.ingredients.length > 0 ? `
            <div class="recipe-ingredients">
                <h5>食材 (${recipe.ingredients.length})</h5>
                <ul>
                    ${recipe.ingredients.map(ing => `
                        <li>
                            <strong>${ing.name}</strong>
                            ${ing.amount ? `<span> - ${ing.amount} ${ing.unit || ''}</span>` : ''}
                            ${ing.category ? `<span class="recipe-badge badge-category">${ing.category}</span>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
            ` : ''}
            
            ${recipe.steps && recipe.steps.length > 0 ? `
            <div class="recipe-steps">
                <h5>步骤 (${recipe.steps.length})</h5>
                <ol>
                    ${recipe.steps.map(step => `
                        <li>
                            ${step.description}
                            ${step.methods && step.methods.length > 0 ? `
                                <div class="step-methods">
                                    方法: ${step.methods.join(', ')}
                                </div>
                            ` : ''}
                            ${step.tools && step.tools.length > 0 ? `
                                <div class="step-tools">
                                    工具: ${step.tools.join(', ')}
                                </div>
                            ` : ''}
                        </li>
                    `).join('')}
                </ol>
            </div>
            ` : ''}
            
            ${recipe.tags && recipe.tags.length > 0 ? `
            <div class="recipe-tags">
                <h5>标签</h5>
                <div class="tags-container">
                    ${recipe.tags.map(tag => `<span class="recipe-badge">${tag}</span>`).join('')}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    contentDiv.innerHTML = html;
    resultDiv.classList.remove('hidden');
}

function clearParseForm() {
    document.getElementById('recipeContent').value = '';
    document.getElementById('filePath').value = '';
    document.getElementById('parseResult').classList.add('hidden');
}



async function loadRecipes() {
    try {
        const response = await fetch('/api/recipes');
        const data = await response.json();
        
        if (data.success) {
            displayRecipes(data.recipes);
        }
    } catch (error) {
        console.error('加载菜谱失败:', error);
    }
}

function displayRecipes(recipes) {
    const recipesList = document.getElementById('recipesList');
    
    if (recipes.length === 0) {
        recipesList.innerHTML = '<p class="empty-message">暂无菜谱数据，请先解析或批量处理菜谱</p>';
        return;
    }
    
    let html = '';
    recipes.forEach(recipe => {
        html += `
            <div class="recipe-item">
                <div class="recipe-header">
                    <h4>${recipe.name}</h4>
                    <div class="recipe-badges">
                        <span class="recipe-badge badge-difficulty">${'★'.repeat(recipe.difficulty || 3)}</span>
                        <span class="recipe-badge badge-category">${recipe.category || '未分类'}</span>
                    </div>
                </div>
                <div class="recipe-file">${recipe.file}</div>
            </div>
        `;
    });
    
    recipesList.innerHTML = html;
}

function searchRecipes() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const difficultyFilter = document.getElementById('difficultyFilter').value;
    
    fetch('/api/recipes')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.recipes) {
                let filtered = data.recipes.filter(recipe => {
                    let matchSearch = !searchTerm || 
                        recipe.name.toLowerCase().includes(searchTerm) ||
                        recipe.file.toLowerCase().includes(searchTerm) ||
                        (recipe.ingredients && recipe.ingredients.some(ing => ing.name.toLowerCase().includes(searchTerm))) ||
                        (recipe.steps && recipe.steps.some(step => step.description.toLowerCase().includes(searchTerm)));
                    
                    let matchCategory = !categoryFilter || recipe.category.includes(categoryFilter);
                    let matchDifficulty = !difficultyFilter || recipe.difficulty == difficultyFilter;
                    
                    return matchSearch && matchCategory && matchDifficulty;
                });
                
                displayRecipes(filtered);
            }
        })
        .catch(error => {
            console.error('搜索菜谱失败:', error);
        });
}

function filterRecipes() {
    searchRecipes();
}

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();
        
        if (data.success && data.categories) {
            const select = document.getElementById('categoryFilter');
            select.innerHTML = '<option value="">所有分类</option>';
            
            data.categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = cat.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载分类失败:', error);
    }
}

async function exportData(format) {
    try {
        showNotification(`正在导出${format.toUpperCase()}格式...`, 'info');
        
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format: format
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || '导出成功', 'success');
        } else {
            showNotification(data.message || '导出失败', 'error');
        }
    } catch (error) {
        console.error('导出数据失败:', error);
        showNotification('导出数据失败', 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = 'notification ' + type;
    notification.classList.remove('hidden');
    
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

// AI Chat Functions
function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Process the message and get AI response
    processUserMessage(message);
}

function sendQuickMessage(action) {
    addMessage(action, 'user');
    processUserMessage(action);
}

function addMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + (sender === 'user' ? 'user-message' : 'ai-message');
    
    const avatar = sender === 'user' ? '👤' : '🤖';
    const content = text.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p>${content}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addAIMessage(htmlContent) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            ${htmlContent}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function processUserMessage(message) {
    // 显示加载状态
    showLoadingMessage();
    
    try {
        // 调用后端AI接口
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const data = await response.json();
        
        // 移除加载状态
        removeLoadingMessage();
        
        if (data.success) {
            // 将AI回复的换行符转换为HTML
            const formattedResponse = data.response.replace(/\n/g, '<br>');
            addAIMessage(`<p>${formattedResponse}</p>`);
        } else {
            addAIMessage(`
                <p>抱歉，AI服务暂时不可用。</p>
                <p>错误信息：${data.message || '未知错误'}</p>
                <p>请检查API配置是否正确，或稍后重试。</p>
            `);
        }
    } catch (error) {
        // 移除加载状态
        removeLoadingMessage();
        
        console.error('AI问答失败:', error);
        addAIMessage(`
            <p>抱歉，连接AI服务失败。</p>
            <p>请确保：</p>
            <ul>
                <li>后端服务已启动</li>
                <li>API密钥已正确配置</li>
                <li>网络连接正常</li>
            </ul>
        `);
    }
}

function showLoadingMessage() {
    const chatMessages = document.getElementById('chatMessages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai-message loading-message';
    loadingDiv.id = 'loadingMessage';
    loadingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <p><span class="loading-dots">正在思考</span></p>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeLoadingMessage() {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// Handle Enter key in chat input
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});