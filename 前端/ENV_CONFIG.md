# 环境配置说明

前端现在支持从环境变量加载后端API地址。

## 配置方法

1. 创建 `.env.local` 文件（不会被提交到Git）：
```bash
# 在前端目录下创建 .env.local 文件
echo "VITE_BACKEND_URL=http://localhost:23456" > .env.local
```

2. 或者在运行时设置环境变量：
```bash
# Linux/macOS
VITE_BACKEND_URL=http://10.96.186.44:23456 npm run dev

# Windows
set VITE_BACKEND_URL=http://10.96.186.44:23456
npm run dev
```

## 可用配置

- `VITE_BACKEND_URL`: 后端API地址，默认为 `http://localhost:23456`

## 示例配置

```bash
# 本地开发
VITE_BACKEND_URL=http://localhost:23456

# 远程服务器
VITE_BACKEND_URL=http://your-server.com:23456

# 网络地址
VITE_BACKEND_URL=http://192.168.1.100:23456
```
