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
          <el-button type="primary" :loading="savingRetention" @click="saveRetentionConfig">保存设置</el-button>
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
           <el-button type="primary" :loading="savingPush" @click="savePushConfig">保存设置</el-button>
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
            
            <el-form-item>
              <template #label>
                <div class="form-item-label">
                  <span>请求方法</span>
                  <span class="form-item-desc">选择HTTP请求方法</span>
                </div>
              </template>
              <el-select v-model="form.push_notification.method" placeholder="请求方法">
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="PATCH" value="PATCH" />
                <el-option label="GET" value="GET" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <template #label>
                <div class="form-item-label">
                  <span>自定义请求头 (JSON格式)</span>
                  <span class="form-item-desc">配置HTTP请求头部参数，如认证信息等。格式示例：{"Authorization": "Bearer token", "X-API-Key": "your-key"}</span>
                </div>
              </template>
              <el-input 
                v-model="headersText"
                type="textarea" 
                :rows="4"
                placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json", "X-API-Key": "your-key"}'
                @blur="validateAndUpdateHeaders"
              />
              <div v-if="headersError" class="error-text">{{ headersError }}</div>
            </el-form-item>
            
            <el-form-item>
              <template #label>
                <div class="form-item-label">
                  <span>请求超时时间（秒）</span>
                  <span class="form-item-desc">HTTP请求的超时时间</span>
                </div>
              </template>
              <el-input-number v-model="form.push_notification.timeout" :min="1" :max="120" />
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
const savingRetention = ref(false);
const savingPush = ref(false);
const headersText = ref('{}');
const headersError = ref('');

const form = reactive({
  alert_retention: {
    enabled: false,
    days: 30,
  },
  push_notification: {
    enabled: false,
    type: 'http',
    url: '',
    method: 'POST',
    headers: {},
    timeout: 10,
    mqtt_broker: '',
    mqtt_port: 1883,
    mqtt_topic: '',
    kafka_bootstrap_servers: '',
    kafka_topic: '',
  },
});

const validateAndUpdateHeaders = () => {
  try {
    headersError.value = '';
    if (!headersText.value.trim()) {
      form.push_notification.headers = {};
      return;
    }
    
    const parsed = JSON.parse(headersText.value);
    if (typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('Headers必须是JSON对象格式');
    }
    
    form.push_notification.headers = parsed;
  } catch (error) {
    headersError.value = `JSON格式错误: ${error.message}`;
    form.push_notification.headers = {};
  }
};

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
      
      // 初始化headers文本框
      if (form.push_notification.headers && typeof form.push_notification.headers === 'object') {
        headersText.value = JSON.stringify(form.push_notification.headers, null, 2);
      }
    }
  } catch (error) {
    ElMessage.error('加载系统配置失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const saveRetentionConfig = async () => {
  if (savingRetention.value) return; // 防止重复点击
  
  savingRetention.value = true;
  try {
    await updateSystemConfigs({ alert_retention: form.alert_retention });
    ElMessage.success('告警保留策略已保存');
  } catch (error) {
    ElMessage.error('保存失败');
    console.error(error);
  } finally {
    savingRetention.value = false;
  }
};

const savePushConfig = async () => {
  if (savingPush.value) return; // 防止重复点击
  
  // 在保存前验证headers格式
  if (form.push_notification.type === 'http') {
    validateAndUpdateHeaders();
    if (headersError.value) {
      ElMessage.error('请修正Headers格式错误');
      return;
    }
  }
  
  savingPush.value = true;
  try {
    await updateSystemConfigs({ push_notification: form.push_notification });
    ElMessage.success('告警推送配置已保存');
  } catch (error) {
    ElMessage.error('保存失败');
    console.error(error);
  } finally {
    savingPush.value = false;
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

.error-text {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.4;
}
</style> 