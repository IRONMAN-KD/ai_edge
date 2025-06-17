<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card dashboard-card" v-for="stat in stats" :key="stat.title">
        <div class="stat-icon" :style="{ background: stat.color }">
          <el-icon size="24" color="#fff">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-title">{{ stat.title }}</div>
          <div class="stat-change" :class="stat.trend">
            <el-icon size="12">
              <component :is="stat.trend === 'up' ? 'ArrowUp' : 'ArrowDown'" />
            </el-icon>
            {{ stat.change }}%
          </div>
        </div>
      </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-grid">
      <div class="chart-card dashboard-card">
        <div class="chart-header">
          <h3>告警趋势</h3>
          <el-select v-model="alertTimeRange" size="small">
            <el-option label="最近7天" value="7" />
            <el-option label="最近30天" value="30" />
            <el-option label="最近90天" value="90" />
          </el-select>
        </div>
        <div class="chart-content">
          <v-chart :option="alertChartOption" autoresize />
        </div>
      </div>
      
      <div class="chart-card dashboard-card">
        <div class="chart-header">
          <h3>任务状态分布</h3>
        </div>
        <div class="chart-content">
          <v-chart :option="taskChartOption" autoresize />
        </div>
      </div>
    </div>
    
    <!-- 最近告警 -->
    <div class="recent-alerts dashboard-card">
      <div class="card-header">
        <h3>最近告警</h3>
        <el-button type="primary" text @click="$router.push('/alerts')">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <div class="alerts-list">
        <div
          v-for="alert in recentAlerts"
          :key="alert.id"
          class="alert-item"
          @click="viewAlertDetail(alert.id)"
        >
          <div class="alert-icon" :class="alert.level">
            <el-icon size="16">
              <component :is="getAlertIcon(alert.level)" />
            </el-icon>
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-info">
              <span>{{ alert.task_name }}</span>
              <span>{{ formatTime(alert.created_at) }}</span>
            </div>
          </div>
          <div class="alert-status" :class="alert.status">
            {{ getStatusText(alert.status) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import {
  Cpu,
  VideoPlay,
  Warning,
  Bell,
  ArrowUp,
  ArrowDown,
  ArrowRight
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const router = useRouter()
const alertTimeRange = ref('7')

// 统计数据
const stats = reactive([
  {
    title: '运行任务',
    value: '12',
    change: '+8',
    trend: 'up',
    icon: 'VideoPlay',
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    title: '已部署模型',
    value: '8',
    change: '+2',
    trend: 'up',
    icon: 'Cpu',
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    title: '今日告警',
    value: '23',
    change: '-12',
    trend: 'down',
    icon: 'Warning',
    color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    title: '系统通知',
    value: '5',
    change: '+1',
    trend: 'up',
    icon: 'Bell',
    color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  }
])

// 告警趋势图表
const alertChartOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['告警数量', '处理数量']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '告警数量',
      type: 'line',
      smooth: true,
      data: [12, 19, 15, 25, 22, 18, 23],
      itemStyle: {
        color: '#f56c6c'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
            { offset: 1, color: 'rgba(245, 108, 108, 0.1)' }
          ]
        }
      }
    },
    {
      name: '处理数量',
      type: 'line',
      smooth: true,
      data: [10, 15, 12, 20, 18, 15, 19],
      itemStyle: {
        color: '#67c23a'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
          ]
        }
      }
    }
  ]
})

// 任务状态分布图表
const taskChartOption = ref({
  tooltip: {
    trigger: 'item'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: '任务状态',
      type: 'pie',
      radius: '50%',
      data: [
        { value: 8, name: '运行中', itemStyle: { color: '#67c23a' } },
        { value: 3, name: '已停止', itemStyle: { color: '#f56c6c' } },
        { value: 1, name: '异常', itemStyle: { color: '#e6a23c' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
})

// 最近告警数据
const recentAlerts = ref([
  {
    id: 1,
    title: '检测到异常行为',
    task_name: '监控任务-01',
    level: 'high',
    status: 'pending',
    created_at: '2024-01-15 14:30:00'
  },
  {
    id: 2,
    title: '置信度低于阈值',
    task_name: '监控任务-02',
    level: 'medium',
    status: 'processing',
    created_at: '2024-01-15 13:45:00'
  },
  {
    id: 3,
    title: '目标识别成功',
    task_name: '监控任务-03',
    level: 'low',
    status: 'resolved',
    created_at: '2024-01-15 12:20:00'
  }
])

const getAlertIcon = (level) => {
  const icons = {
    high: 'Warning',
    medium: 'InfoFilled',
    low: 'SuccessFilled'
  }
  return icons[level] || 'InfoFilled'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已解决'
  }
  return statusMap[status] || status
}

const formatTime = (time) => {
  return dayjs(time).format('MM-DD HH:mm')
}

const viewAlertDetail = (id) => {
  router.push(`/alerts/${id}`)
}

onMounted(() => {
  // 这里可以加载真实数据
  console.log('仪表盘加载完成')
})
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 24px;
  
  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20px;
  }
  
  .stat-content {
    flex: 1;
    
    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--text-color);
      margin-bottom: 4px;
    }
    
    .stat-title {
      font-size: 14px;
      color: var(--text-color-secondary);
      margin-bottom: 8px;
    }
    
    .stat-change {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      font-weight: 600;
      
      &.up {
        color: var(--success-color);
      }
      
      &.down {
        color: var(--danger-color);
      }
    }
  }
}

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  padding: 20px;
  
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-color);
    }
  }
  
  .chart-content {
    height: 300px;
  }
}

.recent-alerts {
  padding: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-color);
    }
  }
}

.alerts-list {
  .alert-item {
    display: flex;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    transition: background-color 0.3s;
    
    &:last-child {
      border-bottom: none;
    }
    
    &:hover {
      background: var(--bg-color);
    }
    
    .alert-icon {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
      
      &.high {
        background: rgba(245, 108, 108, 0.1);
        color: var(--danger-color);
      }
      
      &.medium {
        background: rgba(230, 162, 60, 0.1);
        color: var(--warning-color);
      }
      
      &.low {
        background: rgba(103, 194, 58, 0.1);
        color: var(--success-color);
      }
    }
    
    .alert-content {
      flex: 1;
      
      .alert-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 4px;
      }
      
      .alert-info {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: var(--text-color-secondary);
      }
    }
    
    .alert-status {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      
      &.pending {
        background: rgba(230, 162, 60, 0.1);
        color: var(--warning-color);
      }
      
      &.processing {
        background: rgba(64, 158, 255, 0.1);
        color: var(--primary-color);
      }
      
      &.resolved {
        background: rgba(103, 194, 58, 0.1);
        color: var(--success-color);
      }
    }
  }
}

// 响应式
@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .charts-grid {
    gap: 15px;
  }
  
  .stat-card {
    padding: 16px;
    
    .stat-icon {
      width: 50px;
      height: 50px;
      margin-right: 16px;
    }
    
    .stat-value {
      font-size: 24px;
    }
  }
}
</style> 