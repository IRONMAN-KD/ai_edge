package manager

import (
	"context"
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	"ai-edge-platform/internal/models"
	"ai-edge-platform/internal/services"
)

// TaskScheduler 任务调度器
type TaskScheduler struct {
	config           *TaskSchedulerConfig
	taskService      services.TaskService
	inferenceService services.InferenceService

	// 工作池
	workerPool chan struct{}
	taskQueue  chan *models.Task

	// 统计
	processedTasks int64
	failedTasks    int64
	lastRun        time.Time

	// 控制
	ctx     context.Context
	cancel  context.CancelFunc
	wg      sync.WaitGroup
	mu      sync.RWMutex
	running bool
}

// TaskSchedulerConfig 任务调度器配置
type TaskSchedulerConfig struct {
	Interval  time.Duration
	Workers   int
	QueueSize int
}

// NewTaskScheduler 创建新的任务调度器
func NewTaskScheduler(config *TaskSchedulerConfig, taskService services.TaskService, inferenceService services.InferenceService) *TaskScheduler {
	return &TaskScheduler{
		config:           config,
		taskService:      taskService,
		inferenceService: inferenceService,
		workerPool:       make(chan struct{}, config.Workers),
		taskQueue:        make(chan *models.Task, config.QueueSize),
	}
}

// Start 启动任务调度器
func (ts *TaskScheduler) Start(ctx context.Context) error {
	ts.mu.Lock()
	defer ts.mu.Unlock()

	if ts.running {
		return fmt.Errorf("task scheduler is already running")
	}

	log.Println("Starting task scheduler...")

	ts.ctx, ts.cancel = context.WithCancel(ctx)
	ts.running = true

	// 启动工作者
	for i := 0; i < ts.config.Workers; i++ {
		ts.wg.Add(1)
		go ts.worker(i)
	}

	// 启动调度器
	ts.wg.Add(1)
	go ts.scheduler()

	log.Printf("Task scheduler started with %d workers", ts.config.Workers)

	// 等待上下文取消
	<-ts.ctx.Done()

	// 等待所有工作者完成
	ts.wg.Wait()

	ts.mu.Lock()
	ts.running = false
	ts.mu.Unlock()

	log.Println("Task scheduler stopped")
	return nil
}

// Stop 停止任务调度器
func (ts *TaskScheduler) Stop() {
	ts.mu.Lock()
	defer ts.mu.Unlock()

	if !ts.running {
		return
	}

	log.Println("Stopping task scheduler...")

	if ts.cancel != nil {
		ts.cancel()
	}
}

// GetStatus 获取任务调度器状态
func (ts *TaskScheduler) GetStatus() *TaskSchedulerStatus {
	ts.mu.RLock()
	defer ts.mu.RUnlock()

	return &TaskSchedulerStatus{
		Running:        ts.running,
		ActiveWorkers:  ts.config.Workers,
		QueueSize:      len(ts.taskQueue),
		ProcessedTasks: atomic.LoadInt64(&ts.processedTasks),
		FailedTasks:    atomic.LoadInt64(&ts.failedTasks),
		LastRun:        ts.lastRun,
	}
}

// scheduler 主调度循环
func (ts *TaskScheduler) scheduler() {
	defer ts.wg.Done()

	ticker := time.NewTicker(ts.config.Interval)
	defer ticker.Stop()

	log.Printf("Task scheduler running with interval: %v", ts.config.Interval)

	for {
		select {
		case <-ts.ctx.Done():
			log.Println("Task scheduler context cancelled")
			return
		case <-ticker.C:
			ts.scheduleEnabledTasks()
		}
	}
}

// scheduleEnabledTasks 调度启用的任务
func (ts *TaskScheduler) scheduleEnabledTasks() {
	ts.lastRun = time.Now()

	// 获取启用的任务
	tasks, err := ts.taskService.GetEnabledTasks(ts.ctx)
	if err != nil {
		log.Printf("Failed to get enabled tasks: %v", err)
		return
	}

	log.Printf("Found %d enabled tasks", len(tasks))

	// 检查每个任务是否需要执行
	for _, task := range tasks {
		if ts.shouldExecuteTask(task) {
			select {
			case ts.taskQueue <- task:
				log.Printf("Task %d queued for execution", task.ID)
			case <-ts.ctx.Done():
				return
			default:
				log.Printf("Task queue full, skipping task %d", task.ID)
			}
		}
	}
}

// shouldExecuteTask 检查任务是否应该执行
func (ts *TaskScheduler) shouldExecuteTask(task *models.Task) bool {
	// 检查任务状态
	if task.Status != "enabled" {
		return false
	}

	// 检查任务类型和调度配置
	switch task.Type {
	case "scheduled":
		return ts.shouldExecuteScheduledTask(task)
	case "continuous":
		return ts.shouldExecuteContinuousTask(task)
	case "triggered":
		return ts.shouldExecuteTriggeredTask(task)
	default:
		log.Printf("Unknown task type: %s", task.Type)
		return false
	}
}

// shouldExecuteScheduledTask 检查定时任务是否应该执行
func (ts *TaskScheduler) shouldExecuteScheduledTask(task *models.Task) bool {
	// 解析调度配置
	scheduleConfig, err := parseScheduleConfig(task.Config)
	if err != nil {
		log.Printf("Failed to parse schedule config for task %d: %v", task.ID, err)
		return false
	}

	// 检查是否到了执行时间
	now := time.Now()
	if task.LastRun == nil {
		return true // 从未执行过
	}

	// 根据调度类型检查
	switch scheduleConfig.Type {
	case "interval":
		return now.Sub(*task.LastRun) >= scheduleConfig.Interval
	case "cron":
		// 这里可以集成 cron 解析库
		return ts.checkCronSchedule(scheduleConfig.Cron, *task.LastRun, now)
	default:
		return false
	}
}

// shouldExecuteContinuousTask 检查连续任务是否应该执行
func (ts *TaskScheduler) shouldExecuteContinuousTask(task *models.Task) bool {
	// 连续任务应该一直运行，检查是否已经在运行
	return task.Status == "enabled" && (task.LastRun == nil || time.Since(*task.LastRun) > time.Minute)
}

// shouldExecuteTriggeredTask 检查触发任务是否应该执行
func (ts *TaskScheduler) shouldExecuteTriggeredTask(task *models.Task) bool {
	// 触发任务需要外部触发，这里可以检查触发条件
	// 例如：文件变化、数据库变化、外部事件等
	return false // 暂时不支持
}

// worker 工作者协程
func (ts *TaskScheduler) worker(id int) {
	defer ts.wg.Done()

	log.Printf("Task worker %d started", id)

	for {
		select {
		case <-ts.ctx.Done():
			log.Printf("Task worker %d stopped", id)
			return
		case task := <-ts.taskQueue:
			ts.executeTask(task, id)
		}
	}
}

// executeTask 执行任务
func (ts *TaskScheduler) executeTask(task *models.Task, workerID int) {
	log.Printf("Worker %d executing task %d (%s)", workerID, task.ID, task.Name)

	start := time.Now()

	// 更新任务状态为运行中
	if err := ts.taskService.UpdateTaskStatus(ts.ctx, task.ID, "running"); err != nil {
		log.Printf("Failed to update task status to running: %v", err)
	}

	// 执行任务
	err := ts.performTaskExecution(task)

	duration := time.Since(start)

	// 更新统计
	if err != nil {
		atomic.AddInt64(&ts.failedTasks, 1)
		log.Printf("Task %d failed after %v: %v", task.ID, duration, err)

		// 更新任务状态为失败
		if updateErr := ts.taskService.UpdateTaskStatus(ts.ctx, task.ID, "failed"); updateErr != nil {
			log.Printf("Failed to update task status to failed: %v", updateErr)
		}
	else {
		atomic.AddInt64(&ts.processedTasks, 1)
		log.Printf("Task %d completed successfully in %v", task.ID, duration)

		// 更新任务状态为完成
		if updateErr := ts.taskService.UpdateTaskStatus(ts.ctx, task.ID, "completed"); updateErr != nil {
			log.Printf("Failed to update task status to completed: %v", updateErr)
		}
	}

	// 更新最后运行时间
	now := time.Now()
	if updateErr := ts.taskService.UpdateLastRun(ts.ctx, task.ID, &now); updateErr != nil {
		log.Printf("Failed to update task last run time: %v", updateErr)
	}
}

// performTaskExecution 执行具体的任务逻辑
func (ts *TaskScheduler) performTaskExecution(task *models.Task) error {
	// 解析任务配置
	taskConfig, err := parseTaskConfig(task.Config)
	if err != nil {
		return fmt.Errorf("failed to parse task config: %w", err)
	}

	// 根据任务类型执行不同的逻辑
	switch taskConfig.Action {
	case "inference":
		return ts.executeInferenceTask(task, taskConfig)
	case "model_update":
		return ts.executeModelUpdateTask(task, taskConfig)
	case "data_cleanup":
		return ts.executeDataCleanupTask(task, taskConfig)
	case "health_check":
		return ts.executeHealthCheckTask(task, taskConfig)
	default:
		return fmt.Errorf("unknown task action: %s", taskConfig.Action)
	}
}

// executeInferenceTask 执行推理任务
func (ts *TaskScheduler) executeInferenceTask(task *models.Task, config *TaskConfig) error {
	log.Printf("Executing inference task %d", task.ID)

	// 创建推理记录
	inferenceRecord := &models.InferenceRecord{
		TaskID:    task.ID,
		ModelID:   config.ModelID,
		Status:    "running",
		StartTime: time.Now(),
	}

	// 保存推理记录
	if err := ts.inferenceService.CreateInferenceRecord(ts.ctx, inferenceRecord); err != nil {
		return fmt.Errorf("failed to create inference record: %w", err)
	}

	// 这里可以调用实际的推理服务
	// 例如：通过 gRPC 调用推理服务

	// 模拟推理执行
	time.Sleep(time.Duration(config.Duration) * time.Second)

	// 更新推理记录状态
	inferenceRecord.Status = "completed"
	inferenceRecord.EndTime = &time.Time{}
	*inferenceRecord.EndTime = time.Now()

	if err := ts.inferenceService.UpdateInferenceRecord(ts.ctx, inferenceRecord.ID, inferenceRecord); err != nil {
		return fmt.Errorf("failed to update inference record: %w", err)
	}

	return nil
}

// executeModelUpdateTask 执行模型更新任务
func (ts *TaskScheduler) executeModelUpdateTask(task *models.Task, config *TaskConfig) error {
	log.Printf("Executing model update task %d", task.ID)

	// 这里可以实现模型更新逻辑
	// 例如：下载新模型、验证模型、部署模型等

	return nil
}

// executeDataCleanupTask 执行数据清理任务
func (ts *TaskScheduler) executeDataCleanupTask(task *models.Task, config *TaskConfig) error {
	log.Printf("Executing data cleanup task %d", task.ID)

	// 这里可以实现数据清理逻辑
	// 例如：清理过期的推理记录、日志文件等

	return nil
}

// executeHealthCheckTask 执行健康检查任务
func (ts *TaskScheduler) executeHealthCheckTask(task *models.Task, config *TaskConfig) error {
	log.Printf("Executing health check task %d", task.ID)

	// 这里可以实现健康检查逻辑
	// 例如：检查服务状态、数据库连接、外部依赖等

	return nil
}

// checkCronSchedule 检查 cron 调度
func (ts *TaskScheduler) checkCronSchedule(cronExpr string, lastRun, now time.Time) bool {
	// 这里可以集成 cron 解析库，如 github.com/robfig/cron
	// 暂时返回 false
	return false
}

// ScheduleConfig 调度配置
type ScheduleConfig struct {
	Type     string        `json:"type"`     // interval, cron
	Interval time.Duration `json:"interval"` // 间隔时间
	Cron     string        `json:"cron"`     // cron 表达式
}

// TaskConfig 任务配置
type TaskConfig struct {
	Action   string `json:"action"`   // inference, model_update, data_cleanup, health_check
	ModelID  uint   `json:"model_id"` // 模型ID（用于推理任务）
	Duration int    `json:"duration"` // 执行时长（秒）
	Params   map[string]interface{} `json:"params"` // 其他参数
}

// parseScheduleConfig 解析调度配置
func parseScheduleConfig(config string) (*ScheduleConfig, error) {
	// 这里应该解析 JSON 配置
	// 暂时返回默认配置
	return &ScheduleConfig{
		Type:     "interval",
		Interval: 5 * time.Minute,
	}, nil
}

// parseTaskConfig 解析任务配置
func parseTaskConfig(config string) (*TaskConfig, error) {
	// 这里应该解析 JSON 配置
	// 暂时返回默认配置
	return &TaskConfig{
		Action:   "inference",
		ModelID:  1,
		Duration: 10,
		Params:   make(map[string]interface{}),
	}, nil
}