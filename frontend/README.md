# 切片预览功能说明

## 功能概述
切片预览功能允许用户查看向量库中的切片数据，并通过点击切片来查看与该切片关联的实体。

## 主要功能

1. **切片数据展示**：显示向量库中的最近20条切片数据，包括切片ID、名称和向量信息。

2. **切片点击事件**：点击任意切片卡片，会自动调用后端API获取与该切片关联的实体。

3. **实体高亮显示**：获取到关联实体后，会在切片文本中高亮显示这些实体。

## 技术实现

### 前端实现

#### 1. 切片数据加载
```javascript
// 从向量库获取最近的20条数据
async function loadLatestVectors() {
    try {
        // 显示加载状态
        chunksList.innerHTML = `
            <div class="loading-state">
                <i class="fa fa-spinner fa-spin"></i>
                <p>正在加载向量数据...</p>
            </div>
        `;
        
        // 调用后端API获取最近的20条向量数据
        const response = await fetch('http://localhost:8000/vector-db/latest?limit=20');
        const result = await response.json();
        
        if (result.code === 200) {
            // 渲染向量数据
            renderVectorsData(result.data);
        } else {
            // 处理错误
        }
    } catch (error) {
        // 处理异常
    }
}
```

#### 2. 切片数据渲染
```javascript
// 渲染向量数据
function renderVectorsData(vectors) {
    if (!vectors || vectors.length === 0) {
        // 显示空状态
        return;
    }
    
    chunksList.innerHTML = '';
    
    vectors.forEach((vector, index) => {
        const vectorCard = document.createElement('div');
        vectorCard.className = 'result-item';
        vectorCard.innerHTML = `
            <div class="result-header">
                <h3>向量 ${index + 1}</h3>
            </div>
            <div class="result-content">
                <div class="vector-info">
                    <div class="vector-id">
                        <strong>ID:</strong> ${vector.pk}
                    </div>
                    <div class="vector-name">
                        <strong>名称:</strong> <span class="vector-text">${vector.text}</span>
                    </div>
                    <div class="vector-embedding">
                        <strong>向量:</strong> [${vector.vector.slice(0, 5).join(', ')}...]
                    </div>
                </div>
            </div>
            <div class="result-meta">
                <span>维度: ${vector.vector.length}</span>
            </div>
        `;
        
        // 添加点击事件
        vectorCard.addEventListener('click', () => {
            getEntitiesByChunkId(vector.pk, vectorCard);
        });
        
        chunksList.appendChild(vectorCard);
    });
}
```

#### 3. 获取关联实体
```javascript
// 根据chunk_id获取关联实体
async function getEntitiesByChunkId(chunkId, vectorCard) {
    try {
        // 显示加载状态
        const vectorTextElement = vectorCard.querySelector('.vector-text');
        const originalText = vectorTextElement.textContent;
        vectorTextElement.innerHTML = `
            <i class="fa fa-spinner fa-spin"></i> 正在获取关联实体...
        `;
        
        // 调用后端API获取关联实体
        const response = await fetch(`http://localhost:8000/graph-db/nodesById?chunk_id=${encodeURIComponent(chunkId)}`);
        const result = await response.json();
        
        if (result.code === 200 && result.data && result.data.length > 0) {
            // 高亮显示实体
            highlightEntities(originalText, result.data, vectorTextElement);
            showNotification(`找到 ${result.data.length} 个关联实体`, 'success');
        } else {
            // 没有找到实体，恢复原始文本
            vectorTextElement.textContent = originalText;
            showNotification('未找到关联实体', 'info');
        }
    } catch (error) {
        console.error('获取关联实体失败:', error);
        showNotification('获取关联实体失败，请检查API连接', 'error');
    }
}
```

#### 4. 实体高亮显示
```javascript
// 在文本中高亮显示实体
function highlightEntities(text, entities, element) {
    if (!entities || entities.length === 0) {
        element.textContent = text;
        return;
    }
    
    // 创建正则表达式，匹配所有实体
    const entityRegex = new RegExp(`(${entities.map(entity => escapeRegExp(entity)).join('|')})`, 'gi');
    
    // 使用正则表达式替换文本，添加高亮标记
    const highlightedText = text.replace(entityRegex, '<span class="entity-highlight">$1</span>');
    
    element.innerHTML = highlightedText;
}
```

### 后端API

#### 获取关联实体API
```python
@app.get("/graph-db/nodesById")
async def get_graph_nodes_by_id(chunk_id: str = Query(...)):
    try:
        nodes = await asyncio.to_thread(graph_db_manager.get_graph_data_by_id, chunk_id)
        return {
            "code": 200,
            "msg": "根据chunk_id获取实体成功",
            "data": nodes
        }
    except Exception as e:
        return {"code": 500, "msg": f"获取节点数据失败：{str(e)}", "data": None}
```

## 使用说明

1. 打开应用程序，进入"切片预览"标签页。
2. 系统会自动加载向量库中的最近20条切片数据。
3. 点击任意切片卡片，系统会调用后端API获取与该切片关联的实体。
4. 获取到实体后，系统会在切片文本中高亮显示这些实体。

## 样式说明

高亮实体使用以下CSS样式：

```css
.entity-highlight {
    background-color: #ffeb3b;
    color: #000;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: bold;
    cursor: help;
    transition: background-color 0.3s ease;
}

.entity-highlight:hover {
    background-color: #fdd835;
    text-decoration: underline;
}
```