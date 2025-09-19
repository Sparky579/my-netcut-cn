# my-netcut

基于 Flask + SQLite + Vue3 的在线剪贴板与文件分享（仿 netcut.cn 的路由隔离）。默认后端监听 23456 端口，前端使用 Vite。

## 功能摘要
- 路由隔离：`/:channel` 访问不同剪贴板
- 文本编辑：Ctrl+S 或按钮保存；设置过期时间、可设/清除密码
- 文件上传：拖拽或选择，多文件；按频道鉴权与过期清理；下载/删除
- 访问密钥：首次自动生成并仅展示一次；浏览器持久保存；可旋转生成新密钥
- 仪表盘：查看含文件的频道及占用大小、总体占用

## 目录
- 后端：`后端/`（Flask）
- 前端：`前端/`（Vue3 + Vite）

## 启动后端（23456）
```bash
cd /home/chengsizhe/codes/my-netcut/后端
./run.sh
```
首次启动会在终端打印“First master key generated”，复制该密钥用于前端登录。此后不会再次显示。

## 启动前端（开发模式）
```bash
cd /home/chengsizhe/codes/my-netcut/前端
npm run dev
```
打开浏览器访问 `http://localhost:5173/`。

## 生产部署（示意）
- 使用 `gunicorn`/`uwsgi` 启动 Flask 应用，反代到 `:23456`
- 前端 `npm run build` 后，将 `dist/` 交由静态服务器（Nginx）托管，并配置 `/api` 代理到后端

## 注意
- 过期清理在 API 调用中按需执行，也可手动 POST `/api/cleanup`（需密钥）
- 上传目录：`后端/uploads/`
