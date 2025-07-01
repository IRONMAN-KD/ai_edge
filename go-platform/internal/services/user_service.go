package services

import (
	"errors"
	"fmt"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"

	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

// UserService 用户服务接口
type UserService interface {
	Create(user *models.User) error
	GetByID(id uint) (*models.User, error)
	GetByUsername(username string) (*models.User, error)
	GetByEmail(email string) (*models.User, error)
	Update(user *models.User) error
	Delete(id uint) error
	List(offset, limit int) ([]*models.User, int64, error)
	ChangePassword(userID uint, oldPassword, newPassword string) error
}

type userService struct {
	db *gorm.DB
}

// NewUserService 创建用户服务实例
func NewUserService(db *gorm.DB) UserService {
	return &userService{db: db}
}

// Create 创建用户
func (s *userService) Create(user *models.User) error {
	// 检查用户名是否已存在
	var existingUser models.User
	if err := s.db.Where("username = ?", user.Username).First(&existingUser).Error; err == nil {
		return errors.New("username already exists")
	}

	// 检查邮箱是否已存在
	if user.Email != "" {
		if err := s.db.Where("email = ?", user.Email).First(&existingUser).Error; err == nil {
			return errors.New("email already exists")
		}
	}

	// 加密密码
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}
	user.Password = string(hashedPassword)

	// 设置默认角色
	if user.Role == "" {
		user.Role = "user"
	}

	return s.db.Create(user).Error
}

// GetByID 根据ID获取用户
func (s *userService) GetByID(id uint) (*models.User, error) {
	var user models.User
	if err := s.db.First(&user, id).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

// GetByUsername 根据用户名获取用户
func (s *userService) GetByUsername(username string) (*models.User, error) {
	var user models.User
	if err := s.db.Where("username = ?", username).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

// GetByEmail 根据邮箱获取用户
func (s *userService) GetByEmail(email string) (*models.User, error) {
	var user models.User
	if err := s.db.Where("email = ?", email).First(&user).Error; err != nil {
		return nil, err
	}
	return &user, nil
}

// Update 更新用户
func (s *userService) Update(user *models.User) error {
	return s.db.Save(user).Error
}

// Delete 删除用户
func (s *userService) Delete(id uint) error {
	return s.db.Delete(&models.User{}, id).Error
}

// List 获取用户列表
func (s *userService) List(offset, limit int) ([]*models.User, int64, error) {
	var users []*models.User
	var total int64

	// 获取总数
	if err := s.db.Model(&models.User{}).Count(&total).Error; err != nil {
		return nil, 0, err
	}

	// 获取分页数据
	if err := s.db.Offset(offset).Limit(limit).Find(&users).Error; err != nil {
		return nil, 0, err
	}

	return users, total, nil
}

// ChangePassword 修改密码
func (s *userService) ChangePassword(userID uint, oldPassword, newPassword string) error {
	// 获取用户
	user, err := s.GetByID(userID)
	if err != nil {
		return err
	}

	// 验证旧密码
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(oldPassword)); err != nil {
		return errors.New("old password is incorrect")
	}

	// 加密新密码
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash new password: %w", err)
	}

	// 更新密码
	return s.db.Model(user).Update("password", string(hashedPassword)).Error
}