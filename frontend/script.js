// 全局变量
let selectedFiles = [];
let chunks = [];
let isKnowledgeBasePublished = false;
let knowledgeBases = [];
let currentKnowledgeBase = null;

// 新增DOM元素
const refreshKnowledgeBtn = document.getElementById('refresh-knowledge-btn');
const knowledgeList = document.getElementById('knowledge-list');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const unpublishBtn = document.getElementById('unpublish-btn');
const refreshGraphBtn = document.getElementById('refresh-graph-btn');
const exportGraphBtn = document.getElementById('export-graph-btn');
const graphCanvas = document.getElementById('graph-canvas');
const nodeCountElement = document.getElementById('node-count');
const relationshipCountElement = document.getElementById('relationship-count');

// 图数据相关变量
let graphData = { nodes: [], relationships: [] };

// DOM元素
const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.section');
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const selectFileBtn = document.getElementById('select-file-btn');
const uploadBtn = document.getElementById('upload-btn');
const cancelUploadBtn = document.getElementById('cancel-upload-btn');
const fileList = document.getElementById('file-list');
const queryInput = document.getElementById('query-input');
const queryBtn = document.getElementById('query-btn');
const retrievalResults = document.getElementById('retrieval-results');
const knowledgeSelect = document.getElementById('knowledge-select');
const publishBtn = document.getElementById('publish-btn');
const apiStatusElement = document.querySelector('.api-value.status-pending');
const modal = document.getElementById('modal');
const modalClose = document.querySelector('.modal-close');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalCancel = document.getElementById('modal-cancel');
const modalConfirm = document.getElementById('modal-confirm');
const notification = document.getElementById('notification');
const createKnowledgeBtn = document.getElementById('create-knowledge-btn');
const deleteKnowledgeBtn = document.getElementById('delete-knowledge-btn');
const changePasswordBtn = document.getElementById('change-password-btn');
const updateProfileBtn = document.getElementById('update-profile-btn');
const addPermissionBtn = document.getElementById('add-permission-btn');
const permissionKnowledgeSelect = document.getElementById('permission-knowledge-select');
const permissionList = document.getElementById('permission-list');
const knowledgeTabs = document.querySelector('.knowledge-tabs');
const settingsTabs = document.querySelector('.settings-tabs');
const chunksList = document.getElementById('chunks-list');

// 初始化函数已移至文件末尾，包含加载知识库列表的功能

// 绑定事件监听
function bindEventListeners() {
    // 导航菜单切换
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('href').substring(1);
            switchSection(targetId);
        });
    });

    // 文件上传相关事件
    uploadArea.addEventListener('click', () => fileInput.click());
    selectFileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    uploadBtn.addEventListener('click', uploadFiles);
    cancelUploadBtn.addEventListener('click', cancelUpload);
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
    });

    // 查询相关事件
    queryBtn.addEventListener('click', performQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performQuery();
        }
    });

    // 发布相关事件
    publishBtn.addEventListener('click', publishKnowledgeBase);
    unpublishBtn.addEventListener('click', unpublishKnowledgeBase);

    // 选项卡切换事件
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // 知识库管理事件
    if (createKnowledgeBtn) {
        createKnowledgeBtn.addEventListener('click', createKnowledgeBase);
    }
    if (deleteKnowledgeBtn) {
        deleteKnowledgeBtn.addEventListener('click', deleteKnowledgeBase);
    }
    if (refreshKnowledgeBtn) {
        refreshKnowledgeBtn.addEventListener('click', loadKnowledgeBases);
    }

    // 设置模块事件
    changePasswordBtn.addEventListener('click', showChangePasswordModal);
    updateProfileBtn.addEventListener('click', showUpdateProfileModal);
    addPermissionBtn.addEventListener('click', showAddPermissionModal);
    
    // 图预览相关事件
    if (refreshGraphBtn) {
        refreshGraphBtn.addEventListener('click', loadGraphData);
    }
    if (exportGraphBtn) {
        exportGraphBtn.addEventListener('click', exportGraphData);
    }

    // 模态框事件
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    modalClose.addEventListener('click', closeModal);
    modalCancel.addEventListener('click', closeModal);
}

// 切换区域
function switchSection(targetId) {
    // 更新导航菜单
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === `#${targetId}`) {
            item.classList.add('active');
        }
    });

    // 更新内容区域
    sections.forEach(section => {
        section.classList.remove('active');
        if (section.id === targetId) {
            section.classList.add('active');
        }
    });

    // 特殊处理：当切换到知识库管理时，始终显示知识库列表选项卡并隐藏其他标签页按钮
    if (targetId === 'knowledge') {
        // 确保只更新知识库管理的选项卡
        const knowledgeTabBtns = document.querySelectorAll('.knowledge-tabs .tab-btn');
        const knowledgeTabContents = document.querySelectorAll('#knowledge .tab-content');
        
        // 移除所有激活状态
        knowledgeTabBtns.forEach(btn => btn.classList.remove('active'));
        knowledgeTabContents.forEach(content => content.classList.remove('active'));
        
        // 隐藏所有选项卡按钮和内容
        knowledgeTabBtns.forEach(btn => {
            btn.classList.add('hidden-tab');
            btn.style.display = 'none';
        });
        
        knowledgeTabContents.forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });
        
        // 只显示知识库列表选项卡按钮和内容
        const listTabBtn = document.querySelector('.knowledge-tabs .tab-btn[data-tab="list"]');
        const listTabContent = document.getElementById('tab-list');
        
        if (listTabBtn) {
            listTabBtn.classList.remove('hidden-tab');
            listTabBtn.classList.add('active');
            listTabBtn.style.display = 'block';
        }
        
        if (listTabContent) {
            listTabContent.classList.add('active');
            listTabContent.style.display = 'block';
        }
    }
}

// 处理文件选择
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
    // 清空input值，允许重复选择相同文件
    e.target.value = '';
}

// 添加文件到列表
function addFiles(files) {
    files.forEach(file => {
        // 检查文件类型
        const allowedTypes = ['.txt', '.pdf', '.docx'];
        const fileExt = `.${file.name.split('.').pop().toLowerCase()}`;
        
        if (!allowedTypes.includes(fileExt)) {
            showNotification('不支持的文件类型，请上传TXT、PDF或DOCX文件', 'error');
            return;
        }
        
        // 检查文件大小（最大10MB）
        if (file.size > 10 * 1024 * 1024) {
            showNotification('文件过大，请上传小于10MB的文件', 'error');
            return;
        }
        
        // 添加到文件列表
        selectedFiles.push(file);
        renderFileList();
    });
}

// 渲染文件列表
function renderFileList() {
    fileList.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        // 获取文件图标
        const fileExt = `.${file.name.split('.').pop().toLowerCase()}`;
        let fileIcon = 'fa-file-text-o';
        if (fileExt === '.pdf') fileIcon = 'fa-file-pdf-o';
        if (fileExt === '.docx') fileIcon = 'fa-file-word-o';
        
        fileItem.innerHTML = `
            <div class="file-item-info">
                <i class="fa ${fileIcon}"></i>
                <div>
                    <div class="file-item-name">${file.name}</div>
                    <div class="file-item-size">${formatFileSize(file.size)}</div>
                </div>
            </div>
            <i class="fa fa-times file-item-remove" data-index="${index}"></i>
        `;
        
        // 添加删除事件
        const removeBtn = fileItem.querySelector('.file-item-remove');
        removeBtn.addEventListener('click', () => removeFile(index));
        
        fileList.appendChild(fileItem);
    });
}

// 删除文件
function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFileList();
}

// 上传文件
async function uploadFiles() {
    if (selectedFiles.length === 0) {
        showNotification('请先选择文件', 'warning');
        return;
    }
    
    if (!currentKnowledgeBase) {
        showNotification('请先选择或创建一个知识库', 'warning');
        return;
    }
    
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 上传中...';
    
    try {
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.code === 200) {
                showNotification(`文件 ${file.name} 上传成功`, 'success');
                
                // 更新当前知识库的文件计数
                const currentKB = knowledgeBases.find(kb => kb.id === currentKnowledgeBase);
                if (currentKB) {
                    currentKB.fileCount += 1;
                    renderKnowledgeBases();
                }
                
                // 获取实际的切片数据（需要后端API支持）
                // 目前先使用示例数据
                addSampleChunks(file.name);
            } else {
                const errorMsg = result.msg || '未知错误';
                showNotification(`文件 ${file.name} 上传失败：${errorMsg}`, 'error');
            }
        }
        
        // 清空选择的文件
        selectedFiles = [];
        renderFileList();
    } catch (error) {
        console.error('上传失败:', error);
        showNotification('上传失败，请检查API连接或后端服务状态', 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fa fa-upload"></i> 开始上传';
    }
}

// 取消上传
function cancelUpload() {
    selectedFiles = [];
    renderFileList();
    showNotification('上传已取消', 'warning');
}

// 执行查询
async function performQuery() {
    const query = queryInput.value.trim();
    
    if (!query) {
        showNotification('请输入查询语句', 'warning');
        return;
    }
    
    queryBtn.disabled = true;
    queryBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 查询中...';
    
    // 清空之前的结果
    retrievalResults.innerHTML = '';
    
    try {
        const response = await fetch(`http://localhost:8000/retrieval?query=${encodeURIComponent(query)}`, {
            method: 'GET'
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            displayQueryResults(result.data, result.vector_chunks, result.extended_chunks);
        } else {
            const errorMsg = result.msg || '未知错误';
            showNotification(`查询失败：${errorMsg}`, 'error');
            displayEmptyResults();
        }
    } catch (error) {
        console.error('查询失败:', error);
        showNotification('查询失败，请检查API连接', 'error');
        displayEmptyResults();
    } finally {
        queryBtn.disabled = false;
        queryBtn.innerHTML = '<i class="fa fa-search"></i> 开始测试';
    }
}

// 显示查询结果
function displayQueryResults(data, vectorChunks, extendedChunks) {
    if (!data) {
        displayEmptyResults();
        return;
    }
    
    // 创建答案卡片
    const answerCard = document.createElement('div');
    answerCard.className = 'result-item';
    answerCard.innerHTML = `
        <div class="result-header">
            <h3>答案</h3>
            <span class="result-score">95%</span>
        </div>
        <div class="result-content">${data}</div>
    `;
    retrievalResults.appendChild(answerCard);
    
    // 创建向量召回展示卡片
    if (vectorChunks) {
        const vectorCard = document.createElement('div');
        vectorCard.className = 'result-item';
        
        let vectorContent = '';
        if (Array.isArray(vectorChunks)) {
            vectorContent = '<ol class="retrieval-list">';
            vectorChunks.forEach((chunk, index) => {
                vectorContent += `<li class="retrieval-item">${chunk}</li>`;
            });
            vectorContent += '</ol>';
        } else {
            vectorContent = `<pre>${JSON.stringify(vectorChunks, null, 2)}</pre>`;
        }
        
        vectorCard.innerHTML = `
            <div class="result-header">
                <h3>向量召回</h3>
                <span class="result-score">${Array.isArray(vectorChunks) ? vectorChunks.length : '未知'}个结果</span>
            </div>
            <div class="result-content">
                ${vectorContent}
            </div>
        `;
        retrievalResults.appendChild(vectorCard);
    }
    
    // 创建图扩展召回展示卡片
    if (extendedChunks) {
        const extendedCard = document.createElement('div');
        extendedCard.className = 'result-item';
        
        let extendedContent = '';
        if (Array.isArray(extendedChunks)) {
            extendedContent = '<ol class="retrieval-list">';
            extendedChunks.forEach((chunk, index) => {
                extendedContent += `<li class="retrieval-item">${chunk}</li>`;
            });
            extendedContent += '</ol>';
        } else {
            extendedContent = `<pre>${JSON.stringify(extendedChunks, null, 2)}</pre>`;
        }
        
        extendedCard.innerHTML = `
            <div class="result-header">
                <h3>图扩展召回</h3>
                <span class="result-score">${Array.isArray(extendedChunks) ? extendedChunks.length : '未知'}个结果</span>
            </div>
            <div class="result-content">
                ${extendedContent}
            </div>
        `;
        retrievalResults.appendChild(extendedCard);
    }
}

// 显示空结果
function displayEmptyResults() {
    retrievalResults.innerHTML = `
        <div class="empty-state">
            <i class="fa fa-search"></i>
            <p>未找到相关结果</p>
        </div>
    `;
}

// 发布知识库
function publishKnowledgeBase() {
    // 模拟发布过程
    publishBtn.disabled = true;
    publishBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 发布中...';
    
    setTimeout(() => {
        // 更新API状态
        isKnowledgeBasePublished = true;
        updateApiStatus();
        
        showNotification('知识库发布成功', 'success');
        
        publishBtn.disabled = false;
        publishBtn.innerHTML = '<i class="fa fa-paper-plane"></i> 发布知识库';
        
        // 跳转到API接口页面
        switchSection('api');
    }, 1500);
}

// 预览API
function previewApi() {
    showModal('API预览', `
        <div class="api-preview">
            <h4>API地址</h4>
            <p>http://localhost:8000</p>
            
            <h4>可用接口</h4>
            <ul>
                <li><strong>POST /upload</strong> - 文件上传</li>
                <li><strong>POST /add-text</strong> - 文本导入</li>
                <li><strong>GET /retrieval</strong> - 知识库检索</li>
            </ul>
            
            <h4>调用示例</h4>
            <pre><code>curl -X GET "http://localhost:8000/retrieval?query=你的问题"</code></pre>
        </div>
    `);
}

// 创建知识库
async function createKnowledgeBase() {
    showModal('创建知识库', `
        <div class="create-knowledge-form">
            <div class="form-group">
                <label>知识库名称</label>
                <input type="text" id="new-knowledge-name" placeholder="输入知识库名称" class="search-input">
            </div>
            <div class="form-group">
                <label>描述</label>
                <textarea id="new-knowledge-desc" placeholder="输入知识库描述" rows="3" class="search-input"></textarea>
            </div>
            <div class="form-group">
                <label>实体类型</label>
                <input type="text" id="new-knowledge-entities" placeholder="人物,组织,地点,事件" class="search-input">
            </div>
        </div>
    `);
    
    // 重新绑定确认按钮事件
    modalConfirm.onclick = async () => {
        const name = document.getElementById('new-knowledge-name').value.trim();
        const description = document.getElementById('new-knowledge-desc').value.trim();
        
        if (!name) {
            showNotification('请输入知识库名称', 'warning');
            return;
        }
        
        try {
            // 发送请求到后端API
            const response = await fetch('http://localhost:8000/knowledge-base', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, description })
            });
            
            const result = await response.json();
            
            if (result.code === 200) {
                // 从API返回的数据中创建知识库对象
                const newKB = {
                    id: result.data.id,
                    name: result.data.name,
                    description: result.data.description,
                    status: result.data.is_active ? 'active' : 'inactive',
                    fileCount: 0,
                    chunkCount: 0,
                    entityCount: 0,
                    createTime: result.data.created_at,
                    updateTime: result.data.updated_at
                };
                
                // 添加到知识库列表
                knowledgeBases.push(newKB);
                
                // 如果是第一个知识库，设为当前知识库
                if (knowledgeBases.length === 1) {
                    currentKnowledgeBase = newKB.id;
                }
                
                // 更新列表显示
                renderKnowledgeBases();
                
                showNotification(`知识库 "${name}" 创建成功`, 'success');
                closeModal();
            } else {
                const errorMsg = result.msg || '未知错误';
                showNotification(`知识库创建失败：${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('创建知识库失败:', error);
            showNotification('创建知识库失败，请检查API连接', 'error');
        }
    };
}

// 删除知识库
function deleteKnowledgeBase() {
    if (!currentKnowledgeBase) {
        showNotification('请先选择一个知识库', 'warning');
        return;
    }
    
    const currentKB = knowledgeBases.find(kb => kb.id === currentKnowledgeBase);
    if (!currentKB) {
        showNotification('当前知识库不存在', 'warning');
        return;
    }
    
    showModal('删除知识库', `
        <div class="delete-knowledge-confirm">
            <p class="warning-text">您确定要删除知识库 "${currentKB.name}" 吗？此操作不可恢复。</p>
            <div class="delete-options">
                <label>
                    <input type="checkbox" id="delete-with-data"> 同时删除所有数据
                </label>
            </div>
        </div>
    `);
    
    // 重新绑定确认按钮事件
    modalConfirm.onclick = () => {
        // 模拟删除过程
        knowledgeBases = knowledgeBases.filter(kb => kb.id !== currentKnowledgeBase);
        if (knowledgeBases.length > 0) {
            currentKnowledgeBase = knowledgeBases[0].id;
        } else {
            currentKnowledgeBase = null;
        }
        
        renderKnowledgeBases();
        
        // 清空当前的数据
        selectedFiles = [];
        renderFileList();
        chunks = [];
        updateChunkCount();
        updateFileCount();
        
        showNotification(`知识库 "${currentKB.name}" 删除成功`, 'success');
        closeModal();
    };
}



// 更新API状态
function updateApiStatus() {
    if (isKnowledgeBasePublished) {
        apiStatusElement.textContent = '已发布';
        apiStatusElement.className = 'api-value status-published';
    } else {
        apiStatusElement.textContent = '未发布';
        apiStatusElement.className = 'api-value status-pending';
    }
}

// 切换选项卡
function switchTab(tabId) {
    // 获取当前激活的区域
    const activeSection = document.querySelector('.section.active');
    if (!activeSection) return;
    
    // 如果是知识库管理区域，实现标签的互斥显示
    if (activeSection.id === 'knowledge') {
        const knowledgeTabBtns = document.querySelectorAll('.knowledge-tabs .tab-btn');
        
        // 如果切换到列表标签，隐藏其他所有功能标签
        if (tabId === 'list') {
            knowledgeTabBtns.forEach(btn => {
                const btnTabId = btn.getAttribute('data-tab');
                if (btnTabId === 'list') {
                    btn.classList.remove('hidden-tab');
                    btn.style.display = 'block';
                } else {
                    btn.classList.add('hidden-tab');
                    btn.style.display = 'none';
                }
            });
        } else {
            // 如果切换到其他功能标签，隐藏列表标签
            knowledgeTabBtns.forEach(btn => {
                const btnTabId = btn.getAttribute('data-tab');
                if (btnTabId === 'list') {
                    btn.classList.add('hidden-tab');
                    btn.style.display = 'none';
                } else {
                    btn.classList.remove('hidden-tab');
                    btn.style.display = 'block';
                }
            });
        }
    }
    
    // 获取当前区域内的选项卡按钮和内容
    const sectionTabBtns = activeSection.querySelectorAll('.tab-btn');
    const sectionTabContents = activeSection.querySelectorAll('.tab-content');
    
    // 更新选项卡按钮状态
    sectionTabBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        }
    });

    // 更新选项卡内容状态
    sectionTabContents.forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
        if (content.id === `tab-${tabId}`) {
            content.classList.add('active');
            content.style.display = 'block';
        }
    });
    
    // 如果切换到API接口选项卡，更新API状态
    if (tabId === 'api') {
        updateApiStatus();
    }
    
    // 如果切换到图预览选项卡，加载并显示图数据
    if (tabId === 'graph') {
        loadGraphData();
    }
    
    // 如果切换到权限管理标签页，确保知识库下拉框已更新
    if (tabId === 'permission') {
        updateKnowledgeDropdown(permissionKnowledgeSelect, '选择知识库').then(() => {
            console.log('权限管理页面知识库下拉框已更新');
        }).catch(error => {
            console.error('更新权限管理页面知识库下拉框失败:', error);
        });
    }
    
    // 如果切换到切片预览标签页，加载向量库中的最新数据
    if (tabId === 'chunks') {
        loadLatestVectors();
    }
}

// 知识库下线
function unpublishKnowledgeBase() {
    if (!isKnowledgeBasePublished) {
        showNotification('知识库尚未发布', 'warning');
        return;
    }

    unpublishBtn.disabled = true;
    unpublishBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 处理中...';

    setTimeout(() => {
        isKnowledgeBasePublished = false;
        updateApiStatus();
        showNotification('知识库已下线', 'success');
        unpublishBtn.disabled = false;
        unpublishBtn.innerHTML = '<i class="fa fa-pause"></i> 下线';
    }, 1500);
}

// 显示修改密码模态框
function showChangePasswordModal() {
    showModal('修改密码', `
        <div class="change-password-form">
            <div class="form-group">
                <label>当前密码</label>
                <input type="password" id="current-password" placeholder="输入当前密码" class="search-input">
            </div>
            <div class="form-group">
                <label>新密码</label>
                <input type="password" id="new-password" placeholder="输入新密码" class="search-input">
            </div>
            <div class="form-group">
                <label>确认新密码</label>
                <input type="password" id="confirm-password" placeholder="再次输入新密码" class="search-input">
            </div>
        </div>
    `);

    modalConfirm.onclick = () => {
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (!currentPassword || !newPassword || !confirmPassword) {
            showNotification('请填写所有密码字段', 'warning');
            return;
        }

        if (newPassword !== confirmPassword) {
            showNotification('两次输入的新密码不一致', 'error');
            return;
        }

        // 模拟修改密码
        setTimeout(() => {
            showNotification('密码修改成功', 'success');
            closeModal();
        }, 1000);
    };
}

// 显示更新个人信息模态框
function showUpdateProfileModal() {
    showModal('更新个人信息', `
        <div class="update-profile-form">
            <div class="form-group">
                <label>邮箱</label>
                <input type="email" id="update-email" value="admin@example.com" class="search-input">
            </div>
            <div class="form-group">
                <label>手机号码</label>
                <input type="tel" id="update-phone" value="13800138000" class="search-input">
            </div>
            <div class="form-group">
                <label>备注</label>
                <textarea id="update-remark" placeholder="输入备注信息" rows="3" class="search-input"></textarea>
            </div>
        </div>
    `);

    modalConfirm.onclick = () => {
        const email = document.getElementById('update-email').value;
        const phone = document.getElementById('update-phone').value;

        if (!email) {
            showNotification('请输入邮箱', 'warning');
            return;
        }

        // 模拟更新个人信息
        setTimeout(() => {
            showNotification('个人信息更新成功', 'success');
            closeModal();
        }, 1000);
    };
}

// 显示添加权限模态框
function showAddPermissionModal() {
    const selectedKnowledge = permissionKnowledgeSelect.value;
    if (!selectedKnowledge) {
        showNotification('请先选择知识库', 'warning');
        return;
    }

    showModal('添加权限', `
        <div class="add-permission-form">
            <div class="form-group">
                <label>用户名/邮箱</label>
                <input type="text" id="permission-username" placeholder="输入用户名或邮箱" class="search-input">
            </div>
            <div class="form-group">
                <label>角色</label>
                <select id="permission-role" class="search-input">
                    <option value="reader">读者</option>
                    <option value="editor">编辑者</option>
                    <option value="admin">管理员</option>
                </select>
            </div>
            <div class="form-group">
                <label>有效期</label>
                <input type="date" id="permission-expire" class="search-input">
            </div>
        </div>
    `);

    modalConfirm.onclick = () => {
        const username = document.getElementById('permission-username').value;
        const role = document.getElementById('permission-role').value;

        if (!username) {
            showNotification('请输入用户名或邮箱', 'warning');
            return;
        }

        // 模拟添加权限
        setTimeout(() => {
            showNotification('权限添加成功', 'success');
            closeModal();
        }, 1000);
    };
}

// 检查API状态
function checkApiStatus() {
    // 模拟API状态检查
    setTimeout(() => {
        isKnowledgeBasePublished = Math.random() > 0.5;
        updateApiStatus();
    }, 1000);
}

// 显示模态框
function showModal(title, bodyContent, confirmText = '确认', cancelText = '取消') {
    modalTitle.textContent = title;
    modalBody.innerHTML = bodyContent;
    modalConfirm.textContent = confirmText;
    modalCancel.textContent = cancelText;
    modal.classList.add('show');
}

// 关闭模态框
function closeModal() {
    modal.classList.remove('show');
    // 重置确认按钮事件
    modalConfirm.onclick = closeModal;
}

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
            const errorMsg = result.msg || '获取向量数据失败';
            showNotification(`获取向量数据失败：${errorMsg}`, 'error');
            chunksList.innerHTML = `
                <div class="empty-state">
                    <i class="fa fa-exclamation-circle"></i>
                    <p>获取向量数据失败</p>
                    <button class="btn btn-primary" onclick="loadLatestVectors()">
                        <i class="fa fa-refresh"></i> 重试
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('获取向量数据失败:', error);
        showNotification('获取向量数据失败，请检查API连接', 'error');
        chunksList.innerHTML = `
            <div class="empty-state">
                <i class="fa fa-exclamation-circle"></i>
                <p>获取向量数据失败</p>
                <button class="btn btn-primary" onclick="loadLatestVectors()">
                    <i class="fa fa-refresh"></i> 重试
                </button>
            </div>
        `;
    }
}

// 渲染向量数据
function renderVectorsData(vectors) {
    if (!vectors || vectors.length === 0) {
        chunksList.innerHTML = `
            <div class="empty-state">
                <i class="fa fa-file-text-o"></i>
                <p>向量库中暂无数据</p>
            </div>
        `;
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
        
        chunksList.appendChild(vectorCard);
        
        // 加载时默认查询相关实体
        getEntitiesByChunkId(vector.pk, vectorCard);
    });
}

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

// 在文本中高亮显示实体
function highlightEntities(text, entities, element) {
    if (!entities || entities.length === 0) {
        element.textContent = text;
        return;
    }
    
    // 过滤出确实存在于文本中的实体
    const existingEntities = entities.filter(entity => {
        const regex = new RegExp(escapeRegExp(entity), 'gi');
        return regex.test(text);
    });
    
    if (existingEntities.length === 0) {
        element.textContent = text;
        return;
    }
    
    // 定义一组颜色
    const entityColors = [
        '#ffeb3b', '#4caf50', '#2196f3', '#ff9800', '#9c27b0',
        '#e91e63', '#00bcd4', '#8bc34a', '#ff5722', '#3f51b5'
    ];
    
    // 创建一个实体到颜色的映射
    const entityColorMap = {};
    existingEntities.forEach((entity, index) => {
        entityColorMap[entity] = entityColors[index % entityColors.length];
    });
    
    // 按照实体长度从长到短排序，确保长实体优先匹配
    existingEntities.sort((a, b) => b.length - a.length);
    
    // 创建正则表达式，匹配所有实体
    const entityRegex = new RegExp(`(${existingEntities.map(entity => escapeRegExp(entity)).join('|')})`, 'gi');
    
    // 使用正则表达式替换文本，添加高亮标记和颜色
    const highlightedText = text.replace(entityRegex, (match) => {
        const color = entityColorMap[match];
        return `<span class="entity-highlight" style="background-color: ${color}">${match}</span>`;
    });
    
    element.innerHTML = highlightedText;
}

// 转义正则表达式特殊字符
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// 显示通知
function showNotification(message, type = 'success') {
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 加载示例数据
function loadSampleData() {
    // 模拟已上传的文件
    selectedFiles = [
        { name: '示例文档1.txt', size: 12345 },
        { name: '示例文档2.pdf', size: 67890 }
    ];
    renderFileList();
    updateFileCount();
    
    // 模拟切片数据
    addSampleChunks('示例文档1.txt');
    addSampleChunks('示例文档2.pdf');
}

// 添加示例切片数据
function addSampleChunks(fileName) {
    const sampleChunks = [
        { id: Date.now() + 1, content: '这是一段示例文本内容，用于展示切片预览功能。', file: fileName, size: 56, time: new Date().toISOString() },
        { id: Date.now() + 2, content: 'Fast-GraphRAG 是一个高效的图知识库系统，可以处理各种类型的文档。', file: fileName, size: 78, time: new Date().toISOString() },
        { id: Date.now() + 3, content: '通过图结构存储和检索信息，可以提供更准确的查询结果。', file: fileName, size: 62, time: new Date().toISOString() }
    ];
    
    chunks.push(...sampleChunks);
    updateChunkCount();
    updateEntityCount();
}

// 更新文件计数
function updateFileCount() {
    const fileCountElement = document.getElementById('file-count');
    if (fileCountElement) {
        fileCountElement.textContent = selectedFiles.length;
    }
}

// 更新切片计数
function updateChunkCount() {
    const chunkCountElement = document.getElementById('chunk-count');
    if (chunkCountElement) {
        chunkCountElement.textContent = chunks.length;
    }
}

// 更新实体计数
function updateEntityCount() {
    const entityCountElement = document.getElementById('entity-count');
    if (entityCountElement) {
        // 模拟实体数量
        entityCountElement.textContent = Math.floor(chunks.length * 2.5);
    }
}

// 加载知识库列表
async function loadKnowledgeBases() {
    refreshKnowledgeBtn.disabled = true;
    refreshKnowledgeBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 加载中...';
    
    try {
        console.log('开始加载知识库列表');
        // 调用后端API获取知识库列表
        const response = await fetch('http://localhost:8000/knowledge-base', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        
        console.log('响应状态:', response.status);
        console.log('响应头部:', response.headers);
        
        const result = await response.json();
        console.log('响应数据:', result);
        
        if (result.code === 200) {
            // 将API返回的数据转换为前端所需的格式
            knowledgeBases = result.data.map(kb => ({
                id: kb.id,
                name: kb.name,
                description: kb.description,
                status: kb.is_active ? 'active' : 'inactive',
                fileCount: 0,  // 目前后端API不返回文件计数，后续可扩展
                chunkCount: 0,  // 目前后端API不返回切片计数，后续可扩展
                entityCount: 0,  // 目前后端API不返回实体计数，后续可扩展
                createTime: kb.created_at,
                updateTime: kb.updated_at
            }));
            
            renderKnowledgeBases();
            showNotification('知识库列表加载成功', 'success');
        } else {
            const errorMsg = result.msg || '未知错误';
            showNotification(`加载知识库失败：${errorMsg}`, 'error');
        }
    } catch (error) {
        console.error('加载知识库失败:', error);
        console.error('错误类型:', error.name);
        console.error('错误信息:', error.message);
        console.error('错误栈:', error.stack);
        showNotification('加载知识库失败，请检查API连接', 'error');
    } finally {
        refreshKnowledgeBtn.disabled = false;
        refreshKnowledgeBtn.innerHTML = '<i class="fa fa-refresh"></i> 刷新列表';
    }
}

// 渲染知识库列表
function renderKnowledgeBases() {
    if (knowledgeBases.length === 0) {
        knowledgeList.innerHTML = `
            <div class="empty-state">
                <i class="fa fa-book-o"></i>
                <p>暂无知识库数据</p>
                <button class="btn btn-primary" onclick="document.getElementById('create-knowledge-btn').click()">
                    <i class="fa fa-plus"></i> 创建第一个知识库
                </button>
            </div>
        `;
        return;
    }
    
    knowledgeList.innerHTML = '';
    
    knowledgeBases.forEach(kb => {
        const card = document.createElement('div');
        card.className = `knowledge-card ${kb.id === currentKnowledgeBase ? 'active' : ''}`;
        card.dataset.id = kb.id;
        
        card.innerHTML = `
            <div class="knowledge-card-header">
                <div>
                    <div class="knowledge-card-title">${kb.name}</div>
                    <div class="knowledge-card-description">${kb.description}</div>
                </div>
                <span class="knowledge-card-status status-${kb.status}">
                    ${kb.status === 'active' ? '活跃' : '已发布'}
                </span>
            </div>
            <div class="knowledge-card-meta">
                <div><i class="fa fa-file"></i> ${kb.fileCount}个文件</div>
                <div><i class="fa fa-file-text-o"></i> ${kb.chunkCount}个切片</div>
                <div><i class="fa fa-tag"></i> ${kb.entityCount}个实体</div>
                <div><i class="fa fa-clock-o"></i> 更新于 ${new Date(kb.updateTime).toLocaleString()}</div>
            </div>
            <div class="knowledge-card-actions">
                <button class="btn btn-primary enter-btn" data-id="${kb.id}">
                    <i class="fa fa-arrow-right"></i> 进入
                </button>
                <button class="btn btn-danger delete-btn" data-id="${kb.id}">
                    <i class="fa fa-trash"></i> 删除
                </button>
            </div>
        `;
        
        // 添加事件监听
        card.querySelector('.enter-btn').addEventListener('click', () => enterKnowledgeBase(kb.id, kb.name));
        card.querySelector('.delete-btn').addEventListener('click', () => deleteKnowledgeBaseItem(kb.id, kb.name));
        
        knowledgeList.appendChild(card);
    });
    
    // 更新所有知识库选择下拉菜单
    updateKnowledgeSelect().then(() => {
        console.log('召回测试区域知识库下拉框已更新');
    }).catch(error => {
        console.error('更新召回测试区域知识库下拉框失败:', error);
    });
    
    updateKnowledgeDropdown(permissionKnowledgeSelect, '选择知识库').then(() => {
        console.log('权限管理区域知识库下拉框已更新');
    }).catch(error => {
        console.error('更新权限管理区域知识库下拉框失败:', error);
    });
    
}

// 更新知识库选择下拉菜单的通用函数（直接调用批量查询API）
async function updateKnowledgeDropdown(dropdownElement, placeholder = '请选择知识库') {
    if (!dropdownElement) return;
    
    // 清空现有选项并显示加载状态
    dropdownElement.innerHTML = `<option value="">${placeholder}...</option>`;
    
    try {
        // 调用后端批量查询接口获取所有知识库
        const response = await fetch('http://localhost:8000/knowledge-base', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            // 清空现有选项
            dropdownElement.innerHTML = `<option value="">${placeholder}</option>`;
            
            // 添加知识库选项
            result.data.forEach(kb => {
                const option = document.createElement('option');
                option.value = kb.id;
                option.textContent = kb.name;
                dropdownElement.appendChild(option);
            });
        } else {
            console.error('批量查询知识库失败:', result.msg);
            // 保持加载状态，让用户知道有错误
            dropdownElement.innerHTML = `<option value="">加载失败，请重试</option>`;
        }
    } catch (error) {
        console.error('批量查询知识库网络错误:', error);
        dropdownElement.innerHTML = `<option value="">网络错误，请重试</option>`;
    }
}

// 更新召回测试区域的知识库选择下拉菜单
async function updateKnowledgeSelect() {
    if (!knowledgeSelect) return;
    await updateKnowledgeDropdown(knowledgeSelect, '请选择知识库');
    
    // 如果当前有选中的知识库，设置为默认选项
    if (currentKnowledgeBase) {
        knowledgeSelect.value = currentKnowledgeBase;
    }
}

// 查看知识库详情
function viewKnowledgeBase(id) {
    const kb = knowledgeBases.find(kb => kb.id === id);
    if (!kb) return;
    
    showModal('知识库详情', `
        <div class="knowledge-detail">
            <div class="detail-item">
                <label>知识库名称：</label>
                <span>${kb.name}</span>
            </div>
            <div class="detail-item">
                <label>描述：</label>
                <span>${kb.description}</span>
            </div>
            <div class="detail-item">
                <label>状态：</label>
                <span class="knowledge-card-status status-${kb.status}">
                    ${kb.status === 'active' ? '活跃' : '已发布'}
                </span>
            </div>
            <div class="detail-item">
                <label>文件数量：</label>
                <span>${kb.fileCount}</span>
            </div>
            <div class="detail-item">
                <label>切片数量：</label>
                <span>${kb.chunkCount}</span>
            </div>
            <div class="detail-item">
                <label>实体数量：</label>
                <span>${kb.entityCount}</span>
            </div>
            <div class="detail-item">
                <label>创建时间：</label>
                <span>${new Date(kb.createTime).toLocaleString()}</span>
            </div>
            <div class="detail-item">
                <label>更新时间：</label>
                <span>${new Date(kb.updateTime).toLocaleString()}</span>
            </div>
        </div>
    `);
}

// 切换当前知识库
function switchKnowledgeBase(id) {
    const kb = knowledgeBases.find(kb => kb.id === id);
    if (!kb) return;
    
    currentKnowledgeBase = id;
    
    // 更新卡片状态
    document.querySelectorAll('.knowledge-card').forEach(card => {
        card.classList.remove('active');
        if (card.dataset.id === id) {
            card.classList.add('active');
        }
    });
    
    // 更新发布管理中的知识库名称
    const knowledgeNameInput = document.getElementById('knowledge-name');
    if (knowledgeNameInput) {
        knowledgeNameInput.value = kb.name;
    }
    
    // 更新统计信息
    updateKnowledgeStats(kb);
    
    // 如果当前在切片预览、发布管理或API接口选项卡，更新内容
    const activeTab = document.querySelector('.knowledge-tabs .tab-btn.active');
    if (activeTab) {
        const tabId = activeTab.getAttribute('data-tab');
        if (tabId === 'chunks' || tabId === 'publish' || tabId === 'api') {
            switchTab(tabId);
        }
    }
    
    showNotification(`已切换到知识库 "${kb.name}"`, 'success');
}

// 更新知识库统计信息
function updateKnowledgeStats(kb) {
    const fileCountElement = document.getElementById('file-count');
    const chunkCountElement = document.getElementById('chunk-count');
    const entityCountElement = document.getElementById('entity-count');
    
    if (fileCountElement) fileCountElement.textContent = kb.fileCount;
    if (chunkCountElement) chunkCountElement.textContent = kb.chunkCount;
    if (entityCountElement) entityCountElement.textContent = kb.entityCount;
}

// 删除知识库
function deleteKnowledgeBaseItem(id, name) {
    showModal('删除知识库', `
        <div class="delete-knowledge-confirm">
            <p class="warning-text">您确定要删除知识库 "${name}" 吗？此操作不可恢复。</p>
            <div class="delete-options">
                <label>
                    <input type="checkbox" id="delete-with-data"> 同时删除所有数据
                </label>
            </div>
        </div>
    `);
    
    modalConfirm.onclick = async () => {
        try {
            // 调用后端API删除知识库
            const response = await fetch(`http://localhost:8000/knowledge-base/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.code === 200) {
                // 更新前端数据
                knowledgeBases = knowledgeBases.filter(kb => kb.id !== id);
                if (currentKnowledgeBase === id) {
                    currentKnowledgeBase = knowledgeBases.length > 0 ? knowledgeBases[0].id : null;
                }
                
                renderKnowledgeBases();
                
                // 清空当前的数据
                selectedFiles = [];
                renderFileList();
                chunks = [];
                updateChunkCount();
                updateFileCount();
                
                showNotification(`知识库 "${name}" 删除成功`, 'success');
            } else {
                const errorMsg = result.msg || '未知错误';
                showNotification(`删除知识库失败：${errorMsg}`, 'error');
            }
        } catch (error) {
            console.error('删除知识库失败:', error);
            showNotification('删除知识库失败，请检查API连接', 'error');
        } finally {
            closeModal();
        }
    };
}

// 进入知识库
function enterKnowledgeBase(id, name) {
    // 设置当前知识库
    currentKnowledgeBase = id;
    
    // 隐藏知识库列表选项卡，显示其他功能选项卡
    const knowledgeTabBtns = document.querySelectorAll('.knowledge-tabs .tab-btn');
    const knowledgeTabContents = document.querySelectorAll('#knowledge .tab-content');
    
    knowledgeTabBtns.forEach(btn => {
        const tabId = btn.getAttribute('data-tab');
        if (tabId === 'list') {
            btn.classList.add('hidden-tab');
        } else {
            btn.classList.remove('hidden-tab');
            btn.style.display = 'block';
        }
    });
    
    knowledgeTabContents.forEach(content => {
        const tabId = content.id.replace('tab-', '');
        // 隐藏所有标签内容，后续会由switchTab函数显示当前选中的标签内容
        content.style.display = 'none';
        content.classList.remove('active');
    });
    
    // 切换到文件上传选项卡
    switchTab('upload');
    
    // 更新知识库统计信息
    const kb = knowledgeBases.find(kb => kb.id === id);
    if (kb) {
        updateKnowledgeStats(kb);
    }
    
    // 更新知识库卡片的激活状态
    renderKnowledgeBases();
    
    // 显示通知
    showNotification(`已进入知识库 "${name}"`, 'success');
}

// 加载图数据
async function loadGraphData() {
    if (!currentKnowledgeBase) {
        showNotification('请先选择知识库', 'warning');
        return;
    }
    
    // 显示加载状态
    graphCanvas.innerHTML = `
        <div class="loading-state">
            <i class="fa fa-spinner fa-spin"></i>
            <p>正在加载图数据...</p>
        </div>
    `;
    
    try {
        const response = await fetch('http://localhost:8000/graph-db/all');
        const result = await response.json();
        
        if (result.code === 200) {
            graphData = result.data;
            renderGraph(graphData);
            updateGraphStats(graphData.nodes.length, graphData.relationships.length);
            showNotification('图数据加载成功', 'success');
        } else {
            throw new Error(result.msg || '加载图数据失败');
        }
    } catch (error) {
        console.error('加载图数据失败:', error);
        graphCanvas.innerHTML = `
            <div class="error-state">
                <i class="fa fa-exclamation-circle"></i>
                <p>加载图数据失败：${error.message}</p>
            </div>
        `;
        showNotification(`加载图数据失败：${error.message}`, 'error');
    }
}

// 渲染图数据
function renderGraph(data) {
    // 清空画布
    graphCanvas.innerHTML = '';
    
    if (!data.nodes || data.nodes.length === 0) {
        graphCanvas.innerHTML = `
            <div class="empty-state">
                <i class="fa fa-sitemap"></i>
                <p>暂无图数据</p>
            </div>
        `;
        return;
    }
    
    const width = graphCanvas.clientWidth;
    const height = graphCanvas.clientHeight;
    
    // 创建SVG元素
    const svg = d3.select(graphCanvas)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("background-color", "#fafafa")
        .style("border-radius", "4px");
    
    // 创建缩放行为
    const zoom = d3.zoom()
        .scaleExtent([0.1, 3])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        });
    
    svg.call(zoom);
    
    // 创建缩放容器
    const g = svg.append("g");
    
    // 准备D3需要的数据格式
    const nodes = data.nodes.map(node => ({
        ...node,
        id: node.id
    }));
    
    const links = data.relationships.map(rel => ({
        source: rel.start_node_id,
        target: rel.end_node_id,
        type: rel.type,
        id: rel.id,
        properties: rel.properties
    }));
    
    // 创建力导向模拟
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(150))
        .force("charge", d3.forceManyBody().strength(-500))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(d => {
            // 根据节点内容动态调整大小
            const label = d.properties.name || d.properties.title || d.id.substring(0, 6);
            return Math.max(30, label.length * 4 + 10);
        }));
    
    // 创建箭头标记
    svg.append("defs").selectAll("marker")
        .data(Array.from(new Set(links.map(d => d.type))))
        .join("marker")
        .attr("id", d => `arrow-${d}`)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 6)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#666");
    
    // 绘制关系
    const link = g.append("g")
        .selectAll("line")
        .data(links)
        .join("line")
        .attr("stroke", "#666")
        .attr("stroke-width", 2)
        .attr("marker-end", d => `url(#arrow-${d.type})`);
    
    // 绘制关系标签
    const linkLabel = g.append("g")
        .selectAll("g")
        .data(links)
        .join("g")
        .attr("class", "link-label");
    
    linkLabel.append("rect")
        .attr("fill", "#ffffff")
        .attr("rx", 3)
        .attr("ry", 3)
        .attr("padding", 5)
        .style("stroke", "#ddd")
        .style("stroke-width", 1);
    
    linkLabel.append("text")
        .text(d => d.type)
        .attr("font-size", "12px")
        .attr("fill", "#333")
        .attr("text-anchor", "middle")
        .attr("dy", ".35em");
    
    // 节点颜色映射
    const labelColors = {
        "Person": "#3498db",
        "Organization": "#e74c3c",
        "Location": "#2ecc71",
        "Event": "#f39c12",
        "Concept": "#9b59b6",
        "Entity": "#1abc9c"
    };
    
    // 获取节点颜色
    const getNodeColor = (node) => {
        if (node.labels && node.labels.length > 0) {
            for (const label of node.labels) {
                if (labelColors[label]) {
                    return labelColors[label];
                }
            }
            return labelColors["Entity"];
        }
        return "#95a5a6";
    };
    
    // 绘制节点组
    const node = g.append("g")
        .selectAll("g")
        .data(nodes)
        .join("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
    
    // 绘制节点圆圈
    node.append("circle")
        .attr("r", d => {
            const label = d.properties.name || d.properties.title || d.id.substring(0, 6);
            return Math.max(25, label.length * 3.5 + 10);
        })
        .attr("fill", getNodeColor)
        .attr("stroke", d => d3.color(getNodeColor(d)).darker(0.3))
        .attr("stroke-width", 2)
        .style("cursor", "pointer")
        .on("click", (event, d) => {
            showNodeDetails(d);
        });
    
    // 绘制节点标签
    node.append("text")
        .text(d => {
            const label = d.properties.name || d.properties.title || d.id.substring(0, 6);
            return label.length > 15 ? label.substring(0, 12) + "..." : label;
        })
        .attr("font-size", "12px")
        .attr("font-weight", "bold")
        .attr("text-anchor", "middle")
        .attr("dy", ".35em")
        .attr("fill", "white")
        .attr("pointer-events", "none");
    
    // 绘制节点标签（在节点下方）
    node.append("text")
        .text(d => {
            if (d.labels && d.labels.length > 0) {
                return d.labels[0];
            }
            return "Node";
        })
        .attr("font-size", "9px")
        .attr("text-anchor", "middle")
        .attr("dy", (d) => {
            const label = d.properties.name || d.properties.title || d.id.substring(0, 6);
            return Math.max(25, label.length * 3.5 + 10) + 15;
        })
        .attr("fill", "#666")
        .attr("pointer-events", "none");
    
    // 更新位置
    simulation.on("tick", () => {
        // 更新关系位置
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        // 更新关系标签位置
        linkLabel
            .attr("transform", d => {
                const x = (d.source.x + d.target.x) / 2;
                const y = (d.source.y + d.target.y) / 2;
                return `translate(${x},${y})`;
            });
        
        // 调整关系标签背景大小
        linkLabel.select("rect")
            .each(function(d) {
                const bbox = this.nextSibling.getBBox();
                d3.select(this)
                    .attr("x", bbox.x - 5)
                    .attr("y", bbox.y - 5)
                    .attr("width", bbox.width + 10)
                    .attr("height", bbox.height + 10);
            });
        
        // 更新节点位置
        node.attr("transform", d => `translate(${d.x},${d.y})`);
    });
    
    // 拖拽事件处理
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// 显示节点详情
function showNodeDetails(node) {
    let properties = '';
    for (const [key, value] of Object.entries(node.properties)) {
        properties += `<div><strong>${key}:</strong> ${value}</div>`;
    }
    
    showModal('节点详情', `
        <div class="node-details">
            <div class="node-header">
                <h4>${node.id}</h4>
                <div class="node-labels">
                    ${node.labels.map(label => `<span class="label-tag">${label}</span>`).join('')}
                </div>
            </div>
            <div class="node-properties">
                <h5>属性</h5>
                ${properties}
            </div>
        </div>
    `);
}

// 更新图统计信息
function updateGraphStats(nodeCount, relationshipCount) {
    if (nodeCountElement) {
        nodeCountElement.textContent = nodeCount;
    }
    if (relationshipCountElement) {
        relationshipCountElement.textContent = relationshipCount;
    }
}

// 导出图数据
function exportGraphData() {
    if (!graphData || graphData.nodes.length === 0) {
        showNotification('暂无图数据可导出', 'warning');
        return;
    }
    
    const dataStr = JSON.stringify(graphData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `graph_data_${currentKnowledgeBase}_${new Date().toISOString().slice(0, 19)}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    showNotification('图数据导出成功', 'success');
}

// 更新初始化函数，添加加载知识库列表
function init() {
    // 绑定事件监听
    bindEventListeners();
    
    // 加载示例数据
    loadSampleData();
    
    // 模拟API状态检查
    checkApiStatus();
    
    // 加载知识库列表
    loadKnowledgeBases();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);