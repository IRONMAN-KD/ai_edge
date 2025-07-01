package services

import (
	"errors"
	"time"

	"ai-edge/ai-edge/ai-edge/go-platform/internal/config"
	"ai-edge/ai-edge/ai-edge/go-platform/internal/models"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

// AuthService 认证服务接口
type AuthService interface {
	Login(username, password string) (string, *models.User, error)
	ValidateToken(tokenString string) (*Claims, error)
	RefreshToken(tokenString string) (string, error)
}

// Claims JWT声明
type Claims struct {
	UserID   uint   `json:"user_id"`
	Username string `json:"username"`
	Role     string `json:"role"`
	jwt.RegisteredClaims
}

type authService struct {
	db     *gorm.DB
	jwtCfg config.JWTConfig
}

// NewAuthService 创建认证服务实例
func NewAuthService(db *gorm.DB, jwtCfg config.JWTConfig) AuthService {
	return &authService{
		db:     db,
		jwtCfg: jwtCfg,
	}
}

// Login 用户登录
func (s *authService) Login(username, password string) (string, *models.User, error) {
	// 查找用户
	var user models.User
	if err := s.db.Where("username = ? AND is_active = ?", username, true).First(&user).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return "", nil, errors.New("invalid username or password")
		}
		return "", nil, err
	}

	// 验证密码
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(password)); err != nil {
		return "", nil, errors.New("invalid username or password")
	}

	// 生成JWT token
	token, err := s.generateToken(&user)
	if err != nil {
		return "", nil, err
	}

	return token, &user, nil
}

// ValidateToken 验证JWT token
func (s *authService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		return []byte(s.jwtCfg.Secret), nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("invalid token")
}

// RefreshToken 刷新JWT token
func (s *authService) RefreshToken(tokenString string) (string, error) {
	claims, err := s.ValidateToken(tokenString)
	if err != nil {
		return "", err
	}

	// 检查用户是否仍然有效
	var user models.User
	if err := s.db.Where("id = ? AND is_active = ?", claims.UserID, true).First(&user).Error; err != nil {
		return "", errors.New("user not found or inactive")
	}

	// 生成新token
	return s.generateToken(&user)
}

// generateToken 生成JWT token
func (s *authService) generateToken(user *models.User) (string, error) {
	expirationTime := time.Now().Add(time.Duration(s.jwtCfg.ExpireTime) * time.Hour)

	claims := &Claims{
		UserID:   user.ID,
		Username: user.Username,
		Role:     user.Role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(expirationTime),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    "ai-edge",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(s.jwtCfg.Secret))
}