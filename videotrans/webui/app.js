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
    console.log('下拉选项填充完成');

    // Bind select events AFTER they are created
    bindSelectEvents();
    console.log('绑定下拉事件完成');

    // Set text input values
    const voiceRoleEl = document.getElementById('voice-role');
    const voiceRateEl = document.getElementById('voice-rate');
    const volumeEl = document.getElementById('volume');
    const pitchEl = document.getElementById('pitch');

    if (voiceRoleEl) voiceRoleEl.value = opts.selected.voice_role || '';
    if (voiceRateEl) voiceRateEl.value = opts.selected.voice_rate || 0;
    if (volumeEl) volumeEl.value = opts.selected.volume || 0;
    if (pitchEl) pitchEl.value = opts.selected.pitch || 0;

    // Set checkbox values
    const checkboxes = [
      { id: 'voice-autorate', key: 'voice_autorate' },
      { id: 'video-autorate', key: 'video_autorate' },
      { id: 'enable-cuda', key: 'enable_cuda' },
      { id: 'enable-hearsight', key: 'enable_hearsight' },
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
    const files = await bridge.selectVideo();
    selectedVideos = files || [];
    updateTaskQueue();
    const count = selectedVideos.length;
    document.getElementById('video-count').innerText = count > 0
      ? `已选择 ${count} 个文件`
      : '未选择视频';
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

  document.getElementById('proxy').addEventListener('change', (e) => {
    bridge.setParams({ proxy: e.target.value || '' });
  });

  document.getElementById('btn-start').addEventListener('click', async () => {
    const btn = document.getElementById('btn-start');
    btn.disabled = true;
    btn.textContent = '处理中...';
    try {
      const result = await bridge.startTranslate();
      if (result && result.success) {
        // Update taskUuidMap with returned UUIDs
        if (result.task_uuids && Array.isArray(result.task_uuids)) {
          result.task_uuids.forEach(item => {
            taskUuidMap[item.path] = item.uuid;
          });
          console.log('Task UUIDs updated:', taskUuidMap);

          // Rebuild task queue with UUIDs
          updateTaskQueue();
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
  const voiceRole = document.getElementById('voice-role');
  const voiceRate = document.getElementById('voice-rate');
  const volume = document.getElementById('volume');
  const pitch = document.getElementById('pitch');

  if (voiceRole) {
    voiceRole.addEventListener('change', (e) => {
      bridge.setParams({ voice_role: e.target.value });
    });
  }

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

  // Bind checkboxes
  const checkboxIds = ['voice-autorate', 'video-autorate', 'enable-cuda', 'enable-hearsight', 'aisendsrt', 'remove-noise'];
  const checkboxKeys = {
    'voice-autorate': 'voice_autorate',
    'video-autorate': 'video_autorate',
    'enable-cuda': 'cuda',
    'enable-hearsight': 'enable_hearsight',
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
