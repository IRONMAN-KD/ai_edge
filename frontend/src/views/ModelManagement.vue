<template>
  <div class="model-management-container">
    <div class="page-header">
      <h1>模型管理</h1>
      <el-button type="primary" :icon="Plus" @click="showUploadDialog = true">
        上传新模型
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索模型名称..."
        clearable
        @input="handleSearch"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="按状态筛选" clearable @change="handleSearch">
        <el-option label="全部状态" value="" />
        <el-option label="启用" value="active" />
        <el-option label="禁用" value="inactive" />
      </el-select>
      <el-select v-model="typeFilter" placeholder="按类型筛选" clearable @change="handleSearch">
        <el-option label="全部类型" value="" />
        <el-option
          v-for="type in modelTypes"
          :key="type.value"
          :label="type.label"
          :value="type.value"
        />
      </el-select>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>
    
    <div v-else-if="models.length === 0" class="empty-state">
      <el-empty description="暂无模型数据，快去上传一个吧！" />
    </div>

    <div v-else class="model-grid">
      <el-card v-for="model in models" :key="model.id" class="model-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <div class="card-title">
              <el-icon :size="24" class="title-icon"><Cpu /></el-icon>
              <span>{{ model.name }}</span>
            </div>
            <el-tag :type="getStatusType(model.status)" effect="dark" round>
              {{ getStatusText(model.status) }}
            </el-tag>
          </div>
        </template>

        <div class="card-body">
          <div class="model-info">
            <div class="info-item">
              <el-icon><CollectionTag /></el-icon>
              <span>版本: <strong>{{ model.version }}</strong></span>
            </div>
            <div class="info-item">
              <el-icon><MessageBox /></el-icon>
              <span>类型: {{ getModelTypeLabel(model.type) }}</span>
            </div>
            <div class="info-item">
              <el-icon><Clock /></el-icon>
              <span>更新于: {{ formatDate(model.update_time) }}</span>
            </div>
          </div>
        </div>

        <div class="card-footer">
          <el-button :icon="View" type="primary" link @click="viewModel(model)">查看详情</el-button>
          <el-button 
            v-if="model.status === 'active'"
            :icon="Close" 
            type="danger" 
            link
            @click="toggleModelStatus(model, 'inactive')">
            禁用
          </el-button>
          <el-button 
            v-else 
            :icon="Check" 
            type="success" 
            link
            @click="toggleModelStatus(model, 'active')">
            启用
          </el-button>
          <el-button :icon="Edit" type="primary" link @click="openEditDialog(model)">编辑</el-button>
          <el-button 
            v-if="model.status === 'inactive'"
            :icon="Delete" 
            type="danger" 
            link
            @click="deleteModel(model)">
            删除
          </el-button>
        </div>
      </el-card>
    </div>
    
    <div class="pagination-container">
      <el-pagination
        v-if="total > 0"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchModels"
        @current-change="fetchModels"
      />
    </div>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="上传新模型" width="600px" :close-on-click-modal="false" @close="resetUploadForm">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="100px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="例如：YOLOv8s" />
        </el-form-item>
        <el-form-item label="模型版本" prop="version">
          <el-input v-model="uploadForm.version" placeholder="例如：1.0.0" />
        </el-form-item>
        <el-form-item label="模型类型" prop="type">
          <el-select v-model="uploadForm.type" placeholder="请选择模型类型">
            <el-option
              v-for="type in modelTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型标签" prop="labels">
          <el-input
            v-model="uploadForm.labels"
            type="textarea"
            :rows="4"
            placeholder="请输入模型标签，每行一个"
          />
          <div class="form-help">为模型的每个输出类别提供一个标签，按顺序每行一个。</div>
        </el-form-item>
        <el-form-item label="模型描述" prop="description">
          <el-input v-model="uploadForm.description" type="textarea" placeholder="请输入模型描述" />
        </el-form-item>
        <el-form-item label="模型文件" prop="file">
          <el-upload
            ref="uploadRef"
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="() => uploadForm.file = null"
            :limit="1"
            :file-list="fileList"
            accept=".onnx,.om"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">仅支持 ONNX 或 OM 格式，大小不超过 500MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">确认上传</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetailDialog" title="模型详情" width="700px">
      <div v-if="selectedModel" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="模型ID">{{ selectedModel.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedModel.status)" effect="dark" round>{{ getStatusText(selectedModel.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模型名称">{{ selectedModel.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ selectedModel.version }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ getModelTypeLabel(selectedModel.type) }}</el-descriptions-item>
          <el-descriptions-item label="文件路径">{{ selectedModel.file_path }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ formatDate(selectedModel.upload_time) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(selectedModel.update_time) }}</el-descriptions-item>
          <el-descriptions-item label="模型描述" :span="2">{{ selectedModel.description || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button type="primary" @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog v-model="showEditDialog" title="编辑模型" width="600px" @close="resetEditForm" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="uploadRules" label-width="100px" class="upload-dialog-form">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型版本" prop="version">
          <el-input v-model="editForm.version" placeholder="请输入模型版本" />
        </el-form-item>
        <el-form-item label="模型类型" prop="type">
          <el-select v-model="editForm.type" placeholder="请选择模型类型">
            <el-option
              v-for="type in modelTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型标签" prop="labels">
          <el-input
            v-model="editForm.labels"
            type="textarea"
            :rows="4"
            placeholder="请输入模型标签，每行一个"
          />
          <div class="form-help">为模型的每个输出类别提供一个标签，按顺序每行一个。</div>
        </el-form-item>
        <el-form-item label="模型描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" placeholder="请输入模型描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleUpdate">
            {{ saving ? '保存中...' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox, ElCard } from 'element-plus';
import { Plus, Search, UploadFilled, Cpu, CollectionTag, Clock, View, Delete, MessageBox, Check, Close, Edit } from '@element-plus/icons-vue';
import { getModels, uploadModel, deleteModel as apiDeleteModel, updateModelStatus, updateModel } from '@/api/models';
import { formatDate } from '@/utils/formatters';
import { MODEL_TYPES, getModelTypeLabel } from '@/utils/model_types';

const modelTypes = ref(MODEL_TYPES);

const loading = ref(true);
const models = ref([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);
const searchKeyword = ref('');
const statusFilter = ref('');
const typeFilter = ref('');

const showUploadDialog = ref(false);
const uploading = ref(false);
const uploadFormRef = ref();
const uploadRef = ref();
const fileList = ref([]);
const uploadForm = reactive({
  name: '',
  version: '1.0',
  description: '',
  type: 'object_detection',
  labels: '',
  file: null,
});

const uploadRules = {
  name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  version: [{ required: true, message: '请输入模型版本', trigger: 'blur' }],
  type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  labels: [{ required: true, message: '请输入模型标签', trigger: 'blur' }],
  file: [{ required: true, message: '请选择模型文件', trigger: 'change' }],
};

const showDetailDialog = ref(false);
const selectedModel = ref(null);

const showEditDialog = ref(false);
const saving = ref(false);
const editFormRef = ref();
const editForm = reactive({
  id: null,
  name: '',
  version: '',
  description: '',
  type: '',
  labels: '',
});

const fetchModels = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value,
      status: statusFilter.value,
      type: typeFilter.value,
    };
    const response = await getModels(params);
    models.value = response.items;
    total.value = response.total;
  } catch (error) {
    console.error('获取模型列表失败:', error);
    ElMessage.error('获取模型列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchModels();
};

const handleFileChange = (file) => {
  uploadForm.file = file.raw;
  fileList.value = [file];
};

const resetUploadForm = () => {
  if (uploadFormRef.value) {
    uploadFormRef.value.resetFields();
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
  uploadForm.file = null;
  fileList.value = [];
};

const submitUpload = () => {
  uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      uploading.value = true;
      const formData = new FormData();
      formData.append('name', uploadForm.name);
      formData.append('version', uploadForm.version);
      formData.append('description', uploadForm.description);
      formData.append('type', uploadForm.type);
      formData.append('file', uploadForm.file);

      // Process labels from textarea (one per line) into a JSON string array
      const labels = uploadForm.labels.split('\n').map(l => l.trim()).filter(l => l);
      formData.append('labels', JSON.stringify(labels));

      try {
        await uploadModel(formData);
        ElMessage.success('上传成功');
        showUploadDialog.value = false;
        fetchModels();
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '上传失败');
      } finally {
        uploading.value = false;
      }
    }
  });
};

const viewModel = (model) => {
  selectedModel.value = model;
  showDetailDialog.value = true;
};

const deleteModel = (model) => {
  ElMessageBox.confirm(`确定要永久删除模型 "${model.name}" (v${model.version})? 此操作无法撤销。`, '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await apiDeleteModel(model.id);
      ElMessage.success('删除成功');
      await fetchModels(); // Refresh list after deletion
    } catch (error) {
      ElMessage.error('删除失败');
      console.error('Failed to delete model:', error);
    }
  }).catch(() => {});
};

const toggleModelStatus = async (model, newStatus) => {
  const actionText = newStatus === 'active' ? '启用' : '禁用';
  try {
    await updateModelStatus(model.id, newStatus);
    ElMessage.success(`模型 ${actionText} 成功`);
    await fetchModels();
  } catch (error) {
    ElMessage.error(`模型 ${actionText} 失败`);
    console.error(`Failed to ${actionText} model:`, error);
  }
};

const openEditDialog = (model) => {
  editForm.id = model.id;
  editForm.name = model.name;
  editForm.version = model.version;
  editForm.description = model.description;
  editForm.type = model.type;
  editForm.labels = Array.isArray(model.labels) ? model.labels.join('\n') : '';
  showEditDialog.value = true;
};

const resetEditForm = () => {
  editForm.id = null;
  editForm.name = '';
  editForm.version = '';
  editForm.description = '';
  editForm.type = '';
  editForm.labels = '';
  if (editFormRef.value) {
    editFormRef.value.resetFields();
  }
};

const handleUpdate = async () => {
  editFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true;
      try {
        const payload = {
          name: editForm.name,
          version: editForm.version,
          description: editForm.description,
          type: editForm.type,
          labels: editForm.labels.split('\n').map(l => l.trim()).filter(l => l),
        };
        await updateModel(editForm.id, payload);
        ElMessage.success('模型更新成功');
        showEditDialog.value = false;
        fetchModels();
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '模型更新失败');
      } finally {
        saving.value = false;
      }
    }
  });
};

onMounted(fetchModels);

const getStatusType = (status) => ({ active: 'success', inactive: 'warning', deleted: 'danger' }[status] || 'primary');
const getStatusText = (status) => ({ active: '启用', inactive: '禁用', deleted: '禁用' }[status] || '未知');
</script>

<style scoped>
.model-management-container {
  padding: 24px;
  background-color: #f7f8fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.model-card {
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.model-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.title-icon {
  color: #409eff;
}

.card-body .model-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: #909399;
  font-size: 14px;
  padding-top: 16px;
}

.model-info .info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-info .info-item strong {
  color: #303133;
  font-weight: 500;
}

.card-footer {
  border-top: 1px solid #e4e7ed;
  padding-top: 16px;
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.loading-state, .empty-state {
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.detail-content {
  padding: 16px;
}

.upload-dialog .el-form {
  padding: 0 20px;
}

.form-help {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style> 