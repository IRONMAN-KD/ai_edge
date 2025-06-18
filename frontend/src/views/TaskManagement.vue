<template>
  <div class="task-management">
    <div class="page-header">
      <h1>任务管理</h1>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        创建新任务
      </el-button>
    </div>

    <!-- 任务卡片列表 -->
    <div v-if="tasks.length > 0" class="task-card-grid" v-loading="loading">
      <el-card v-for="task in tasks" :key="task.id" class="task-card">
        <template #header>
          <div class="card-header">
            <span class="task-name-card">{{ task.name }}</span>
            <el-tag :type="getStatusType(task.status)" size="small">{{ getStatusText(task.status) }}</el-tag>
          </div>
        </template>
        <div class="card-body">
          <div class="info-item">
            <el-icon><Menu /></el-icon>
            <span><strong>模型:</strong> {{ task.model_name || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <el-icon><VideoCamera /></el-icon>
            <span><strong>视频源:</strong></span>
            <div class="source-tags">
              <el-tag v-for="source in task.video_sources" :key="source.url" size="small" class="source-tag-card">{{ source.url }}</el-tag>
            </div>
          </div>
          <div class="info-item">
            <el-icon><Timer /></el-icon>
            <span><strong>创建于:</strong> {{ formatDate(task.create_time) }}</span>
          </div>
        </div>
        <div class="card-footer">
          <el-switch
            v-model="task.is_enabled"
            :active-value="true"
            :inactive-value="false"
            @change="handleStatusChange(task)"
            style="margin-right: 15px;"
          />
          <el-button-group>
            <el-button size="small" :icon="View" @click="viewTask(task)" title="查看详情" />
            <el-button size="small" :icon="Edit" @click="openEditDialog(task)" title="编辑任务" />
            <el-button size="small" :icon="Monitor" @click="openPreview(task)" title="实时预览" />
            <el-button size="small" :icon="Delete" @click="deleteTask(task)" title="删除任务" />
          </el-button-group>
        </div>
      </el-card>
    </div>
    <el-empty v-else-if="!loading" description="暂无任务，快去创建一个吧！" />

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchTasks"
        @current-change="fetchTasks"
      />
    </div>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog v-model="showEditDialog" :title="isEditMode ? '编辑任务' : '创建新任务'" width="700px" :close-on-click-modal="false" @close="resetTaskForm">
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="100px" class="task-form">
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="为您的任务起个名字">
            <template #prepend><el-icon><Tickets /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item label="任务描述" prop="description">
          <el-input v-model="taskForm.description" type="textarea" :rows="3" placeholder="简要描述任务内容" />
        </el-form-item>
        <el-form-item label="选择模型" prop="model_id">
          <el-select v-model="taskForm.model_id" placeholder="请选择一个已启用的模型" style="width: 100%">
            <template #prefix><el-icon><Menu /></el-icon></template>
            <el-option v-for="model in availableModels" :key="model.id" :label="model.name" :value="model.id">
              <div class="model-option">
                <span>{{ model.name }} (v{{ model.version }})</span>
                <el-tag :type="model.status === 'active' ? 'success' : 'info'" size="small">
                  {{ model.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-divider content-position="left">数据源配置</el-divider>
        <el-form-item label="视频源" prop="video_sources">
           <div v-for="(source, index) in taskForm.video_sources" :key="index" class="source-item">
            <div class="source-input-group">
              <el-input v-model="source.name" placeholder="视频名称 (例如：前门摄像头)" class="source-name-input">
                <template #prepend><el-icon><InfoFilled /></el-icon></template>
              </el-input>
              <el-input v-model="source.url" placeholder="请输入视频源地址 (e.g., /dev/video0, rtsp://...)" class="source-url-input">
                 <template #prepend><el-icon><VideoCamera /></el-icon></template>
                <template #append>
                  <el-button-group>
                    <el-button :icon="Crop" @click="openRoiSelector(index)" title="配置检测区域" />
                    <el-button :icon="Delete" @click.prevent="removeVideoSource(index)" title="删除视频源" />
                  </el-button-group>
                </template>
              </el-input>
            </div>
            <div v-if="source.roi" class="roi-display">
              <el-tag size="small" closable @close="clearRoi(index)">
                ROI: x:{{source.roi.x}}, y:{{source.roi.y}}, w:{{source.roi.w}}, h:{{source.roi.h}}
              </el-tag>
            </div>
           </div>
           <el-button @click.prevent="addVideoSource" :icon="Plus" style="width: 100%;" class="add-source-btn">
             添加视频源
           </el-button>
        </el-form-item>
        
        <el-divider content-position="left">告警配置</el-divider>
        <el-form-item label="置信度阈值" prop="confidence_threshold">
          <el-slider v-model="taskForm.confidence_threshold" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="告警冷却(秒)" prop="alert_debounce_interval">
          <el-input-number v-model="taskForm.alert_debounce_interval" :min="0" placeholder="单位：秒" />
        </el-form-item>
        <el-form-item label="推理频率(秒)" prop="inference_interval">
          <el-input-number v-model="taskForm.inference_interval" :min="0.1" :step="0.1" placeholder="每次推理的间隔时间" />
        </el-form-item>
        <el-form-item label="告警消息" prop="alert_message">
          <el-input v-model="taskForm.alert_message" type="textarea" :rows="3" placeholder="配置告警消息模板" />
          <div class="template-hint">
            可用占位符: {video_name} 标识摄像头名称
          </div>
        </el-form-item>

        <el-divider content-position="left">调度配置</el-divider>
        <el-form-item label="任务启用" prop="is_enabled">
          <el-switch v-model="taskForm.is_enabled" />
        </el-form-item>
        <el-form-item label="调度类型" prop="schedule_type">
          <el-select v-model="taskForm.schedule_type" placeholder="请选择调度类型" style="width: 100%">
            <el-option label="持续运行" value="continuous"></el-option>
            <el-option label="每天" value="daily"></el-option>
            <el-option label="每周" value="weekly"></el-option>
            <el-option label="每月" value="monthly"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="taskForm.schedule_type === 'weekly'" label="执行日" prop="schedule_days">
          <el-checkbox-group v-model="taskForm.schedule_days">
            <el-checkbox label="1">周一</el-checkbox>
            <el-checkbox label="2">周二</el-checkbox>
            <el-checkbox label="3">周三</el-checkbox>
            <el-checkbox label="4">周四</el-checkbox>
            <el-checkbox label="5">周五</el-checkbox>
            <el-checkbox label="6">周六</el-checkbox>
            <el-checkbox label="7">周日</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item v-if="taskForm.schedule_type === 'monthly'" label="执行日" prop="schedule_days">
          <el-select v-model="taskForm.schedule_days" multiple placeholder="请选择每月的执行日期" style="width: 100%">
            <el-option v-for="day in 31" :key="day" :label="`${day}日`" :value="String(day)" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="taskForm.schedule_type !== 'continuous'" label="执行时段" prop="time_range">
           <el-time-picker
              v-model="timeRange"
              is-range
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              style="width: 100%"
            />
        </el-form-item>

      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveTask" :loading="saving">
            {{ isEditMode ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="任务详情" width="700px">
      <div v-if="selectedTask" class="task-detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ selectedTask.id }}</el-descriptions-item>
          <el-descriptions-item label="任务状态">
            <el-tag :type="getStatusType(selectedTask.status)">{{ getStatusText(selectedTask.status) }}</el-tag>
            <el-tag v-if="selectedTask.is_enabled === false" type="info" style="margin-left: 8px;">已禁用</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="任务名称">{{ selectedTask.name }}</el-descriptions-item>
          <el-descriptions-item label="使用模型">{{ selectedTask.model_name }} (ID: {{ selectedTask.model_id }})</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedTask.create_time) }}</el-descriptions-item>
          <el-descriptions-item label="最后更新">{{ formatDate(selectedTask.update_time) }}</el-descriptions-item>
          <el-descriptions-item label="任务描述" :span="2">{{ selectedTask.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="视频源" :span="2">
            <div v-if="selectedTask.video_sources && selectedTask.video_sources.length">
              <el-tag v-for="(source, index) in selectedTask.video_sources" :key="index" class="source-tag">
                {{ source.url }}
              </el-tag>
            </div>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="调度计划" :span="2">
            <div>{{ getScheduleText(selectedTask) }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 视频预览对话框 -->
    <el-dialog v-model="showPreviewDialog" :title="`任务预览: ${selectedTask?.name}`" width="80vw" @close="selectedTask = null" destroy-on-close>
      <VideoPreview 
        v-if="showPreviewDialog && selectedTask" 
        :task-id="selectedTask.id" 
        :stream-url="`/api/tasks/${selectedTask.id}/stream`" 
      />
    </el-dialog>

    <!-- ROI选择器对话框 -->
    <el-dialog v-model="showRoiDialog" title="配置检测区域 (ROI)" width="60vw" append-to-body destroy-on-close>
        <div v-loading="roiImageLoading" style="min-height: 200px;">
          <RegionSelector
            v-if="!roiImageLoading && currentRoiImageUrl && currentEditingSource"
            :image-url="currentRoiImageUrl"
            :initial-roi="currentEditingSource.roi"
            @update:roi="updateRoi"
          />
          <el-empty v-else-if="!roiImageLoading && !currentRoiImageUrl" description="无法加载视频帧" />
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showRoiDialog = false">取消</el-button>
            <el-button type="primary" @click="confirmRoi">确认</el-button>
          </span>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Delete, Monitor, Edit, Menu, VideoCamera, Timer, Tickets, Crop, InfoFilled } from '@element-plus/icons-vue'
import { getTasks, createTask as apiCreateTask, updateTask as apiUpdateTask, deleteTask as apiDeleteTask, startTask as apiStartTask, stopTask as apiStopTask, getTaskFrame } from '@/api/tasks'
import { getModels } from '@/api/models'
import { formatDate } from '@/utils/formatters'
import VideoPreview from '@/components/VideoPreview.vue'
import RegionSelector from '@/components/RegionSelector.vue'

// 响应式数据
const loading = ref(true)
const tasks = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 创建/编辑任务相关
const showEditDialog = ref(false)
const isEditMode = ref(false)
const saving = ref(false)
const taskFormRef = ref()
const availableModels = ref([])
const taskForm = reactive({
  id: null,
  name: '',
  description: '',
  model_id: null,
  video_sources: [{ url: '', name: '', roi: null }],
  is_enabled: true,
  schedule_type: 'continuous',
  schedule_days: [],
  start_time: '00:00:00',
  end_time: '23:59:59',
  confidence_threshold: 0.8,
  alert_debounce_interval: 60,
  inference_interval: 1.0,
  alert_message: "在任务'{task_name}'中，于{time}检测到{class_name}，置信度为{confidence:.2f}%。",
})

// 详情相关
const showDetailDialog = ref(false)
const selectedTask = ref(null)

const showPreviewDialog = ref(false)

// ROI
const showRoiDialog = ref(false);
const currentEditingSourceIndex = ref(null);
const roiImageLoading = ref(false);
const currentRoiImageUrl = ref('');

const currentEditingSource = computed(() => {
  if (currentEditingSourceIndex.value !== null) {
    return taskForm.video_sources[currentEditingSourceIndex.value];
  }
  return null;
});

const timeRange = computed({
  get() {
    if (taskForm.start_time && taskForm.end_time) {
      const startDate = new Date();
      const [startH, startM, startS] = taskForm.start_time.split(':');
      startDate.setHours(startH, startM, startS);

      const endDate = new Date();
      const [endH, endM, endS] = taskForm.end_time.split(':');
      endDate.setHours(endH, endM, endS);
      
      return [startDate, endDate];
    }
    return [new Date(2024, 1, 1, 0, 0, 0), new Date(2024, 1, 1, 23, 59, 59)];
  },
  set(newVal) {
    if (newVal && newVal.length === 2) {
      taskForm.start_time = `${String(newVal[0].getHours()).padStart(2, '0')}:${String(newVal[0].getMinutes()).padStart(2, '0')}:${String(newVal[0].getSeconds()).padStart(2, '0')}`;
      taskForm.end_time = `${String(newVal[1].getHours()).padStart(2, '0')}:${String(newVal[1].getMinutes()).padStart(2, '0')}:${String(newVal[1].getSeconds()).padStart(2, '0')}`;
    } else {
      taskForm.start_time = '00:00:00';
      taskForm.end_time = '23:59:59';
    }
  }
});

// 表单验证规则
const taskRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' }
  ],
  model_id: [
    { required: true, message: '请选择一个模型', trigger: 'change' }
  ],
  video_sources: [
    { required: true, message: '请至少提供一个视频源' },
    { 
      validator: (rule, value, callback) => {
        if (!value || value.length === 0 || value.some(s => !s)) {
          callback(new Error('所有视频源地址均不能为空'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await getTasks({
      page: currentPage.value,
      page_size: pageSize.value
    })
    tasks.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 获取可用模型列表
const fetchAvailableModels = async () => {
  try {
    const response = await getModels({
      page: 1,
      page_size: 1000, // 获取所有启用的模型
      status: 'active'
    })
    availableModels.value = response.items
  } catch (error) {
    console.error('获取可用模型列表失败:', error)
  }
}

// 打开创建任务对话框
const openCreateDialog = () => {
  isEditMode.value = false
  resetTaskForm()
  fetchAvailableModels()
  showEditDialog.value = true
}

// 打开编辑任务对话框
const openEditDialog = (task) => {
  isEditMode.value = true
  resetTaskForm()
  fetchAvailableModels()
  // Deep copy task data to form
  taskForm.id = task.id
  taskForm.name = task.name
  taskForm.description = task.description
  taskForm.model_id = task.model_id
  
  // scheduling and alerting fields
  taskForm.is_enabled = task.is_enabled ?? true;
  taskForm.schedule_type = task.schedule_type || 'continuous';
  taskForm.schedule_days = task.schedule_days || [];
  taskForm.start_time = task.start_time || '00:00:00';
  taskForm.end_time = task.end_time || '23:59:59';
  taskForm.confidence_threshold = task.confidence_threshold ?? 0.8;
  taskForm.alert_debounce_interval = task.alert_debounce_interval ?? 60;
  taskForm.inference_interval = task.inference_interval ?? 1.0;
  taskForm.alert_message = task.alert_message || "在任务'{task_name}'中，于{time}检测到{class_name}，置信度为{confidence:.2f}%。";

  if (Array.isArray(task.video_sources) && task.video_sources.length > 0) {
      taskForm.video_sources = task.video_sources.map(s => 
          typeof s === 'string' 
              ? { url: s, name: '', roi: null } 
              : { url: s.url, name: s.name || '', roi: s.roi || null }
      );
  } else {
      taskForm.video_sources = [{ url: '', name: '', roi: null }];
  }
  
  if (taskForm.video_sources.length === 0) {
    taskForm.video_sources.push({ url: '', name: '', roi: null })
  }
  showEditDialog.value = true
}

// 重置任务表单
const resetTaskForm = () => {
  taskForm.id = null
  taskForm.name = ''
  taskForm.description = ''
  taskForm.model_id = null
  taskForm.video_sources = [{ url: '', name: '', roi: null }]
  
  // Reset scheduling and alerting fields
  taskForm.is_enabled = true;
  taskForm.schedule_type = 'continuous';
  taskForm.schedule_days = [];
  taskForm.start_time = '00:00:00';
  taskForm.end_time = '23:59:59';
  taskForm.confidence_threshold = 0.8;
  taskForm.alert_debounce_interval = 60;
  taskForm.inference_interval = 1.0;
  taskForm.alert_message = "在任务'{task_name}'中，于{time}检测到{class_name}，置信度为{confidence:.2f}%。";

  if (taskFormRef.value) {
    taskFormRef.value.clearValidate()
  }
}

// 创建或更新任务
const saveTask = () => {
  taskFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      // Create a payload without the 'id' field, which is not expected by the backend for create/update operations.
      const payload = { ...taskForm }
      delete payload.id

      try {
        if (isEditMode.value) {
          await apiUpdateTask(taskForm.id, payload)
          ElMessage.success('任务更新成功')
        } else {
          await apiCreateTask(payload)
          ElMessage.success('任务创建成功')
        }
        showEditDialog.value = false
        fetchTasks()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        saving.value = false
      }
    }
  })
}

// 查看任务详情
const viewTask = (task) => {
  selectedTask.value = task
  showDetailDialog.value = true
}

// 启动任务
const startTask = (task) => {
  ElMessageBox.confirm(`确定要启动任务 "${task.name}" 吗？`, '确认', { type: 'info' })
    .then(async () => {
      try {
        await apiStartTask(task.id)
        ElMessage.success('任务已启动')
        fetchTasks()
      } catch (error) {
        ElMessage.error('启动任务失败')
      }
    }).catch(() => {})
}

// 停止任务
const stopTask = (task) => {
  ElMessageBox.confirm(`确定要停止任务 "${task.name}" 吗？`, '确认', { type: 'warning' })
    .then(async () => {
      try {
        await apiStopTask(task.id)
        ElMessage.success('任务已停止')
        fetchTasks()
      } catch (error) {
        ElMessage.error('停止任务失败')
      }
    }).catch(() => {})
}

// 删除任务
const deleteTask = (task) => {
  ElMessageBox.confirm(`此操作将永久删除任务 "${task.name}"，是否继续？`, '警告', { type: 'error', confirmButtonText: '确定删除' })
    .then(async () => {
      try {
        await apiDeleteTask(task.id)
        ElMessage.success('任务删除成功')
        fetchTasks()
      } catch (error) {
        ElMessage.error('删除任务失败')
      }
    }).catch(() => {})
}

// 工具函数
const getStatusType = (status) => {
  const types = {
    'stopped': 'info',
    'running': 'success',
    'error': 'danger',
    'disabled': 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'stopped': '已停止',
    'running': '运行中',
    'error': '错误',
    'disabled': '已禁用'
  }
  return texts[status] || status
}

const getScheduleText = (task) => {
  if (!task.is_enabled) {
    return '任务已禁用';
  }
  switch (task.schedule_type) {
    case 'continuous':
      return '持续运行';
    case 'daily':
      return `每天 ${task.start_time} - ${task.end_time}`;
    case 'weekly': {
      const weekDays = { '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六', '7': '周日' };
      const days = (task.schedule_days || []).map(d => weekDays[d]).join(', ');
      if (!days) return `每周 ${task.start_time} - ${task.end_time}`;
      return `每周 (${days}) ${task.start_time} - ${task.end_time}`;
    }
    case 'monthly': {
      const days = (task.schedule_days || []).join(', ');
      if (!days) return `每月 ${task.start_time} - ${task.end_time}`;
      return `每月 (${days}日) ${task.start_time} - ${task.end_time}`;
    }
    default:
      return '未配置';
  }
};

const handleStatusChange = async (task) => {
  const newStatus = task.status;
  const actionText = newStatus === 'running' ? '启动' : '停止';
  try {
    if (newStatus === 'running') {
      await apiStartTask(task.id);
    } else {
      await apiStopTask(task.id);
    }
    ElMessage.success(`任务已${actionText}`);
    await fetchTasks();
  } catch (error) {
    ElMessage.error(`${actionText}任务失败`);
    // Revert status on failure
    task.status = newStatus === 'running' ? 'stopped' : 'running';
  }
}

const addVideoSource = () => {
  taskForm.video_sources.push({ url: '', name: '', roi: null })
}

const removeVideoSource = (index) => {
  if (taskForm.video_sources.length > 1) {
    taskForm.video_sources.splice(index, 1)
  }
}

const openRoiSelector = async (index) => {
  currentEditingSourceIndex.value = index;
  const sourceUrl = taskForm.video_sources[index]?.url;
  if (!sourceUrl) {
    ElMessage.warning('请输入视频源地址');
    return;
  }
  
  roiImageLoading.value = true;
  showRoiDialog.value = true;
  currentRoiImageUrl.value = ''; // Reset previous image

  try {
    const response = await getTaskFrame(sourceUrl);
    // The backend is expected to return a base64 encoded image string
    currentRoiImageUrl.value = response.frame;
  } catch (error) {
    console.error("Failed to get task frame:", error);
    ElMessage.error(error.response?.data?.detail || '加载视频帧失败');
    currentRoiImageUrl.value = ''; // Ensure no broken image is shown
  } finally {
    roiImageLoading.value = false;
  }
};

const updateRoi = (newRoi) => {
  if (currentEditingSource.value) {
    currentEditingSource.value.roi = newRoi;
  }
};

const clearRoi = (index) => {
  if(taskForm.video_sources[index]) {
    taskForm.video_sources[index].roi = null;
  }
};

const confirmRoi = () => {
  showRoiDialog.value = false;
  currentEditingSourceIndex.value = null;
};

const openPreview = (task) => {
  selectedTask.value = task
  showPreviewDialog.value = true
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
  fetchAvailableModels()
})
</script>

<style scoped>
.task-management {
  padding: 24px;
  background-color: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.task-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.task-card {
  border-radius: 8px;
  transition: box-shadow 0.3s;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-name-card {
  font-weight: bold;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.card-body {
  font-size: 14px;
  color: #606266;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.info-item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-left: 5px;
}

.source-tag-card {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.source-item {
  margin-bottom: 10px;
}

.source-item:last-child {
  margin-bottom: 0;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.task-detail-content {
  padding: 16px;
}

.task-form .el-divider {
  margin: 10px 0 25px 0;
}

.add-source-btn {
  border-style: dashed;
}

.template-hint {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 5px;
}

.roi-display {
  margin-top: 5px;
}

.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.el-checkbox {
  margin-right: 15px;
}

.source-input-group {
  display: flex;
  gap: 10px;
  width: 100%;
}

.source-name-input {
  width: 200px;
  flex-shrink: 0;
}

.source-url-input {
  flex-grow: 1;
}
</style> 