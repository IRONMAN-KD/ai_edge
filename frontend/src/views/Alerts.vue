<template>
  <div class="alerts-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>告警管理</h2>
        <p>查看和处理系统告警信息</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleBatchProcess" icon="el-icon-finished">
          批量处理
        </el-button>
        <el-button @click="handleRefresh" icon="el-icon-refresh">
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 搜索和筛选 -->
    <el-card class="box-card search-card" shadow="never">
      <div class="search-bar">
        <el-input
          v-model="searchForm.keyword"
          placeholder="搜索告警内容、任务名称"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="searchForm.level" placeholder="告警级别" clearable @change="handleSearch">
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>
        
        <el-select v-model="searchForm.status" placeholder="处理状态" clearable @change="handleSearch">
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已解决" value="resolved" />
        </el-select>
        
        <el-date-picker
          v-model="searchForm.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 告警列表 -->
    <el-card class="box-card" shadow="never">
      <el-table
        :data="alerts"
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-class-name="alert-table-row"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="告警快照" width="100">
          <template #default="{ row }">
            <el-image 
              style="width: 70px; height: 50px; border-radius: 4px;"
              :src="`/${(row.alert_image || '').replace(/^\/+/, '')}`" 
              :preview-src-list="[`/${(row.alert_image || '').replace(/^\/+/, '')}`]"
              fit="cover"
              :initial-index="0"
              hide-on-click-modal
              preview-teleported
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="title" label="告警内容" min-width="250">
          <template #default="{ row }">
            <div class="alert-info">
              <div class="alert-desc">{{ row.description }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="task_name" label="关联任务" width="150" />
        
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">
              {{ getLevelText(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="confidence" label="置信度" width="120">
          <template #default="{ row }">
            <div class="confidence-bar">
              <el-progress
                :percentage="parseFloat((row.confidence * 100).toFixed(2))"
                :color="getConfidenceColor(row.confidence * 100)"
                :stroke-width="6"
                :show-text="false"
              />
              <span class="confidence-text">{{ (row.confidence * 100).toFixed(2) }}%</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="告警时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              text
              size="small"
              @click="viewAlertDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="success"
              text
              size="small"
              @click="processAlert(row)"
            >
              处理
            </el-button>
            <el-button
              type="danger"
              text
              size="small"
              @click="deleteAlert(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 批量处理对话框 -->
    <el-dialog
      v-model="showBatchDialog"
      title="批量处理告警"
      width="500px"
    >
      <el-form :model="batchForm" label-width="100px">
        <el-form-item label="处理状态">
          <el-select v-model="batchForm.status" placeholder="请选择处理状态">
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="处理备注">
          <el-input
            v-model="batchForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入处理备注"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBatchDialog = false">取消</el-button>
          <el-button type="primary" :loading="batchProcessing" @click="confirmBatchProcess">
            {{ batchProcessing ? '处理中...' : '确认处理' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, Warning, InfoFilled, SuccessFilled, ArrowDown } from '@element-plus/icons-vue'
import { getAlerts, updateAlert, deleteAlert as deleteAlertApi, batchUpdateAlerts } from '@/api/alerts'
import dayjs from 'dayjs'

const router = useRouter()

// 响应式数据
const alerts = ref([])
const loading = ref(false)
const selectedAlerts = ref([])
const showBatchDialog = ref(false)
const batchProcessing = ref(false)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  level: '',
  status: '',
  date_range: []
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 批量处理表单
const batchForm = reactive({
  status: '',
  remark: ''
})

// 获取告警列表
const loadAlerts = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    }
    
    if (searchForm.date_range && searchForm.date_range.length === 2) {
      params.start_date = searchForm.date_range[0]
      params.end_date = searchForm.date_range[1]
    }
    
    const response = await getAlerts(params)
    alerts.value = response.items
    pagination.total = response.total
  } catch (error) {
    console.error('加载告警列表失败:', error)
    ElMessage.error('加载告警列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadAlerts()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  loadAlerts()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadAlerts()
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedAlerts.value = selection
}

// 刷新
const handleRefresh = () => {
  loadAlerts()
}

// 批量处理
const handleBatchProcess = () => {
  if (selectedAlerts.value.length === 0) {
    ElMessage.warning('请选择要处理的告警')
    return
  }
  
  showBatchDialog.value = true
}

// 确认批量处理
const confirmBatchProcess = async () => {
  if (!batchForm.status) {
    ElMessage.warning('请选择处理状态')
    return
  }
  
  try {
    batchProcessing.value = true
    
    const ids = selectedAlerts.value.map(alert => alert.id)
    await batchUpdateAlerts(ids, {
      status: batchForm.status,
      remark: batchForm.remark
    })
    
    ElMessage.success('批量处理成功')
    showBatchDialog.value = false
    resetBatchForm()
    loadAlerts()
  } catch (error) {
    console.error('批量处理失败:', error)
    ElMessage.error('批量处理失败')
  } finally {
    batchProcessing.value = false
  }
}

// 重置批量处理表单
const resetBatchForm = () => {
  batchForm.status = ''
  batchForm.remark = ''
}

// 查看告警详情
const viewAlertDetail = (alert) => {
  router.push(`/alerts/${alert.id}`)
}

// 处理告警
const processAlert = async (alert) => {
  try {
    await updateAlert(alert.id, {
      status: 'processing',
      remark: '开始处理'
    })
    
    ElMessage.success('告警状态已更新')
    loadAlerts()
  } catch (error) {
    ElMessage.error('更新告警状态失败')
  }
}

// 删除告警
const deleteAlert = async (alert) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除告警 "${alert.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteAlertApi(alert.id)
    ElMessage.success('告警删除成功')
    loadAlerts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('告警删除失败')
    }
  }
}

// 工具函数
const getAlertIcon = (level) => {
  const icons = {
    high: 'Warning',
    medium: 'InfoFilled',
    low: 'SuccessFilled'
  }
  return icons[level] || 'InfoFilled'
}

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

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  loadAlerts()
})
</script>

<style lang="scss">
.el-table .alert-table-row {
  height: 75px;
}
</style>

<style scoped lang="scss">
.alerts-container {
  padding: 24px;
  background-color: #f7f8fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  .header-left {
    h2 {
      margin: 0 0 4px;
      font-size: 22px;
    }
    p {
      margin: 0;
      font-size: 14px;
      color: #909399;
    }
  }
}

.box-card {
  border: none;
}

.search-card {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.search-bar {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
  .el-input, .el-select {
    width: 240px;
  }
}

.alerts-table {
  .alert-content {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .alert-icon {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      
      &.high { background: #fef0f0; color: #f56c6c; }
      &.medium { background: #fdf6ec; color: #e6a23c; }
      &.low { background: #f0f9eb; color: #67c23a; }
    }
    
    .alert-info {
      .alert-title {
        font-weight: 500;
        color: #303133;
        margin-bottom: 4px;
      }
      .alert-desc {
        font-size: 13px;
        color: #606266;
        line-height: 1.5;
      }
    }
  }
  
  .confidence-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .confidence-text {
      font-size: 13px;
      color: #606266;
      min-width: 45px;
      font-weight: 500;
    }
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.danger-option {
  color: #f56c6c;
}
</style> 