// 全域初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Bootstrap提示工具
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化圖片預覽功能
    initImagePreview();
    
    // 初始化確認對話框
    initConfirmDialogs();
    
    // 自動隱藏通知訊息
    initAutoHideAlerts();
});

// 圖片預覽功能
function initImagePreview() {
    const imageInput = document.getElementById('id_image');
    if (!imageInput) return;
    
    const previewImage = document.getElementById('preview-image');
    const noPreview = document.getElementById('no-preview');
    
    imageInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.classList.remove('hidden');
                if (noPreview) {
                    noPreview.classList.add('hidden');
                }
            }
            
            reader.readAsDataURL(this.files[0]);
        }
    });
}

// 確認對話框
function initConfirmDialogs() {
    const confirmForms = document.querySelectorAll('.confirm-form');
    confirmForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = this.getAttribute('data-confirm-message') || '確定要執行此操作嗎？';
            const title = this.getAttribute('data-confirm-title') || '確認';
            
            if (confirm(message)) {
                this.submit();
            }
        });
    });
}

// 自動隱藏通知訊息
function initAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            // 創建淡出效果
            alert.style.transition = 'opacity 1s';
            alert.style.opacity = '0';
            
            // 淡出後移除元素
            setTimeout(() => {
                alert.remove();
            }, 1000);
        }, 5000);
    });
}

// 類別過濾器
function filterByCategory(selectElement) {
    const form = selectElement.closest('form');
    if (form) {
        form.submit();
    }
}

// 複製到剪貼簿
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    // 顯示提示
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });
    
    Toast.fire({
        icon: 'success',
        title: '已複製到剪貼簿'
    });
}

// 關鍵字標籤輸入
function initTagInput() {
    const keywordsInput = document.getElementById('id_keywords');
    if (!keywordsInput) return;
    
    // 創建標籤容器
    const tagContainer = document.createElement('div');
    tagContainer.className = 'tag-container d-flex flex-wrap gap-2 mt-2';
    keywordsInput.parentNode.insertBefore(tagContainer, keywordsInput.nextSibling);
    
    // 分割關鍵字並創建標籤
    function updateTags() {
        tagContainer.innerHTML = '';
        const keywords = keywordsInput.value.split(',');
        
        keywords.forEach(keyword => {
            keyword = keyword.trim();
            if (keyword) {
                const tag = document.createElement('span');
                tag.className = 'badge bg-primary d-flex align-items-center';
                tag.innerHTML = `
                    ${keyword}
                    <button type="button" class="btn-close btn-close-white ms-2" aria-label="Close"></button>
                `;
                
                // 刪除標籤
                tag.querySelector('.btn-close').addEventListener('click', function() {
                    const newKeywords = keywordsInput.value
                        .split(',')
                        .filter(k => k.trim() && k.trim() !== keyword)
                        .join(', ');
                        
                    keywordsInput.value = newKeywords;
                    updateTags();
                });
                
                tagContainer.appendChild(tag);
            }
        });
    }
    
    // 初始更新
    updateTags();
    
    // 監聽變更
    keywordsInput.addEventListener('blur', updateTags);
    keywordsInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            updateTags();
        }
    });
}

// 動態表單控制
function toggleFormSection(checkboxId, sectionId) {
    const checkbox = document.getElementById(checkboxId);
    const section = document.getElementById(sectionId);
    
    if (!checkbox || !section) return;
    
    function updateVisibility() {
        if (checkbox.checked) {
            section.classList.remove('d-none');
            // 設置必填
            section.querySelectorAll('.form-control').forEach(input => {
                input.required = true;
            });
        } else {
            section.classList.add('d-none');
            // 取消必填
            section.querySelectorAll('.form-control').forEach(input => {
                input.required = false;
            });
        }
    }
    
    // 初始更新
    updateVisibility();
    
    // 監聽變更
    checkbox.addEventListener('change', updateVisibility);
}