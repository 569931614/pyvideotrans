let bridge = null;
let selectedVideos = [];
let taskUuidMap = {}; // Map video path -> uuid
let progressPollInterval = null;

function initChannel() {
  new QWebChannel(qt.webChannelTransport, function (channel) {
    bridge = channel.objects.bridge;
    bindBridgeSignals();
    bootstrap();
  });
}

function bindBridgeSignals() {
  if (!bridge || !bridge.notify) return;
  bridge.notify.connect((event, payload) => {
    if (event === 'proxyChanged') {
      showNotification('代理已更新', 'success');
    }
  });
}

async function bootstrap() {
  try {
    console.log('Bootstrap开始...');

    const state = await bridge.getInitState();
    console.log('获取初始状态:', state);

    if (state && state.version) {
      document.getElementById('version').innerText = state.version;
    }
    if (state && state.targetDir) {
      document.getElementById('save-dir').innerText = state.targetDir;
    }
    if (state && state.proxy !== undefined) {
      document.getElementById('proxy').value = state.proxy || '';
    }

    // Load full option sets
    const opts = await bridge.getOptions();
    console.log('获取选项配置:', opts);

    if (opts.error) {
      showNotification('加载选项失败: ' + opts.error, 'error');
      return;
    }

    // Populate all selects
    console.log('开始填充下拉选项...');
    populateSelect('translate-type', opts.translateTypes, opts.selected.translate_type);
    populateSelect('source-language', opts.languages, opts.selected.source_language);
    const targetLangs = [{ value: '-', label: '-' }].concat(opts.languages.slice(0, -1));
    populateSelect('target-language', targetLangs, opts.selected.target_language || '-');
    populateSelect('recogn-type', opts.recognitionTypes, opts.selected.recogn_type);
    // Decide model list based on recogn_type
    populateModelByRecogn(opts.selected.recogn_type, opts);
    populateSplit(opts.splitTypes, opts.selected.split_type);
    populateSelect('tts-type', opts.ttsTypes, opts.selected.tts_type);
    populateSelect('subtitle-type', opts.subtitleTypes, opts.selected.subtitle_type);

    // Populate voice role select
    const voiceRoles = opts.voiceRoles || [];
    if (voiceRoles.length > 0) {
      const defaultRole = opts.selected.voice_role || (voiceRoles[0] ? voiceRoles[0].value : 'No');
      populateSelect('voice-role', voiceRoles, defaultRole);
    } else {
      populateSelect('voice-role', [{ value: 'No', label: 'No' }], 'No');
    }

    console.log('下拉选项填充完成');

    // Load HearSight folders
    await loadHearSightFolders();
    console.log('HearSight文件夹加载完成');

    // Bind select events AFTER they are created
    bindSelectEvents();
    console.log('绑定下拉事件完成');

  // Bind settings button events
  bindSettingsButtons();
  console.log('绑定设置按钮事件完成');

    // Set text input values
    const voiceRateEl = document.getElementById('voice-rate');
    const volumeEl = document.getElementById('volume');
    const pitchEl = document.getElementById('pitch');
    const trimStartEl = document.getElementById('trim-start');
    const trimEndEl = document.getElementById('trim-end');

    if (voiceRateEl) voiceRateEl.value = opts.selected.voice_rate || 0;
    if (volumeEl) volumeEl.value = opts.selected.volume || 0;
    if (pitchEl) pitchEl.value = opts.selected.pitch || 0;
    if (trimStartEl) trimStartEl.value = opts.selected.trim_start || 0;
    if (trimEndEl) trimEndEl.value = opts.selected.trim_end || 0;

    // Set checkbox values
    const checkboxes = [
      { id: 'voice-autorate', key: 'voice_autorate' },
      { id: 'video-autorate', key: 'video_autorate' },
      { id: 'enable-cuda', key: 'enable_cuda' },
      { id: 'enable-hearsight', key: 'enable_hearsight' },
      { id: 'enable-preprocess', key: 'enable_preprocess' },
      { id: 'aisendsrt', key: 'aisendsrt' },
      { id: 'remove-noise', key: 'remove_noise' }
    ];

    checkboxes.forEach(({ id, key }) => {
      const el = document.getElementById(id);
      if (el) el.checked = !!opts.selected[key];
    });

    console.log('Bootstrap完成');
    showNotification('配置加载完成', 'success');
  } catch (e) {
    console.error('Bootstrap失败:', e);
    showNotification('初始化失败: ' + e.message, 'error');
  }
}

function setupHandlers() {
  console.log('设置基础事件处理器...');

  document.getElementById('btn-select-video').addEventListener('click', async () => {
    const result = await bridge.selectVideo();
    selectedVideos = result.files || [];
    updateTaskQueue();
    const count = selectedVideos.length;
    document.getElementById('video-count').innerText = count > 0
      ? `已选择 ${count} 个文件`
      : '未选择视频';

    // 更新保存目录显示
    if (result.target_dir) {
      document.getElementById('save-dir').innerText = result.target_dir;
    }

    if (count > 0) {
      showNotification(`已选择 ${count} 个视频`, 'success');
    }
  });

  document.getElementById('btn-save-dir').addEventListener('click', async () => {
    const dir = await bridge.selectSaveDir();
    if (dir) {
      document.getElementById('save-dir').innerText = dir;
      showNotification('保存目录已更新', 'success');
    }
  });

  // 点击保存目录路径直接打开文件夹
  document.getElementById('save-dir').addEventListener('click', async () => {
    const saveDirText = document.getElementById('save-dir').innerText;
    if (saveDirText === '未选择' || !saveDirText) {
      showNotification('请先选择保存目录', 'info');
      return;
    }

    try {
      const result = await bridge.openSaveDir();
      if (result.success) {
        showNotification('已打开文件夹', 'success');
      } else {
        showNotification(result.message || '打开文件夹失败', 'error');
      }
    } catch (e) {
      showNotification('打开文件夹失败: ' + e.message, 'error');
    }
  });

  document.getElementById('proxy').addEventListener('change', (e) => {
    bridge.setParams({ proxy: e.target.value || '' });
  });

  document.getElementById('btn-start').addEventListener('click', async () => {
    const btn = document.getElementById('btn-start');
    btn.disabled = true;
    btn.textContent = '处理中...';

    try {
      // 在开始任务前，确保读取并保存trim_start和trim_end的当前值
      const trimStartEl = document.getElementById('trim-start');
      const trimEndEl = document.getElementById('trim-end');
      if (trimStartEl) {
        const trimStartValue = parseFloat(trimStartEl.value || '0');
        await bridge.setParams({ trim_start: trimStartValue });
        console.log('[DEBUG] Set trim_start:', trimStartValue);
      }
      if (trimEndEl) {
        const trimEndValue = parseFloat(trimEndEl.value || '0');
        await bridge.setParams({ trim_end: trimEndValue });
        console.log('[DEBUG] Set trim_end:', trimEndValue);
      }

      // 等待50ms确保参数已保存
      await new Promise(resolve => setTimeout(resolve, 50));

      const result = await bridge.startTranslate();
      console.log('startTranslate result:', result);
      if (result && result.success) {
        // Update taskUuidMap with returned UUIDs
        if (result.task_uuids && Array.isArray(result.task_uuids)) {
          console.log('Received task_uuids:', result.task_uuids);
          console.log('Current selectedVideos:', selectedVideos);
          result.task_uuids.forEach(item => {
            console.log(`Mapping path "${item.path}" to UUID "${item.uuid}"`);
            taskUuidMap[item.path] = item.uuid;
          });
          console.log('Task UUIDs updated:', taskUuidMap);

          // Rebuild task queue with UUIDs
          updateTaskQueue();
        } else {
          console.warn('No task_uuids in result or not an array');
        }

        showNotification('处理已启动', 'success');
        // Start polling for progress
        startProgressPolling();
      } else {
        showNotification('启动失败，请检查设置', 'error');
      }
    } catch (e) {
      console.error('Start translate error:', e);
      showNotification('启动失败: ' + e.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '开始处理';
    }
  });

  // Bind input fields
  const voiceRate = document.getElementById('voice-rate');
  const volume = document.getElementById('volume');
  const pitch = document.getElementById('pitch');
  const trimStart = document.getElementById('trim-start');
  const trimEnd = document.getElementById('trim-end');

  if (voiceRate) {
    voiceRate.addEventListener('change', (e) => {
      bridge.setParams({ voice_rate: parseInt(e.target.value || '0', 10) });
    });
  }

  if (volume) {
    volume.addEventListener('change', (e) => {
      bridge.setParams({ volume: parseInt(e.target.value || '0', 10) });
    });
  }

  if (pitch) {
    pitch.addEventListener('change', (e) => {
      bridge.setParams({ pitch: parseInt(e.target.value || '0', 10) });
    });
  }

  if (trimStart) {
    trimStart.addEventListener('change', (e) => {
      bridge.setParams({ trim_start: parseFloat(e.target.value || '0') });
    });
  }

  if (trimEnd) {
    trimEnd.addEventListener('change', (e) => {
      bridge.setParams({ trim_end: parseFloat(e.target.value || '0') });
    });
  }

  // Bind checkboxes
  const checkboxIds = ['voice-autorate', 'video-autorate', 'enable-cuda', 'enable-hearsight', 'enable-preprocess', 'aisendsrt', 'remove-noise'];
  const checkboxKeys = {
    'voice-autorate': 'voice_autorate',
    'video-autorate': 'video_autorate',
    'enable-cuda': 'cuda',
    'enable-hearsight': 'enable_hearsight',
    'enable-preprocess': 'enable_preprocess',
    'aisendsrt': 'aisendsrt',
    'remove-noise': 'remove_noise'
  };

  checkboxIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', (e) => {
        const payload = {};
        payload[checkboxKeys[id]] = !!e.target.checked;
        bridge.setParams(payload);
      });
    }
  });
}

function bindSelectEvents() {
  console.log('绑定下拉列表事件...');

  // Bind selects - these are created dynamically, so bind AFTER populateSelect
  bindSelect('target-language', 'target_language');
  bindSelect('source-language', 'source_language');
  bindSelect('translate-type', 'translate_type', (v) => parseInt(v, 10));
  bindSelect('recogn-type', 'recogn_type', (v) => {
    onRecognChanged();
    return parseInt(v, 10);
  });
  bindSelect('tts-type', 'tts_type', (v) => parseInt(v, 10));
  bindSelect('subtitle-type', 'subtitle_type', (v) => parseInt(v, 10));
  bindSelect('voice-role', 'voice_role');

  const modelName = document.getElementById('model-name');
  if (modelName) {
    modelName.addEventListener('cschange', (e) => {
      bridge.setParams({ model_name: e.detail.value });
    });
  }

  const splitType = document.getElementById('split-type');
  if (splitType) {
    splitType.addEventListener('cschange', (e) => {
      bridge.setParams({ split_type: e.detail.value });
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  setupHandlers();
  initChannel();
});

// ========== Custom Select Component ==========

function populateSelect(id, list, selected) {
  const container = document.getElementById(id + '-container');
  if (!container) {
    console.error('❌ Container未找到:', id + '-container');
    return;
  }

  console.log(`✓ 填充下拉框 ${id}, 选项数:`, list?.length || 0, '选中值:', selected);

  // Clear existing content
  container.innerHTML = '';

  if (!list || list.length === 0) {
    console.warn(`⚠ ${id} 的选项列表为空`);
    return;
  }

  const valueStr = (v) => String(v === undefined || v === null ? '' : v);
  const selectedValue = valueStr(selected);

  // Create trigger button
  const trigger = document.createElement('div');
  trigger.className = 'custom-select-trigger';
  trigger.id = id;
  trigger.tabIndex = 0;

  // Create dropdown menu
  const menu = document.createElement('div');
  menu.className = 'custom-select-menu';
  menu.id = id + '__menu';

  // Hidden input to store value
  const hidden = document.createElement('input');
  hidden.type = 'hidden';
  hidden.id = id + '__value';
  hidden.value = selectedValue;

  // Populate menu items
  let selectedLabel = '';
  list.forEach((item, idx) => {
    const value = (item && item.value !== undefined) ? valueStr(item.value) : valueStr(idx);
    const label = (item && item.label !== undefined) ? String(item.label) : String(item);

    const menuItem = document.createElement('div');
    menuItem.className = 'custom-select-item';
    menuItem.dataset.value = value;
    menuItem.textContent = label;

    if (value === selectedValue) {
      menuItem.classList.add('selected');
      selectedLabel = label;
    }

    menuItem.addEventListener('click', () => {
      // Update value
      hidden.value = value;
      trigger.textContent = label;

      // Update selected state
      menu.querySelectorAll('.custom-select-item').forEach(i => i.classList.remove('selected'));
      menuItem.classList.add('selected');

      // Close menu
      closeMenu();

      // Dispatch custom event
      const event = new CustomEvent('cschange', { detail: { value, label } });
      trigger.dispatchEvent(event);
    });

    menu.appendChild(menuItem);
  });

  trigger.textContent = selectedLabel || '请选择';

  // Toggle menu on click
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.contains('open');

    // Close all other menus
    document.querySelectorAll('.custom-select-menu.open').forEach(m => {
      if (m !== menu) {
        m.classList.remove('open');
        // Also remove open class from triggers
        const parentContainer = m.parentElement;
        if (parentContainer) {
          const otherTrigger = parentContainer.querySelector('.custom-select-trigger');
          if (otherTrigger) otherTrigger.classList.remove('open');
        }
      }
    });

    if (isOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  const openMenu = () => {
    menu.classList.add('open');
    trigger.classList.add('open');
  };

  const closeMenu = () => {
    menu.classList.remove('open');
    trigger.classList.remove('open');
  };

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!container.contains(e.target)) {
      closeMenu();
    }
  }, true);

  // Assemble
  container.appendChild(trigger);
  container.appendChild(menu);
  container.appendChild(hidden);

  console.log(`✓ ${id} 下拉框创建完成, 选中: ${selectedLabel}`);
}

function populateModelByRecogn(recognType, opts) {
  let list = [];
  if (recognType === 0) list = opts.whisperModels || [];
  else if (recognType === 2) list = opts.funasrModels || [];
  else if (recognType === 3) list = opts.deepgramModels || [];
  else list = opts.whisperModels || [];

  populateSelect('model-name', list, opts.selected.model_name);
}

function populateSplit(splitMap, selected) {
  const entries = Object.keys(splitMap || {}).map(k => ({ value: k, label: splitMap[k] }));
  populateSelect('split-type', entries, selected);
}

function bindSelect(id, key, mapFn) {
  const el = document.getElementById(id);
  if (!el) return;

  el.addEventListener('cschange', (e) => {
    const value = e.detail.value;
    const val = mapFn ? mapFn(value) : value;
    const payload = {};
    payload[key] = val;
    bridge.setParams(payload);
  });
}

function onRecognChanged() {
  const hidden = document.getElementById('recogn-type__value');
  if (!hidden) return;

  const idx = parseInt(hidden.value, 10);
  bridge.getOptions().then(opts => {
    if (!opts.error) {
      populateModelByRecogn(idx, opts);
    }
  });
}

// ========== Settings Buttons ==========

function bindSettingsButtons() {
  // 翻译设置按钮
  const translateSettingsBtn = document.getElementById('btn-translate-settings');
  if (translateSettingsBtn) {
    translateSettingsBtn.addEventListener('click', async () => {
      const hidden = document.getElementById('translate-type__value');
      if (!hidden) return;

      const translateType = parseInt(hidden.value, 10);
      try {
        const result = await bridge.openTranslateSettings(translateType);
        if (result.success) {
          showNotification('已打开翻译设置', 'success');
        } else {
          showNotification(result.message || '无需配置', 'info');
        }
      } catch (e) {
        showNotification('打开设置失败: ' + e.message, 'error');
      }
    });
  }

  // 配音设置按钮
  const ttsSettingsBtn = document.getElementById('btn-tts-settings');
  if (ttsSettingsBtn) {
    ttsSettingsBtn.addEventListener('click', async () => {
      const hidden = document.getElementById('tts-type__value');
      if (!hidden) return;

      const ttsType = parseInt(hidden.value, 10);
      try {
        const result = await bridge.openTtsSettings(ttsType);
        if (result.success) {
          showNotification('已打开配音设置', 'success');
        } else {
          showNotification(result.message || '无需配置', 'info');
        }
      } catch (e) {
        showNotification('打开设置失败: ' + e.message, 'error');
      }
    });
  }

  // 识别设置按钮
  const recognSettingsBtn = document.getElementById('btn-recogn-settings');
  if (recognSettingsBtn) {
    recognSettingsBtn.addEventListener('click', async () => {
      const hidden = document.getElementById('recogn-type__value');
      if (!hidden) return;

      const recognType = parseInt(hidden.value, 10);
      try {
        const result = await bridge.openRecognSettings(recognType);
        if (result.success) {
          showNotification('已打开识别设置', 'success');
        } else {
          showNotification(result.message || '无需配置', 'info');
        }
      } catch (e) {
        showNotification('打开设置失败: ' + e.message, 'error');
      }
    });
  }

  // 智能摘要配置按钮
  const hearsightConfigBtn = document.getElementById('btn-hearsight-config');
  if (hearsightConfigBtn) {
    hearsightConfigBtn.addEventListener('click', async () => {
      try {
        const result = await bridge.openHearSightConfig();
        if (result.success) {
          showNotification('已打开智能摘要配置', 'success');
        } else {
          showNotification(result.message || '打开配置失败', 'error');
        }
      } catch (e) {
        showNotification('打开配置失败: ' + e.message, 'error');
      }
    });
  }
}

// ========== Notification System ==========

function updateTaskQueue() {
  const emptyDiv = document.getElementById('task-queue-empty');
  const listDiv = document.getElementById('task-queue-list');

  if (selectedVideos.length === 0) {
    emptyDiv.style.display = 'block';
    listDiv.style.display = 'none';
    listDiv.innerHTML = '';
    return;
  }

  emptyDiv.style.display = 'none';
  listDiv.style.display = 'flex';

  // Build task list HTML with progress bar
  listDiv.innerHTML = selectedVideos.map((filePath, index) => {
    const fileName = filePath.split(/[/\\]/).pop();
    const uuid = taskUuidMap[filePath] || null;
    console.log(`Building task item for path "${filePath}", UUID: "${uuid}"`);

    return `
      <div class="task-item" data-index="${index}" data-uuid="${uuid || ''}" data-path="${filePath}">
        <div class="task-item-icon">🎬</div>
        <div class="task-item-content">
          <div class="task-item-name">${fileName}</div>
          <div class="task-item-path">${filePath}</div>
          <div class="task-item-progress-container">
            <div class="task-item-progress-bar">
              <div class="task-item-progress-fill" style="width: 0%"></div>
            </div>
            <div class="task-item-progress-text">0%</div>
          </div>
          <div class="task-item-status-text">等待处理</div>
        </div>
        <div class="task-item-status task-status-pending">等待</div>
        <button class="task-item-remove" onclick="removeTask(${index})" title="移除">×</button>
      </div>
    `;
  }).join('');
}

function startProgressPolling() {
  // Clear existing interval if any
  if (progressPollInterval) {
    clearInterval(progressPollInterval);
  }

  // Poll every 500ms
  progressPollInterval = setInterval(async () => {
    try {
      const progress = await bridge.getTaskProgress();
      updateTaskProgress(progress);
    } catch (e) {
      console.error('Failed to fetch progress:', e);
    }
  }, 500);
}

function stopProgressPolling() {
  if (progressPollInterval) {
    clearInterval(progressPollInterval);
    progressPollInterval = null;
  }
}

function updateTaskProgress(progressData) {
  if (!progressData || typeof progressData !== 'object') {
    console.warn('No progress data received');
    return;
  }

  console.log('Progress data received:', progressData);

  // Update each task's progress
  const taskItems = document.querySelectorAll('.task-item[data-uuid]');
  console.log(`Found ${taskItems.length} task items`);

  taskItems.forEach(taskItem => {
    const uuid = taskItem.dataset.uuid;
    console.log(`Checking task item with UUID: ${uuid}`);

    if (!uuid || !progressData[uuid]) {
      console.log(`No progress data for UUID: ${uuid}`);
      return;
    }

    const progress = progressData[uuid];
    const percent = progress.percent || 0;
    const status = progress.status || 'processing';
    const text = progress.text || '';

    console.log(`Updating task ${uuid}: ${percent}%, status: ${status}, text: ${text}`);

    // Update progress bar
    const progressFill = taskItem.querySelector('.task-item-progress-fill');
    const progressText = taskItem.querySelector('.task-item-progress-text');
    const statusText = taskItem.querySelector('.task-item-status-text');
    const statusBadge = taskItem.querySelector('.task-item-status');

    if (progressFill) {
      progressFill.style.width = `${percent}%`;
    }

    if (progressText) {
      progressText.textContent = `${percent}%`;
    }

    if (statusText) {
      statusText.textContent = text;
    }

    if (statusBadge) {
      // Update status badge
      statusBadge.className = 'task-item-status';
      if (status === 'completed') {
        statusBadge.classList.add('task-status-completed');
        statusBadge.textContent = '✓ 完成';
      } else if (status === 'error') {
        statusBadge.classList.add('task-status-error');
        statusBadge.textContent = '✕ 错误';
      } else if (status === 'stopped') {
        statusBadge.classList.add('task-status-stopped');
        statusBadge.textContent = '⏸ 停止';
      } else {
        statusBadge.classList.add('task-status-processing');
        statusBadge.textContent = '⏳ 处理中';
      }
    }

    // If all tasks are completed, stop polling
    if (percent === 100 && status === 'completed') {
      const allCompleted = Array.from(taskItems).every(item => {
        const itemUuid = item.dataset.uuid;
        if (!itemUuid || !progressData[itemUuid]) return false;
        return progressData[itemUuid].status === 'completed';
      });

      if (allCompleted) {
        stopProgressPolling();
        showNotification('所有任务已完成', 'success');

        // 清除任务队列和 UUID 映射，允许重新添加相同的视频
        setTimeout(() => {
          selectedVideos = [];
          taskUuidMap = {};
          updateTaskQueue();

          // 通知后端重置状态
          if (bridge && bridge.resetStatus) {
            bridge.resetStatus();
          }
        }, 2000); // 2秒后清除，给用户时间查看完成状态
      }
    }
  });
}

function removeTask(index) {
  selectedVideos.splice(index, 1);
  updateTaskQueue();

  // Update video count display
  const count = selectedVideos.length;
  document.getElementById('video-count').innerText = count > 0
    ? `已选择 ${count} 个文件`
    : '未选择视频';

  // Update bridge queue
  if (bridge && bridge.setVideoQueue) {
    bridge.setVideoQueue(selectedVideos);
  }

  showNotification('已移除任务', 'info');
}

// ========== Notification System ==========

function showNotification(message, type = 'info') {
  const container = document.getElementById('notification-container');
  if (!container) {
    const div = document.createElement('div');
    div.id = 'notification-container';
    div.className = 'notification-container';
    document.body.appendChild(div);
    return showNotification(message, type);
  }

  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;

  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  notification.innerHTML = `
    <span class="notification-icon">${icon}</span>
    <span class="notification-message">${message}</span>
  `;

  container.appendChild(notification);

  // Trigger animation
  setTimeout(() => notification.classList.add('show'), 10);

  // Auto remove after 3s
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// ========== HearSight Folder Selection ==========

async function loadHearSightFolders() {
  try {
    if (!bridge || !bridge.getHearSightFolders) {
      console.warn('Bridge or getHearSightFolders not available');
      return;
    }

    const folders = await bridge.getHearSightFolders();
    console.log('获取到文件夹列表:', folders);

    if (!folders || folders.length === 0) {
      console.warn('没有可用的文件夹');
      return;
    }

    // 格式化为下拉选项格式（添加计数显示）
    const options = folders.map(folder => ({
      value: folder.value === null ? '' : folder.value,  // null 转换为空字符串
      label: folder.count > 0 ? `${folder.label} (${folder.count})` : folder.label
    }));

    // 填充下拉框，默认选中第一个（全部视频）
    populateSelect('hearsight-folder', options, '');

    // 绑定变更事件
    bindHearSightFolderChange();

  } catch (e) {
    console.error('加载文件夹列表失败:', e);
    showNotification('加载文件夹列表失败: ' + e.message, 'error');
  }
}

function bindHearSightFolderChange() {
  const el = document.getElementById('hearsight-folder');
  if (!el) {
    console.warn('找不到 hearsight-folder 元素');
    return;
  }

  el.addEventListener('cschange', (e) => {
    const folderId = e.detail.value || '';
    console.log('选择文件夹:', folderId || '全部视频');

    if (bridge && bridge.setHearSightFolder) {
      bridge.setHearSightFolder(folderId);
    }
  });
}
