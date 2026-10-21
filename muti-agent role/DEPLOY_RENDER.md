# Render 云端部署操作指南

本项目是一个 Python HTTP 服务，使用 SQLite 保存账号、对话、问卷与进度，并将上传文件保存在私有目录。推荐 Render 的**付费 Web Service + 持久磁盘**：现有 `render.yaml` 可一次声明服务、环境变量与磁盘；Render 提供 `*.onrender.com` HTTPS 地址，Mac 关机后仍由云端运行。Railway 也支持持久卷和平台域名，但需要在控制台分别配置服务、卷、备份和域名；当前项目已有 Render 蓝图，迁移改动更少。本实验配置为单实例处理 10 人并发；本机真实 DeepSeek 测试已通过，云端仍须复测。

Render 配置：新加坡区域、`1c-2g` 计算方案、1 个实例、10 GB 磁盘挂载到 `/var/data`。该配置会产生费用；创建服务前以 Render 控制台显示的实时价格为准。新加坡网址在中国大陆的访问稳定性需要实测。

## 1. 建立私有代码仓库

1. 注册 GitHub 和 Render 账号，并安装 GitHub Desktop。
2. 在 GitHub Desktop 选择 **File → Add Local Repository**，定位到 `~/Desktop/muti-agent role`。若提示该文件夹还不是 Git 仓库，选择在此处创建本地仓库；确认仓库位置仍是该项目目录。
3. 在 **Changes** 列表逐项检查：不得出现 `data/`、`private_config.json`、`.env`、SQLite 数据库、上传文件、备份包或参与者资料。项目的 `.gitignore` 已排除这些路径。若出现任何敏感文件，停止发布并检查忽略规则。
4. 提交代码，在 GitHub Desktop 点击 **Publish repository**，确认 **Keep this code private** 已勾选。不要把私有仓库改为 Public。

运行网站所需的核心文件是 `server.py`、`web/`、`migrations/`、`runtime_prompts/`、`session_tasks.json`、`survey_questions.json`、`.python-version` 和 `render.yaml`。本机 `data/private_config.json` 不应上传；云端使用平台环境变量读取 DeepSeek Key。本机测试数据也不会自动迁移。

## 2. 在 Render 创建服务

1. 打开 [Render Dashboard](https://dashboard.render.com/)，点击 **New +** → **Blueprint**。
2. 授权 Render 访问刚建的**私有仓库**，选择该仓库。Render 会读取根目录的 `render.yaml`。
3. 检查蓝图显示的服务：`canteen-cps-study`、区域 **Singapore**、计算方案 **1c-2g**、磁盘 **study-data 10 GB** 且挂载路径为 `/var/data`。确认这是付费资源后继续。
4. 在蓝图提示的私密环境变量输入框分别填写：
   - `ADMIN_PASSWORD`：新设管理员强密码，建议至少 12 位，勿沿用测试密码。
   - `LLM_API_KEY`：DeepSeek API Key。只在 Render 的私密环境变量输入框粘贴，不放到仓库或前端。
5. 点击 **Apply / Deploy Blueprint**，等待部署状态变为 **Live**。从服务页面复制 `https://…onrender.com` 网址。平台提供 HTTPS，无需先购买域名。

蓝图已经设置：`HOST=0.0.0.0`、`DATA_DIR=/var/data`、`COOKIE_SECURE=1`、`DEPLOYMENT_MODE=production`、DeepSeek 地址与固定模型标识、固定生成参数、聊天频率上限，以及关闭自动部署。Render 自动提供 `PORT`，无需手动填写。若以后更改 `ADMIN_PASSWORD` 环境变量，**不会重置已存在管理员的密码**。

## 3. 公网验收

1. 用 HTTPS 网址打开首页，以 `admin` 和新密码登录。
2. 在管理员后台生成实验组**一次性邀请码**，立即下载 CSV 并安全保存。每个邀请码只可使用一次，服务器只保存哈希，不会再次展示明文。
3. 用无痕浏览器或另一台设备打开网站，输入邀请码、设置密码，记下系统分配的匿名编号。以该编号登录并完成知情同意。
4. 做一轮真实 DeepSeek 对话；刷新、退出并重新登录，确认聊天记录仍在。测试工作簿、问卷草稿、文件上传和管理员导出。再重启服务，确认记录仍在。
5. 用中国大陆的手机流量及另一种网络测试访问和响应速度。正式实验前执行至少 10 个测试账号的真实模型并发测试，并核对 S5→S6、S10→S11 的角色行为与周末问卷。

角色按**已授权 Session 编号**切换：实验组 S1–S5 GUIDE、S6–S10 COACH、S11–S15 EVALUATOR；不会在单次活动中途因日历时间到达而切换。这遵循 05 和 07 号实验规范。

## 4. 数据持久化与备份

`/var/data/research.sqlite3` 保存账号、进度、对话、问卷与文件索引；`/var/data/uploads/` 保存上传文件。数据库初始化仅执行 `CREATE TABLE IF NOT EXISTS`，服务重启或重新部署不会清空记录。Render 持久磁盘仅供一个实例访问，因此蓝图固定为单实例；不要删除磁盘、改挂载路径或改 `DATA_DIR`。正式实验期间不要手动部署未经验证的新版本。

Render 的磁盘快照是额外恢复手段，**不可替代 SQLite 一致性备份**。研究管理员每天在 Render 服务的 **Shell** 页面运行（把日期换成当天日期）：

```sh
python3 scripts/backup_data.py --data-dir /var/data --output /var/data/study-backup-YYYYMMDD.tar.gz
```

脚本使用 SQLite Backup API，验证备份库完整性，并只打包数据库引用的上传文件；它不会打包 API Key 或 `private_config.json`。随后按 [Render 的 SCP 文件传输指南](https://render.com/docs/disks#transferring-files)将备份下载到受保护的校外位置，确认下载文件后删除云端旧备份以控制磁盘用量。备份包包含研究数据，须限制访问。至少做一次恢复演练。仅导出 CSV 无法恢复上传文件。

## 5. 尚需完成的正式实验验收

- 云端 Render 实例上的 10 人真实 DeepSeek 并发与供应商限流测试；本机真实模型 10/10 已通过。
- 中国大陆不同网络访问测试；云端模型出口能否稳定连接 DeepSeek。
- 角色行为预实验、问卷和任务版本冻结、备份下载及恢复演练。

平台依据：[Render Blueprint](https://render.com/docs/blueprint-spec)、[Web Services / HTTPS](https://render.com/docs/web-services)、[持久磁盘](https://render.com/docs/disks)、[Railway Volumes](https://docs.railway.com/volumes)、[Railway 公网域名](https://docs.railway.com/networking/public-networking)。
