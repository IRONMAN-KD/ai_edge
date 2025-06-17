<template>
  <div class="alert-detail-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.back()" text>
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>告警详情</h2>
      </div>
      <div class="header-right">
        <el-button
          v-if="alertDetail.status === 'pending'"
          type="success"
          @click="processAlert"
        >
          开始处理
        </el-button>
        <el-button
          v-if="alertDetail.status === 'processing'"
          type="primary"
          @click="resolveAlert"
        >
          标记解决
        </el-button>
      </div>
    </div>
    
    <div v-loading="loading" class="detail-content">
      <div class="detail-grid">
        <!-- 基本信息 -->
        <div class="detail-card">
          <div class="card-header">
            <h3>基本信息</h3>
          </div>
          <div class="card-content">
            <div class="info-row">
              <span class="label">告警标题:</span>
              <span class="value">{{ alertDetail.title }}</span>
            </div>
            <div class="info-row">
              <span class="label">告警级别:</span>
              <span class="value">
                <el-tag :type="getLevelType(alertDetail.level)">
                  {{ getLevelText(alertDetail.level) }}
                </el-tag>
              </span>
            </div>
            <div class="info-row">
              <span class="label">处理状态:</span>
              <span class="value">
                <el-tag :type="getStatusType(alertDetail.status)">
                  {{ getStatusText(alertDetail.status) }}
                </el-tag>
              </span>
            </div>
            <div class="info-row">
              <span class="label">置信度:</span>
              <span class="value">
                <el-progress
                  :percentage="alertDetail.confidence"
                  :color="getConfidenceColor(alertDetail.confidence)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="confidence-text">{{ alertDetail.confidence }}%</span>
              </span>
            </div>
            <div class="info-row">
              <span class="label">告警时间:</span>
              <span class="value">{{ formatTime(alertDetail.created_at) }}</span>
            </div>
            <div class="info-row">
              <span class="label">更新时间:</span>
              <span class="value">{{ formatTime(alertDetail.updated_at) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 任务信息 -->
        <div class="detail-card">
          <div class="card-header">
            <h3>关联任务</h3>
          </div>
          <div class="card-content">
            <div class="info-row">
              <span class="label">任务名称:</span>
              <span class="value">{{ alertDetail.task_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">使用模型:</span>
              <span class="value">{{ alertDetail.model_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">视频源:</span>
              <span class="value">{{ alertDetail.video_source }}</span>
            </div>
            <div class="info-row">
              <span class="label">检测区域:</span>
              <span class="value">{{ alertDetail.detection_area || '全画面' }}</span>
            </div>
          </div>
        </div>
        
        <!-- 告警描述 -->
        <div class="detail-card full-width">
          <div class="card-header">
            <h3>告警描述</h3>
          </div>
          <div class="card-content">
            <p class="description">{{ alertDetail.description }}</p>
          </div>
        </div>
        
        <!-- 告警图片 -->
        <div v-if="alertDetail.alert_image" class="detail-card full-width">
          <div class="card-header">
            <h3>告警图片</h3>
          </div>
          <div class="card-content">
            <div class="image-container">
              <img :src="`http://localhost:5001/${alertDetail.alert_image}`" alt="告警图片" class="alert-image" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getAlert, updateAlert } from '@/api/alerts'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

// 响应式数据
const alertDetail = ref({})
const loading = ref(false)
const processing = ref(false)
const showProcessDialog = ref(false)

// 处理表单
const processForm = reactive({
  status: '',
  remark: ''
})

// 获取告警详情
const loadAlertDetail = async () => {
  try {
    loading.value = true
    const response = await getAlert(route.params.id)
    alertDetail.value = response
  } catch (error) {
    console.error('加载告警详情失败:', error)
    ElMessage.error('加载告警详情失败')
  } finally {
    loading.value = false
  }
}

// 开始处理告警
const processAlert = () => {
  processForm.status = 'processing'
  processForm.remark = ''
  showProcessDialog.value = true
}

// 标记解决
const resolveAlert = () => {
  processForm.status = 'resolved'
  processForm.remark = ''
  showProcessDialog.value = true
}

// 确认处理
const confirmProcess = async () => {
  if (!processForm.remark.trim()) {
    ElMessage.warning('请输入处理备注')
    return
  }
  
  try {
    processing.value = true
    
    await updateAlert(alertDetail.value.id, {
      status: processForm.status,
      remark: processForm.remark
    })
    
    ElMessage.success('处理成功')
    showProcessDialog.value = false
    loadAlertDetail()
  } catch (error) {
    console.error('处理失败:', error)
    ElMessage.error('处理失败')
  } finally {
    processing.value = false
  }
}

// 工具函数
const getLevelType = (level) => {
  const typeMap = {
    high: 'danger',
    medium: 'warning',
    low: 'success'
  }
  return typeMap[level] || 'info'
}

const getLevelText = (level) => {
  const levelMap = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return levelMap[level] || level
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    processing: 'primary',
    resolved: 'success'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决'
  }
  return statusMap[status] || status
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 80) return '#67c23a'
  if (confidence >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getLogType = (action) => {
  const typeMap = {
    create: 'info',
    process: 'primary',
    resolve: 'success'
  }
  return typeMap[action] || 'info'
}

const getLogActionText = (action) => {
  const actionMap = {
    create: '创建',
    process: '处理',
    resolve: '解决'
  }
  return actionMap[action] || action
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  loadAlertDetail()
})
</script>

<style scoped lang="scss">
.alert-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--text-color);
    }
  }
  
  .header-right {
    display: flex;
    gap: 12px;
  }
}

.detail-content {
  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    
    .full-width {
      grid-column: 1 / -1;
    }
  }
}

.detail-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  
  .card-header {
    background: var(--bg-color);
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-color);
    }
  }
  
  .card-content {
    padding: 20px;
  }
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  .label {
    width: 100px;
    font-weight: 600;
    color: var(--text-color-secondary);
    flex-shrink: 0;
  }
  
  .value {
    flex: 1;
    color: var(--text-color);
    display: flex;
    align-items: center;
    gap: 8px;
    
    .confidence-text {
      font-size: 12px;
      color: var(--text-color-secondary);
      min-width: 30px;
    }
  }
}

.description {
  margin: 0;
  line-height: 1.6;
  color: var(--text-color);
}

.image-container {
  text-align: center;
  
  .alert-image {
    max-width: 100%;
    max-height: 400px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}

.logs-list {
  .log-item {
    border-bottom: 1px solid var(--border-color);
    padding: 16px 0;
    
    &:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    
    .log-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .log-time {
        font-size: 12px;
        color: var(--text-color-secondary);
      }
    }
    
    .log-content {
      .log-remark {
        margin: 0 0 4px;
        color: var(--text-color);
        line-height: 1.5;
      }
      
      .log-operator {
        margin: 0;
        font-size: 12px;
        color: var(--text-color-secondary);
      }
    }
  }
}

.empty-logs {
  padding: 40px 0;
}

// 响应式
@media (max-width: 768px) {
  .alert-detail-container {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    
    .label {
      width: auto;
    }
  }
}
</style> 