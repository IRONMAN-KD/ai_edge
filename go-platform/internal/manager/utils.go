package manager

import (
	"context"
	"fmt"
	"os"
	"runtime"
	"time"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
	"github.com/shirou/gopsutil/v3/process"
)

// GetSystemInfo 获取系统信息
func GetSystemInfo() (*SystemInfo, error) {
	hostInfo, err := host.Info()
	if err != nil {
		return nil, fmt.Errorf("failed to get host info: %w", err)
	}

	return &SystemInfo{
		Hostname:   hostInfo.Hostname,
		OS:         hostInfo.OS,
		Arch:       hostInfo.KernelArch,
		GoVersion:  runtime.Version(),
		StartTime:  time.Unix(int64(hostInfo.BootTime), 0),
		Uptime:     time.Duration(hostInfo.Uptime) * time.Second,
		PID:        os.Getpid(),
		Goroutines: runtime.NumGoroutine(),
	}, nil
}

// GetResourceUsage 获取资源使用情况
func GetResourceUsage() (*ResourceUsage, error) {
	// CPU 使用率
	cpuPercent, err := cpu.Percent(time.Second, false)
	if err != nil {
		return nil, fmt.Errorf("failed to get CPU usage: %w", err)
	}

	// 内存使用情况
	memInfo, err := mem.VirtualMemory()
	if err != nil {
		return nil, fmt.Errorf("failed to get memory info: %w", err)
	}

	// 磁盘使用情况
	diskInfo, err := disk.Usage("/")
	if err != nil {
		return nil, fmt.Errorf("failed to get disk info: %w", err)
	}

	// 网络统计
	netStats, err := net.IOCounters(false)
	if err != nil {
		return nil, fmt.Errorf("failed to get network stats: %w", err)
	}

	var networkIn, networkOut uint64
	if len(netStats) > 0 {
		networkIn = netStats[0].BytesRecv
		networkOut = netStats[0].BytesSent
	}

	var cpuPercentValue float64
	if len(cpuPercent) > 0 {
		cpuPercentValue = cpuPercent[0]
	}

	return &ResourceUsage{
		CPUPercent:    cpuPercentValue,
		MemoryUsed:    memInfo.Used,
		MemoryTotal:   memInfo.Total,
		MemoryPercent: memInfo.UsedPercent,
		DiskUsed:      diskInfo.Used,
		DiskTotal:     diskInfo.Total,
		DiskPercent:   diskInfo.UsedPercent,
		NetworkIn:     networkIn,
		NetworkOut:    networkOut,
	}, nil
}

// GetProcessInfo 获取进程信息
func GetProcessInfo(pid int32) (*ProcessInfo, error) {
	proc, err := process.NewProcess(pid)
	if err != nil {
		return nil, fmt.Errorf("failed to get process: %w", err)
	}

	name, _ := proc.Name()
	cmdline, _ := proc.Cmdline()
	cwd, _ := proc.Cwd()
	createTime, _ := proc.CreateTime()
	cpuPercent, _ := proc.CPUPercent()
	memInfo, _ := proc.MemoryInfo()
	status, _ := proc.Status()
	numThreads, _ := proc.NumThreads()
	numFDs, _ := proc.NumFDs()

	var memoryUsed uint64
	if memInfo != nil {
		memoryUsed = memInfo.RSS
	}

	return &ProcessInfo{
		PID:         pid,
		Name:        name,
		Cmdline:     cmdline,
		Cwd:         cwd,
		Status:      status,
		CreateTime:  time.Unix(int64(createTime/1000), 0),
		CPUPercent:  cpuPercent,
		MemoryUsed:  memoryUsed,
		NumThreads:  numThreads,
		NumFDs:      numFDs,
	}, nil
}

// ProcessInfo 进程信息
type ProcessInfo struct {
	PID        int32     `json:"pid"`
	Name       string    `json:"name"`
	Cmdline    string    `json:"cmdline"`
	Cwd        string    `json:"cwd"`
	Status     string    `json:"status"`
	CreateTime time.Time `json:"create_time"`
	CPUPercent float64   `json:"cpu_percent"`
	MemoryUsed uint64    `json:"memory_used"`
	NumThreads int32     `json:"num_threads"`
	NumFDs     int32     `json:"num_fds"`
}

// FormatBytes 格式化字节数
func FormatBytes(bytes uint64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// FormatDuration 格式化时间间隔
func FormatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%.1fs", d.Seconds())
	}
	if d < time.Hour {
		return fmt.Sprintf("%.1fm", d.Minutes())
	}
	if d < 24*time.Hour {
		return fmt.Sprintf("%.1fh", d.Hours())
	}
	return fmt.Sprintf("%.1fd", d.Hours()/24)
}

// FormatPercent 格式化百分比
func FormatPercent(value float64) string {
	return fmt.Sprintf("%.1f%%", value)
}

// CalculateErrorRate 计算错误率
func CalculateErrorRate(errors, total int64) float64 {
	if total == 0 {
		return 0
	}
	return float64(errors) / float64(total) * 100
}

// CalculateSuccessRate 计算成功率
func CalculateSuccessRate(success, total int64) float64 {
	if total == 0 {
		return 0
	}
	return float64(success) / float64(total) * 100
}

// CalculateAverage 计算平均值
func CalculateAverage(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

// CalculatePercentile 计算百分位数
func CalculatePercentile(values []float64, percentile float64) float64 {
	if len(values) == 0 {
		return 0
	}
	
	// 简单实现，实际应用中可能需要更精确的算法
	index := int(float64(len(values)) * percentile / 100)
	if index >= len(values) {
		index = len(values) - 1
	}
	return values[index]
}

// IsHealthy 检查组件是否健康
func IsHealthy(status string) bool {
	return status == "healthy" || status == "ok" || status == "up"
}

// GetHealthStatus 根据错误获取健康状态
func GetHealthStatus(err error) string {
	if err == nil {
		return "healthy"
	}
	return "unhealthy"
}

// GetHealthMessage 根据错误获取健康消息
func GetHealthMessage(err error) string {
	if err == nil {
		return "OK"
	}
	return err.Error()
}

// MergeMetrics 合并指标
func MergeMetrics(base, additional map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	
	// 复制基础指标
	for k, v := range base {
		result[k] = v
	}
	
	// 添加额外指标
	for k, v := range additional {
		result[k] = v
	}
	
	return result
}

// ValidateThreshold 验证阈值
func ValidateThreshold(value, threshold float64, operator string) bool {
	switch operator {
	case ">":
		return value > threshold
	case ">=":
		return value >= threshold
	case "<":
		return value < threshold
	case "<=":
		return value <= threshold
	case "==":
		return value == threshold
	case "!=":
		return value != threshold
	default:
		return false
	}
}

// GenerateID 生成唯一ID
func GenerateID(prefix string) string {
	return fmt.Sprintf("%s_%d", prefix, time.Now().UnixNano())
}

// SafeClose 安全关闭通道
func SafeClose(ch chan struct{}) {
	select {
	case <-ch:
		// 通道已关闭
	default:
		close(ch)
	}
}

// WithTimeout 带超时的上下文执行
func WithTimeout(ctx context.Context, timeout time.Duration, fn func(context.Context) error) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	
	done := make(chan error, 1)
	go func() {
		done <- fn(ctx)
	}()
	
	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

// RetryWithBackoff 带退避的重试
func RetryWithBackoff(ctx context.Context, maxRetries int, initialDelay time.Duration, fn func() error) error {
	var lastErr error
	delay := initialDelay
	
	for i := 0; i < maxRetries; i++ {
		if err := fn(); err == nil {
			return nil
		} else {
			lastErr = err
		}
		
		if i < maxRetries-1 {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(delay):
				delay *= 2 // 指数退避
			}
		}
	}
	
	return lastErr
}

// GetEnvOrDefault 获取环境变量或默认值
func GetEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Contains 检查切片是否包含元素
func Contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// RemoveDuplicates 移除重复元素
func RemoveDuplicates(slice []string) []string {
	seen := make(map[string]bool)
	result := []string{}
	
	for _, item := range slice {
		if !seen[item] {
			seen[item] = true
			result = append(result, item)
		}
	}
	
	return result
}

// Min 返回最小值
func Min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Max 返回最大值
func Max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// MinFloat64 返回最小浮点数
func MinFloat64(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

// MaxFloat64 返回最大浮点数
func MaxFloat64(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

// ClampFloat64 限制浮点数范围
func ClampFloat64(value, min, max float64) float64 {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}

// RoundFloat64 四舍五入浮点数
func RoundFloat64(value float64, precision int) float64 {
	multiplier := 1.0
	for i := 0; i < precision; i++ {
		multiplier *= 10
	}
	return float64(int(value*multiplier+0.5)) / multiplier
}