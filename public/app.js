console.log('VenturePulse app.js loading...');

var allProviders = {};
var currentConfig = {};

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready, initializing...');
    
    // Setup tab navigation
    var tabs = document.querySelectorAll('.tab');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            var tabName = tab.getAttribute('data-tab');
            console.log('Switching to tab:', tabName);
            
            tabs.forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            
            var contents = document.querySelectorAll('.tab-content');
            contents.forEach(function(c) { c.classList.remove('active'); });
            document.getElementById(tabName + '-tab').classList.add('active');
            
            if (tabName === 'prompts') loadPromptsTab();
            if (tabName === 'history') loadHistoryTab();
            if (tabName === 'settings') loadSettingsTab();
        });
    });
    
    loadConfig();
    loadPrompts();
});

function loadConfig() {
    console.log('Loading configuration...');
    fetch('/api/config')
        .then(function(r) { return r.json(); })
        .then(function(config) {
            console.log('Config loaded:', config);
            currentConfig = config;
            allProviders = config.providers;
            
            var providerSelect = document.getElementById('providerSelect');
            providerSelect.innerHTML = '';
            
            Object.keys(allProviders).forEach(function(key) {
                var option = document.createElement('option');
                option.value = key;
                option.textContent = allProviders[key].name;
                providerSelect.appendChild(option);
            });
            
            // Set to .env default
            providerSelect.value = config.currentProvider;
            updateModelList();
            
            console.log('Provider dropdown populated with .env defaults');
        })
        .catch(function(e) {
            console.error('Error loading config:', e);
        });
}

function updateModelList() {
    var providerSelect = document.getElementById('providerSelect');
    var modelSelect = document.getElementById('modelSelect');
    var selectedProvider = providerSelect.value;
    
    console.log('Updating models for provider:', selectedProvider);
    
    if (!selectedProvider || !allProviders[selectedProvider]) {
        modelSelect.innerHTML = '<option value="">Select provider first</option>';
        return;
    }
    
    var provider = allProviders[selectedProvider];
    modelSelect.innerHTML = '';
    
    provider.models.forEach(function(model) {
        var option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        modelSelect.appendChild(option);
    });
    
    // Set to .env default if it matches
    if (currentConfig.defaultModel && provider.models.indexOf(currentConfig.defaultModel) !== -1) {
        modelSelect.value = currentConfig.defaultModel;
    }
    
    console.log('Models loaded:', provider.models.length);
}

function loadPrompts() {
    console.log('Loading prompts dropdown...');
    fetch('/api/prompts')
        .then(function(r) { return r.json(); })
        .then(function(prompts) {
            var select = document.getElementById('promptSelect');
            select.innerHTML = '';
            
            if (prompts.length === 0) {
                select.innerHTML = '<option value="">No prompts available</option>';
            } else {
                prompts.forEach(function(p) {
                    var option = document.createElement('option');
                    option.value = p.filename;
                    option.textContent = p.name;
                    select.appendChild(option);
                });
            }
            
            console.log('Prompts dropdown loaded:', prompts.length, 'prompts');
        })
        .catch(function(e) {
            console.error('Error loading prompts:', e);
        });
}

function loadPromptsTab() {
    console.log('Loading prompts tab...');
    fetch('/api/prompts')
        .then(function(r) { return r.json(); })
        .then(function(prompts) {
            var list = document.getElementById('promptsList');
            if (prompts.length === 0) {
                list.innerHTML = '<p>No prompts found</p>';
            } else {
                list.innerHTML = prompts.map(function(p) {
                    return '<div class="prompt-item"><div><strong>' + p.name + '</strong><br><small>Modified: ' + new Date(p.modified).toLocaleString() + '</small></div><div class="item-actions"><button onclick="viewPrompt(\'' + p.filename + '\')">View</button></div></div>';
                }).join('');
            }
        });
}

function loadHistoryTab() {
    console.log('Loading history tab...');
    fetch('/api/analysis')
        .then(function(r) { return r.json(); })
        .then(function(analyses) {
            var list = document.getElementById('historyList');
            if (analyses.length === 0) {
                list.innerHTML = '<p>No analyses yet. Create your first one!</p>';
            } else {
                list.innerHTML = analyses.map(function(a) {
                    return '<div class="analysis-item"><div><strong>' + a.name + '</strong><br><small>' + new Date(a.created).toLocaleString() + ' • ' + (a.size/1024).toFixed(1) + ' KB</small></div><div class="item-actions"><button onclick="viewAnalysis(\'' + a.filename + '\')">View</button><button onclick="downloadAnalysis(\'' + a.filename + '\')">Download</button><button onclick="deleteAnalysis(\'' + a.filename + '\')">Delete</button></div></div>';
                }).join('');
            }
        });
}

function loadSettingsTab() {
    console.log('Loading settings tab...');
    fetch('/api/config')
        .then(function(r) { return r.json(); })
        .then(function(config) {
            var content = document.getElementById('settingsContent');
            var providers = Object.keys(config.providers).map(function(key) {
                var p = config.providers[key];
                return '<li><strong>' + p.name + '</strong> - Models: ' + p.models.join(', ') + '</li>';
            }).join('');
            
            content.innerHTML = '<div class="config-item"><strong>Current Provider (from .env):</strong> ' + config.currentProvider + '</div>' +
                '<div class="config-item"><strong>Default Model (from .env):</strong> ' + (config.defaultModel || 'Not set') + '</div>' +
                '<div class="config-item"><strong>API Key:</strong> ' + (config.hasApiKey ? '✅ Configured' : '❌ Not set') + '</div>' +
                '<div class="config-item"><strong>Available Providers:</strong><ul>' + providers + '</ul></div>' +
                '<p><small>💡 Provider/model selection in UI is for current session only. To change defaults, edit .env file.</small></p>';
        });
}

function uploadFile() {
    var fileInput = document.getElementById('fileUpload');
    var file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file first');
        return;
    }
    
    var formData = new FormData();
    formData.append('file', file);
    
    showStatus('Uploading and extracting text...', 'info');
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.extractedText) {
            document.getElementById('projectContent').value = data.extractedText;
            showStatus('File uploaded: ' + data.originalName, 'success');
        } else {
            showStatus('Error: ' + (data.error || 'Upload failed'), 'error');
        }
    })
    .catch(function(e) {
        showStatus('Upload failed: ' + e.message, 'error');
    });
}

function runAnalysis() {
    var projectName = document.getElementById('projectName').value.trim();
    var projectContent = document.getElementById('projectContent').value.trim();
    var promptFile = document.getElementById('promptSelect').value;
    var selectedProvider = document.getElementById('providerSelect').value;
    var selectedModel = document.getElementById('modelSelect').value;
    
    if (!projectName) {
        alert('Please enter a project name');
        return;
    }
    
    if (!projectContent) {
        alert('Please enter project description or upload a document');
        return;
    }
    
    if (!promptFile) {
        alert('Please select a prompt');
        return;
    }
    
    if (!selectedProvider || !selectedModel) {
        alert('Please select provider and model');
        return;
    }
    
    console.log('Starting analysis with:', {
        provider: selectedProvider,
        model: selectedModel,
        prompt: promptFile
    });
    
    showStatus('Loading prompt...', 'info');
    
    fetch('/api/prompts/' + promptFile)
        .then(function(r) { return r.json(); })
        .then(function(promptData) {
            showStatus('Running AI analysis with ' + selectedProvider + '/' + selectedModel + '... This may take 1-2 minutes.', 'info');
            
            return fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    promptContent: promptData.content,
                    projectContent: projectContent,
                    projectName: projectName,
                    provider: selectedProvider,
                    model: selectedModel
                })
            });
        })
        .then(function(r) { return r.json(); })
        .then(function(result) {
            if (result.success) {
                showStatus('✅ Analysis complete! Saved as: ' + result.filename, 'success');
                setTimeout(function() {
                    document.querySelector('[data-tab="history"]').click();
                }, 2000);
            } else {
                showStatus('❌ Analysis failed: ' + (result.error || 'Unknown error'), 'error');
            }
        })
        .catch(function(e) {
            showStatus('❌ Error: ' + e.message, 'error');
            console.error('Analysis error:', e);
        });
}

function viewPrompt(filename) {
    fetch('/api/prompts/' + filename)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            alert(data.content);
        });
}

function viewAnalysis(filename) {
    window.open('/api/analysis/' + filename, '_blank');
}

function downloadAnalysis(filename) {
    var link = document.createElement('a');
    link.href = '/api/analysis/' + filename;
    link.download = filename;
    link.click();
}

function deleteAnalysis(filename) {
    if (confirm('Delete ' + filename + '?')) {
        fetch('/api/analysis/' + filename, {method: 'DELETE'})
            .then(function() {
                loadHistoryTab();
            });
    }
}

function showStatus(message, type) {
    var statusBox = document.getElementById('analysisStatus');
    statusBox.textContent = message;
    statusBox.className = 'status-box ' + type;
    statusBox.style.display = 'block';
}

console.log('✅ App.js loaded successfully');
