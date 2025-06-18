<template>
  <div class="settings-container">
    <div class="page-header">
      <h2>系统配置</h2>
      <p>配置系统核心参数和行为</p>
    </div>

    <el-card class="box-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>告警保留策略</span>
          <el-button type="primary" :loading="saving" @click="saveRetentionConfig">保存设置</el-button>
        </div>
      </template>

      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item>
          <template #label>
            <div class="form-item-label">
              <span>自动删除旧告警</span>
              <span class="form-item-desc">启用后，系统将定期删除超过指定保留时长的告警记录及其关联图片，以节省磁盘空间。</span>
            </div>
          </template>
          <el-switch v-model="form.alert_retention.enabled" />
        </el-form-item>

        <el-form-item v-if="form.alert_retention.enabled">
          <template #label>
            <div class="form-item-label">
              <span>数据保留时长（天）</span>
              <span class="form-item-desc">设置告警数据在被自动删除前应保留的天数。</span>
            </div>
          </template>
          <el-input-number v-model="form.alert_retention.days" :min="1" :max="3650" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="box-card" shadow="never" v-loading="loading" style="margin-top: 24px;">
      <template #header>
        <div class="card-header">
          <span>告警推送</span>
           <el-button type="primary" :loading="saving" @click="savePushConfig">保存设置</el-button>
        </div>
      </template>

      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item>
           <template #label>
            <div class="form-item-label">
              <span>启用告警推送</span>
              <span class="form-item-desc">在生成新告警时，通过所选方式将告警信息推送到外部系统。</span>
            </div>
          </template>
          <el-switch v-model="form.push_notification.enabled" />
        </el-form-item>

        <template v-if="form.push_notification.enabled">
          <el-form-item label="推送方式">
            <el-radio-group v-model="form.push_notification.type">
              <el-radio-button label="http">HTTP/HTTPS</el-radio-button>
              <el-radio-button label="mqtt">MQTT</el-radio-button>
              <el-radio-button label="kafka">Kafka</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <!-- HTTP/S Configs -->
          <div v-if="form.push_notification.type === 'http'">
            <el-form-item label="Webhook URL">
              <el-input v-model="form.push_notification.url" placeholder="https://your-service.com/webhook" />
            </el-form-item>
          </div>

          <!-- MQTT Configs -->
          <div v-if="form.push_notification.type === 'mqtt'">
            <el-form-item label="MQTT Broker 地址">
              <el-input v-model="form.push_notification.mqtt_broker" placeholder="e.g., mqtt.eclipseprojects.io" />
            </el-form-item>
            <el-form-item label="MQTT 端口">
              <el-input-number v-model="form.push_notification.mqtt_port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="MQTT 主题 (Topic)">
              <el-input v-model="form.push_notification.mqtt_topic" placeholder="e.g., /alerts/system1" />
            </el-form-item>
          </div>

          <!-- Kafka Configs -->
          <div v-if="form.push_notification.type === 'kafka'">
            <el-form-item label="Kafka Bootstrap Servers">
              <el-input v-model="form.push_notification.kafka_bootstrap_servers" placeholder="e.g., kafka1:9092,kafka2:9092" />
               <div class="form-item-desc">多个地址请用英文逗号分隔。</div>
            </el-form-item>
            <el-form-item label="Kafka Topic">
              <el-input v-model="form.push_notification.kafka_topic" placeholder="e.g., my-alerts-topic" />
            </el-form-item>
          </div>

        </template>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { getSystemConfigs, updateSystemConfigs } from '@/api/system';
import { ElMessage } from 'element-plus';

const loading = ref(true);
const saving = ref(false);

const form = reactive({
  alert_retention: {
    enabled: false,
    days: 30,
  },
  push_notification: {
    enabled: false,
    type: 'http',
    url: '',
    mqtt_broker: '',
    mqtt_port: 1883,
    mqtt_topic: '',
    kafka_bootstrap_servers: '',
    kafka_topic: '',
  },
});

const loadConfigs = async () => {
  loading.value = true;
  try {
    const data = await getSystemConfigs();
    if (data.alert_retention) {
      form.alert_retention = data.alert_retention;
    }
    if (data.push_notification) {
      // Ensure all possible keys are present
      form.push_notification = {
        ...form.push_notification,
        ...data.push_notification,
      };
    }
  } catch (error) {
    ElMessage.error('加载系统配置失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const saveRetentionConfig = async () => {
  saving.value = true;
  try {
    await updateSystemConfigs({ alert_retention: form.alert_retention });
    ElMessage.success('告警保留策略已保存');
  } catch (error) {
    ElMessage.error('保存失败');
    console.error(error);
  } finally {
    saving.value = false;
  }
};

const savePushConfig = async () => {
  saving.value = true;
  try {
    await updateSystemConfigs({ push_notification: form.push_notification });
    ElMessage.success('告警推送配置已保存');
  } catch (error) {
    ElMessage.error('保存失败');
    console.error(error);
  } finally {
    saving.value = false;
  }
};

onMounted(loadConfigs);
</script>

<style scoped lang="scss">
.settings-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
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

.box-card {
  border: none;
  :deep(.el-card__header) {
    background-color: #fafafa;
    font-weight: 500;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-form {
  max-width: 600px;
}

.form-item-label {
  display: flex;
  flex-direction: column;
  line-height: 1.5;
  .form-item-desc {
    font-size: 12px;
    color: #909399;
    font-weight: normal;
  }
}
</style> 