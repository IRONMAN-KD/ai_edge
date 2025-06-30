<template>
  <div class="alert-detail-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.back()" :icon="ArrowLeft" text>
          返回
        </el-button>
        <div class="divider"></div>
        <h2>{{ alertDetail.title || '告警详情' }}</h2>
      </div>
      <div class="header-right">
        <el-button
          v-if="alertDetail.status === 'pending'"
          type="primary"
          @click="processAlert"
          :icon="VideoPlay"
        >
          开始处理
        </el-button>
        <el-button
          v-if="alertDetail.status === 'processing'"
          type="success"
          @click="resolveAlert"
          :icon="CircleCheck"
        >
          标记为已解决
        </el-button>
      </div>
    </div>
    
    <el-row :gutter="24" v-loading="loading">
      <!-- Left Column: Image and Description -->
      <el-col :span="14">
        <el-card class="box-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>告警快照</span>
            </div>
          </template>
          <div class="image-container">
                    <el-image
          v-if="alertDetail.alert_image"
          :src="`/alert_images/${alertDetail.alert_image.replace(/^.*\//, '')}`"
          class="alert-image"
          fit="contain"
          :preview-src-list="[`/alert_images/${alertDetail.alert_image.replace(/^.*\//, '')}`]"
              hide-on-click-modal
              preview-teleported
            />
            <el-empty v-else description="暂无告警图片" />
          </div>
        </el-card>

        <el-card class="box-card" shadow="never" style="margin-top: 24px;">
           <template #header>
            <div class="card-header">
              <span>告警描述</span>
            </div>
          </template>
          <p class="description">{{ alertDetail.description }}</p>
        </el-card>
      </el-col>

      <!-- Right Column: Metadata -->
      <el-col :span="10">
        <el-card class="box-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>告警元数据</span>
            </div>
          </template>
          <div class="metadata-content">
            <div class="info-row">
              <span class="label">处理状态</span>
              <span class="value">
                <el-tag :type="getStatusType(alertDetail.status)" size="small">
                  {{ getStatusText(alertDetail.status) }}
                </el-tag>
              </span>
            </div>
            <div class="info-row">
              <span class="label">告警级别</span>
              <span class="value">
                <el-tag :type="getLevelType(alertDetail.level)" size="small">
                  {{ getLevelText(alertDetail.level) }}
                </el-tag>
              </span>
            </div>
            <div class="info-row">
              <span class="label">置信度</span>
              <span class="value">
                <el-progress
                  :percentage="parseFloat(((alertDetail.confidence || 0) * 100).toFixed(2))"
                  :color="getConfidenceColor((alertDetail.confidence || 0) * 100)"
                  :stroke-width="6"
                  :show-text="false"
                  style="width: 100px"
                />
                <span class="confidence-text">{{ ((alertDetail.confidence || 0) * 100).toFixed(2) }}%</span>
              </span>
            </div>
            <el-divider />
            <div class="info-row">
              <span class="label">关联任务</span>
              <span class="value">{{ alertDetail.task_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">使用模型</span>
              <span class="value">{{ alertDetail.model_name }}</span>
            </div>
             <el-divider />
            <div class="info-row">
              <span class="label">告警时间</span>
              <span class="value">{{ formatTime(alertDetail.created_at) }}</span>
            </div>
             <div class="info-row">
              <span class="label">更新时间</span>
              <span class="value">{{ formatTime(alertDetail.updated_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay, CircleCheck } from '@element-plus/icons-vue'
import { getAlert, updateAlert } from '@/api/alerts'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

// 响应式数据
const alertDetail = ref({})
const loading = ref(false)

// 获取告警详情
const loadAlertDetail = async () => {
  try {
    loading.value = true
    alertDetail.value = await getAlert(route.params.id)
  } catch (error) {
    console.error('加载告警详情失败:', error)
    ElMessage.error('加载告警详情失败')
  } finally {
    loading.value = false
  }
}

const updateStatus = async (status, remark) => {
  try {
    await updateAlert(alertDetail.value.id, { status, remark });
    ElMessage.success('状态更新成功');
    loadAlertDetail();
  } catch (error) {
    console.error('更新失败:', error);
    ElMessage.error('状态更新失败');
  }
}

// 开始处理告警
const processAlert = () => {
  updateStatus('processing', '用户开始处理此告警');
}

// 标记解决
const resolveAlert = () => {
  updateStatus('resolved', '用户标记此告警为已解决');
}

// 工具函数
const getLevelType = (level) => ({ high: 'danger', medium: 'warning', low: 'success' }[level] || 'info');
const getLevelText = (level) => ({ high: '高', medium: '中', low: '低' }[level] || level);
const getStatusType = (status) => ({ pending: 'warning', processing: 'primary', resolved: 'success' }[status] || 'info');
const getStatusText = (status) => ({ pending: '待处理', processing: '处理中', resolved: '已解决' }[status] || status);
const getConfidenceColor = (confidence) => {
  if (confidence >= 80) return '#67c23a';
  if (confidence >= 60) return '#e6a23c';
  return '#f56c6c';
}
const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : 'N/A';

onMounted(() => {
  loadAlertDetail()
})
</script>

<style scoped lang="scss">
.alert-detail-container {
  padding: 24px;
  background-color: #f7f8fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background-color: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .divider {
      width: 1px;
      height: 24px;
      background-color: #dcdfe6;
    }
    
    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }
}

.box-card {
  border: none;
}

:deep(.el-card__header) {
  background-color: #fafafa;
  font-weight: 500;
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  
  .alert-image {
    max-width: 100%;
    max-height: 500px;
    border-radius: 4px;
  }
}

.description {
  margin: 0;
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
}

.metadata-content {
  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    margin-bottom: 20px;

    &:last-child {
      margin-bottom: 0;
    }

    .label {
      color: #606266;
    }
    
    .value {
      color: #303133;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      
      .confidence-text {
        font-size: 13px;
        min-width: 45px;
      }
    }
  }
}
</style> 