package manager

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"ai-edge-platform/internal/models"
	"ai-edge-platform/internal/services"
)

// AlertManager 告警管理器
type AlertManager struct {
	config       *AlertManagerConfig
	alertService services.AlertService

	// 告警规则
	rules map[string]*AlertRule

	// 告警抑制
	suppression map[string]time.Time

	// 通知渠道
	notifiers []AlertNotifier

	// 控制
	ctx     context.Context
	cancel  context.CancelFunc
	wg      sync.WaitGroup
	mu      sync.RWMutex
	running bool
}

// AlertManagerConfig 告警管理器配置
type AlertManagerConfig struct {
	CheckInterval    time.Duration
	SuppressionTime  time.Duration
	MaxAlerts        int
	NotificationConfig *NotificationConfig
}

// NotificationConfig 通知配置
type NotificationConfig struct {
	Email    *EmailConfig    `json:"email"`
	Webhook  *WebhookConfig  `json:"webhook"`
	Slack    *SlackConfig    `json:"slack"`
	DingTalk *DingTalkConfig `json:"dingtalk"`
}

// EmailConfig 邮件配置
type EmailConfig struct {
	Enabled    bool     `json:"enabled"`
	SMTPHost   string   `json:"smtp_host"`
	SMTPPort   int      `json:"smtp_port"`
	Username   string   `json:"username"`
	Password   string   `json:"password"`
	From       string   `json:"from"`
	To         []string `json:"to"`
	Subject    string   `json:"subject"`
	Template   string   `json:"template"`
}

// WebhookConfig Webhook 配置
type WebhookConfig struct {
	Enabled bool   `json:"enabled"`
	URL     string `json:"url"`
	Method  string `json:"method"`
	Headers map[string]string `json:"headers"`
	Timeout time.Duration `json:"timeout"`
}

// SlackConfig Slack 配置
type SlackConfig struct {
	Enabled   bool   `json:"enabled"`
	WebhookURL string `json:"webhook_url"`
	Channel   string `json:"channel"`
	Username  string `json:"username"`
	IconEmoji string `json:"icon_emoji"`
}

// DingTalkConfig 钉钉配置
type DingTalkConfig struct {
	Enabled     bool   `json:"enabled"`
	WebhookURL  string `json:"webhook_url"`
	Secret      string `json:"secret"`
	AtMobiles   []string `json:"at_mobiles"`
	AtAll       bool   `json:"at_all"`
}

// AlertRule 告警规则
type AlertRule struct {
	ID          string        `json:"id"`
	Name        string        `json:"name"`
	Description string        `json:"description"`
	Condition   string        `json:"condition"`
	Level       string        `json:"level"`
	Enabled     bool          `json:"enabled"`
	Interval    time.Duration `json:"interval"`
	Threshold   float64       `json:"threshold"`
	Actions     []string      `json:"actions"`
	CreatedAt   time.Time     `json:"created_at"`
	UpdatedAt   time.Time     `json:"updated_at"`
}

// AlertNotifier 告警通知器接口
type AlertNotifier interface {
	Notify(ctx context.Context, alert *models.Alert) error
	GetType() string
}

// NewAlertManager 创建新的告警管理器
func NewAlertManager(config *AlertManagerConfig, alertService services.AlertService) *AlertManager {
	am := &AlertManager{
		config:       config,
		alertService: alertService,
		rules:        make(map[string]*AlertRule),
		suppression:  make(map[string]time.Time),
		notifiers:    make([]AlertNotifier, 0),
	}

	// 初始化通知器
	am.initNotifiers()

	return am
}

// Start 启动告警管理器
func (am *AlertManager) Start(ctx context.Context) error {
	am.mu.Lock()
	defer am.mu.Unlock()

	if am.running {
		return fmt.Errorf("alert manager is already running")
	}

	log.Println("Starting alert manager...")

	am.ctx, am.cancel = context.WithCancel(ctx)
	am.running = true

	// 启动告警处理循环
	am.wg.Add(1)
	go am.alertLoop()

	// 启动规则检查循环
	am.wg.Add(1)
	go am.ruleCheckLoop()

	log.Printf("Alert manager started with %d notifiers", len(am.notifiers))

	// 等待上下文取消
	<-am.ctx.Done()

	// 等待所有协程完成
	am.wg.Wait()

	am.mu.Lock()
	am.running = false
	am.mu.Unlock()

	log.Println("Alert manager stopped")
	return nil
}

// Stop 停止告警管理器
func (am *AlertManager) Stop() {
	am.mu.Lock()
	defer am.mu.Unlock()

	if !am.running {
		return
	}

	log.Println("Stopping alert manager...")

	if am.cancel != nil {
		am.cancel()
	}
}

// GetStatus 获取告警管理器状态
func (am *AlertManager) GetStatus() *AlertManagerStatus {
	am.mu.RLock()
	defer am.mu.RUnlock()

	return &AlertManagerStatus{
		Running:       am.running,
		RulesCount:    len(am.rules),
		NotifiersCount: len(am.notifiers),
		SuppressionCount: len(am.suppression),
	}
}

// AddRule 添加告警规则
func (am *AlertManager) AddRule(rule *AlertRule) {
	am.mu.Lock()
	defer am.mu.Unlock()

	rule.CreatedAt = time.Now()
	rule.UpdatedAt = time.Now()
	am.rules[rule.ID] = rule

	log.Printf("Alert rule added: %s", rule.Name)
}

// RemoveRule 移除告警规则
func (am *AlertManager) RemoveRule(ruleID string) {
	am.mu.Lock()
	defer am.mu.Unlock()

	if rule, exists := am.rules[ruleID]; exists {
		delete(am.rules, ruleID)
		log.Printf("Alert rule removed: %s", rule.Name)
	}
}

// GetRules 获取所有告警规则
func (am *AlertManager) GetRules() []*AlertRule {
	am.mu.RLock()
	defer am.mu.RUnlock()

	rules := make([]*AlertRule, 0, len(am.rules))
	for _, rule := range am.rules {
		rules = append(rules, rule)
	}

	return rules
}

// ProcessAlert 处理告警
func (am *AlertManager) ProcessAlert(alert *models.Alert) error {
	// 检查告警是否被抑制
	if am.isAlertSuppressed(alert) {
		log.Printf("Alert suppressed: %s", alert.Type)
		return nil
	}

	// 发送通知
	for _, notifier := range am.notifiers {
		if err := notifier.Notify(am.ctx, alert); err != nil {
			log.Printf("Failed to send notification via %s: %v", notifier.GetType(), err)
		} else {
			log.Printf("Notification sent via %s for alert: %s", notifier.GetType(), alert.Type)
		}
	}

	// 添加到抑制列表
	am.addToSuppression(alert)

	return nil
}

// alertLoop 告警处理主循环
func (am *AlertManager) alertLoop() {
	defer am.wg.Done()

	ticker := time.NewTicker(am.config.CheckInterval)
	defer ticker.Stop()

	log.Printf("Alert processing loop started with interval: %v", am.config.CheckInterval)

	for {
		select {
		case <-am.ctx.Done():
			log.Println("Alert processing loop context cancelled")
			return
		case <-ticker.C:
			am.processActiveAlerts()
			am.cleanupSuppression()
		}
	}
}

// ruleCheckLoop 规则检查循环
func (am *AlertManager) ruleCheckLoop() {
	defer am.wg.Done()

	ticker := time.NewTicker(am.config.CheckInterval)
	defer ticker.Stop()

	log.Printf("Rule check loop started with interval: %v", am.config.CheckInterval)

	for {
		select {
		case <-am.ctx.Done():
			log.Println("Rule check loop context cancelled")
			return
		case <-ticker.C:
			am.checkRules()
		}
	}
}

// processActiveAlerts 处理活跃告警
func (am *AlertManager) processActiveAlerts() {
	// 获取活跃告警
	alerts, err := am.alertService.GetActiveAlerts(am.ctx)
	if err != nil {
		log.Printf("Failed to get active alerts: %v", err)
		return
	}

	log.Printf("Processing %d active alerts", len(alerts))

	// 处理每个告警
	for _, alert := range alerts {
		if err := am.ProcessAlert(alert); err != nil {
			log.Printf("Failed to process alert %d: %v", alert.ID, err)
		}
	}
}

// checkRules 检查告警规则
func (am *AlertManager) checkRules() {
	am.mu.RLock()
	rules := make([]*AlertRule, 0, len(am.rules))
	for _, rule := range am.rules {
		if rule.Enabled {
			rules = append(rules, rule)
		}
	}
	am.mu.RUnlock()

	log.Printf("Checking %d enabled rules", len(rules))

	// 检查每个规则
	for _, rule := range rules {
		if am.evaluateRule(rule) {
			am.triggerRuleAlert(rule)
		}
	}
}

// evaluateRule 评估告警规则
func (am *AlertManager) evaluateRule(rule *AlertRule) bool {
	// 这里需要实现规则评估逻辑
	// 可以根据规则条件查询指标数据，判断是否满足告警条件
	// 暂时返回 false
	return false
}

// triggerRuleAlert 触发规则告警
func (am *AlertManager) triggerRuleAlert(rule *AlertRule) {
	alert := &models.Alert{
		Type:      rule.ID,
		Level:     rule.Level,
		Message:   fmt.Sprintf("Rule '%s' triggered: %s", rule.Name, rule.Description),
		Source:    "alert_manager",
		Status:    "active",
		CreatedAt: time.Now(),
	}

	if err := am.alertService.CreateAlert(am.ctx, alert); err != nil {
		log.Printf("Failed to create rule alert: %v", err)
	} else {
		log.Printf("Rule alert created: %s", rule.Name)
	}
}

// isAlertSuppressed 检查告警是否被抑制
func (am *AlertManager) isAlertSuppressed(alert *models.Alert) bool {
	am.mu.RLock()
	defer am.mu.RUnlock()

	key := am.getSuppressionKey(alert)
	if suppressedUntil, exists := am.suppression[key]; exists {
		return time.Now().Before(suppressedUntil)
	}

	return false
}

// addToSuppression 添加到抑制列表
func (am *AlertManager) addToSuppression(alert *models.Alert) {
	am.mu.Lock()
	defer am.mu.Unlock()

	key := am.getSuppressionKey(alert)
	am.suppression[key] = time.Now().Add(am.config.SuppressionTime)
}

// getSuppressionKey 获取抑制键
func (am *AlertManager) getSuppressionKey(alert *models.Alert) string {
	return fmt.Sprintf("%s:%s", alert.Type, alert.Source)
}

// cleanupSuppression 清理过期的抑制记录
func (am *AlertManager) cleanupSuppression() {
	am.mu.Lock()
	defer am.mu.Unlock()

	now := time.Now()
	for key, suppressedUntil := range am.suppression {
		if now.After(suppressedUntil) {
			delete(am.suppression, key)
		}
	}
}

// initNotifiers 初始化通知器
func (am *AlertManager) initNotifiers() {
	if am.config.NotificationConfig == nil {
		return
	}

	config := am.config.NotificationConfig

	// 初始化邮件通知器
	if config.Email != nil && config.Email.Enabled {
		notifier := NewEmailNotifier(config.Email)
		am.notifiers = append(am.notifiers, notifier)
		log.Println("Email notifier initialized")
	}

	// 初始化 Webhook 通知器
	if config.Webhook != nil && config.Webhook.Enabled {
		notifier := NewWebhookNotifier(config.Webhook)
		am.notifiers = append(am.notifiers, notifier)
		log.Println("Webhook notifier initialized")
	}

	// 初始化 Slack 通知器
	if config.Slack != nil && config.Slack.Enabled {
		notifier := NewSlackNotifier(config.Slack)
		am.notifiers = append(am.notifiers, notifier)
		log.Println("Slack notifier initialized")
	}

	// 初始化钉钉通知器
	if config.DingTalk != nil && config.DingTalk.Enabled {
		notifier := NewDingTalkNotifier(config.DingTalk)
		am.notifiers = append(am.notifiers, notifier)
		log.Println("DingTalk notifier initialized")
	}
}

// LoadDefaultRules 加载默认告警规则
func (am *AlertManager) LoadDefaultRules() {
	// 系统资源告警规则
	am.AddRule(&AlertRule{
		ID:          "high_cpu_usage",
		Name:        "High CPU Usage",
		Description: "CPU usage exceeds threshold",
		Condition:   "cpu_usage > 80",
		Level:       "warning",
		Enabled:     true,
		Interval:    time.Minute,
		Threshold:   80.0,
		Actions:     []string{"notify"},
	})

	am.AddRule(&AlertRule{
		ID:          "high_memory_usage",
		Name:        "High Memory Usage",
		Description: "Memory usage exceeds threshold",
		Condition:   "memory_usage > 85",
		Level:       "warning",
		Enabled:     true,
		Interval:    time.Minute,
		Threshold:   85.0,
		Actions:     []string{"notify"},
	})

	am.AddRule(&AlertRule{
		ID:          "high_disk_usage",
		Name:        "High Disk Usage",
		Description: "Disk usage exceeds threshold",
		Condition:   "disk_usage > 90",
		Level:       "critical",
		Enabled:     true,
		Interval:    time.Minute,
		Threshold:   90.0,
		Actions:     []string{"notify"},
	})

	// 应用告警规则
	am.AddRule(&AlertRule{
		ID:          "high_error_rate",
		Name:        "High Error Rate",
		Description: "Application error rate exceeds threshold",
		Condition:   "error_rate > 5",
		Level:       "critical",
		Enabled:     true,
		Interval:    time.Minute,
		Threshold:   5.0,
		Actions:     []string{"notify"},
	})

	am.AddRule(&AlertRule{
		ID:          "slow_response_time",
		Name:        "Slow Response Time",
		Description: "Response time exceeds threshold",
		Condition:   "response_time > 1000",
		Level:       "warning",
		Enabled:     true,
		Interval:    time.Minute,
		Threshold:   1000.0,
		Actions:     []string{"notify"},
	})

	// 任务告警规则
	am.AddRule(&AlertRule{
		ID:          "too_many_failed_tasks",
		Name:        "Too Many Failed Tasks",
		Description: "Failed tasks count exceeds threshold",
		Condition:   "failed_tasks > 10",
		Level:       "critical",
		Enabled:     true,
		Interval:    time.Minute * 5,
		Threshold:   10.0,
		Actions:     []string{"notify"},
	})

	log.Printf("Loaded %d default alert rules", len(am.rules))
}