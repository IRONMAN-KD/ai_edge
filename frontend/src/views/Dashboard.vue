<template>
  <div class="dashboard-container" v-loading="loading">
    <!-- 概览统计 -->
    <el-row :gutter="20" class="summary-row">
      <el-col :span="6" v-for="item in summaryItems" :key="item.title">
        <el-card shadow="hover" class="summary-card">
          <div class="card-content">
            <div class="icon-wrapper" :style="{ backgroundColor: item.color }">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="text-wrapper">
              <div class="title">{{ item.title }}</div>
              <div class="value">{{ item.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表和列表 -->
    <el-row :gutter="20">
      <!-- 告警状态分布 -->
      <el-col :span="8">
        <el-card shadow="never" class="chart-card">
          <template #header>告警状态分布</template>
          <div ref="alertStatusPie" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <!-- 过去7日告警趋势 -->
      <el-col :span="16">
        <el-card shadow="never" class="chart-card">
          <template #header>过去7日告警趋势</template>
          <div ref="alertsPastWeekLine" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近告警 -->
    <el-row>
      <el-col :span="24">
        <el-card shadow="never" class="latest-alerts-card">
          <template #header>最近告警</template>
          <el-table :data="latestAlerts" style="width: 100%" @row-click="goToAlertDetail">
            <el-table-column prop="title" label="告警标题" />
            <el-table-column prop="task_name" label="关联任务" width="180" />
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)">{{ getLevelText(row.level) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="告警时间" width="200">
               <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getDashboardStats } from '@/api/dashboard'
import { ElMessage } from 'element-plus'
import { Tickets, VideoCamera, Menu, Warning } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const loading = ref(true)
const router = useRouter()

// Refs for chart elements
const alertStatusPie = ref(null)
const alertsPastWeekLine = ref(null)

// Data
const summaryData = ref({ total_tasks: 0, running_tasks: 0, total_models: 0, pending_alerts: 0 })
const alertsByStatus = ref({ pending: 0, processing: 0, resolved: 0 })
const alertsPastWeek = ref([])
const latestAlerts = ref([])

const summaryItems = computed(() => [
  { title: '任务总数', value: summaryData.value.total_tasks, icon: Tickets, color: '#409EFF' },
  { title: '运行中任务', value: summaryData.value.running_tasks, icon: VideoCamera, color: '#67C23A' },
  { title: '模型总数', value: summaryData.value.total_models, icon: Menu, color: '#E6A23C' },
  { title: '待处理告警', value: summaryData.value.pending_alerts, icon: Warning, color: '#F56C6C' },
])

const fetchData = async () => {
  try {
    loading.value = true
    const stats = await getDashboardStats()
    summaryData.value = stats.summary
    alertsByStatus.value = stats.alerts_by_status
    alertsPastWeek.value = stats.alerts_past_week
    latestAlerts.value = stats.latest_alerts
    await nextTick()
    initCharts()
  } catch (error) {
    ElMessage.error('加载仪表盘数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  // Pie Chart
  const pieChart = echarts.init(alertStatusPie.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { top: 'bottom' },
    series: [{
      name: '告警状态',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      data: [
        { value: alertsByStatus.value.pending, name: '待处理' },
        { value: alertsByStatus.value.processing, name: '处理中' },
        { value: alertsByStatus.value.resolved, name: '已解决' },
      ],
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })

  // Line Chart
  const lineChart = echarts.init(alertsPastWeekLine.value)
  lineChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: alertsPastWeek.value.map(item => item.date) },
    yAxis: { type: 'value' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    series: [{
      name: '告警数',
      data: alertsPastWeek.value.map(item => item.count),
      type: 'line',
      smooth: true
    }]
  })
}

// Utils
const getLevelType = (level) => ({ high: 'danger', medium: 'warning', low: 'success' }[level] || 'info')
const getLevelText = (level) => ({ high: '高', medium: '中', low: '低' }[level] || level)
const formatTime = (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : 'N/A'
const goToAlertDetail = (row) => router.push(`/alerts/${row.id}`)

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 24px;
}
.summary-row {
  margin-bottom: 20px;
}
.summary-card .card-content {
  display: flex;
  align-items: center;
  .icon-wrapper {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 30px;
    margin-right: 20px;
  }
  .text-wrapper {
    .title {
      font-size: 14px;
      color: #909399;
      margin-bottom: 8px;
    }
    .value {
      font-size: 24px;
      font-weight: bold;
    }
  }
}
.chart-card, .latest-alerts-card {
  margin-bottom: 20px;
}
:deep(.el-card__header) {
  font-weight: bold;
}
</style> 