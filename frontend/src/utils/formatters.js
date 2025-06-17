/**
 * 格式化日期时间
 * @param {string | Date} dateStr - 日期字符串或Date对象
 * @returns {string} 格式化的日期时间，如 'YYYY-MM-DD HH:mm:ss'
 */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '无效日期';
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-');
}

/**
 * 格式化文件大小
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化的文件大小，如 '10.24 MB'
 */
export function formatFileSize(bytes) {
  if (bytes === null || bytes === undefined || bytes < 0) return 'N/A';
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 