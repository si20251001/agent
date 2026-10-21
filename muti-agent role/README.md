# 校园食堂服务创新研究网站（实验组）

这是一个可本地运行的研究网站，采用 Python 标准库、SQLite 和原生 HTML/CSS/JavaScript。服务器提供管理员生成一次性邀请码、学生自设密码注册与登录、知情同意、15 次学习活动、工作簿版本记录、AI 对话、私有文件上传、S5/S10/S15 正式成果、问卷及研究管理员后台。

## 任务与问卷依据

按研究者当前决定，`07_experimental_website_prd.md` 是 15 次学习活动、M1–M10 工作簿和成果流程的依据；`08_survey_implementation_spec.md` 是问卷的依据。`session_tasks.json` 将 07 的三周目标编排为 15 次活动，任务版本为 `07-v1`。后续如调整任务内容，应在正式实验前确定版本并保留变更记录。

`runtime_prompts/` 从 01–04 文档的指定代码块原文提取；`survey_questions.json` 从 08 文档题库原文提取。重新生成可运行 `python3 setup_content.py`，但正式实验开始后应锁定版本并记录哈希。

## 启动

需要 Python 3.9+，无需安装第三方依赖。如果已运行 `scripts/save_local_config.py`，在项目目录执行：

```sh
export ADMIN_PASSWORD='请设置至少 8 位的强密码'
python3 server.py
```

访问 `http://127.0.0.1:8000`，管理员以 `admin` 和设定密码登录，先创建匿名学生账号。管理员初始密码只在首次建库时生效；后续改变环境变量不会重置已有密码。`data/research.sqlite3` 与 `data/uploads/` 保存研究数据，均不应放入公开目录。

若要让其他设备访问，设置 `HOST=0.0.0.0` 并通过支持 HTTPS 的反向代理提供服务，同时设置 `COOKIE_SECURE=1`。服务器本身只提供 HTTP；正式收集数据前需部署 HTTPS、做好访问控制与定期备份。API 兼容常见 `/chat/completions` 格式；密钥只由服务端读取。本站对 DeepSeek 明确设置非思考模式，使固定的 `LLM_TEMPERATURE` 参数生效；正式实验前请冻结此设置。未配置模型时聊天接口明确报错，其他功能仍可使用。

供不同网络参与者访问的云端部署步骤见 [DEPLOY_RENDER.md](DEPLOY_RENDER.md)。

## 数据、角色与问卷

- 实验组 S1–S5 GUIDE、S6–S10 COACH、S11–S15 EVALUATOR；预留的对照组始终 GUIDE。角色只由数据库中的组别与当前 Session 编号决定。
- 每轮请求装载基础身份 Prompt 和一个阶段 Prompt；记录 Prompt SHA-256、模型、请求编号、候选输出、核验结果、最终展示回复与错误。生成回复先经确定性检查与独立语义评审调用，未通过最多重试一次后使用角色对应的保底回复。真实模型的角色区分度仍需预实验和人工复核。
- 问卷在 S2/S4/S6/S8/S12/S14 为 16 题，S5 为 56 题，S10 合并为 73 题，S15 为 57 题。草稿保留；正式提交只能一次。PS1/3/5 反向计分，TLX4 保持“很好到很差”原方向；子量表均分与原始答案分开保存。
- S5/S10/S15 关闭前必须有正式 Word/PDF 成果文件；对应节点问卷也必须正式提交。关闭 Session 后才能进入下一次活动。
- 管理后台可按被试查看进度、对话、文件、成果、问卷均分，导出对话、问卷长表/宽表、量表得分、题目字典、工作簿版本和日志 CSV。

## 研究管理员操作

后台可分别生成实验组和对照组的一次性邀请码，参与者凭码自行设置密码并获得匿名编号；也可由管理员直接创建账号、重置密码、停用账号、查看逐人记录与导出数据。邀请码仅生成时显示明文，数据库只存哈希。人工调整进度必须填写原因，操作写入审计日志。请安全发放邀请码，不收集真实姓名或学号。

数据库初始化脚本为 `migrations/001_initial.sql`。定期备份时，使用 SQLite 的备份 API 或在停服后复制数据库文件，并同时备份 `data/uploads/`；不要只复制数据库而遗漏附件。

## 本地验收

```sh
MOCK_LLM=1 ADMIN_PASSWORD=test-admin-123 DATA_DIR=/private/tmp/cps-site-test PORT=8001 python3 server.py
```

在另一个终端运行 `python3 tests/integration.py`、`python3 tests/weekly.py` 和 `python3 tests/full_flow.py`。模拟模型只供本地流程验收，不代表真实模型的角色行为或供应商限流表现。

本次已通过：10 名不同学生同时各完成 3 轮模拟聊天（30 轮）、工作簿保存、文件上传、S2 问卷草稿与提交；两名模拟被试完成 S1–S15 的全部问卷和三次周成果。真实 DeepSeek 网站测试完成 GUIDE、COACH、EVALUATOR 三阶段调用及输出核验；本机 10 人同时真实聊天为 10/10 成功。Chrome 测试完成登录、知情同意、聊天回复显示、刷新恢复和历史 Session 回看。正式实验前仍需完成角色行为预实验、云端真实模型并发实测与 HTTPS 部署。

公网部署准备新增验证：一次性邀请码注册、重复邀请码拒绝、学生无法调用管理员接口、登录失败限制、每人聊天频率限制、重新登录恢复聊天、备份归档及数据库完整性、重复初始化不清空数据。备份脚本见 `scripts/backup_data.py`；云端操作见 `DEPLOY_RENDER.md`。

## DeepSeek 真实模型联调

在**已经设置 `LLM_API_KEY` 的同一个终端**运行下列命令；脚本不会打印或保存密钥：

```sh
export LLM_BASE_URL='https://api.deepseek.com/v1'
export LLM_MODEL='deepseek-flash'
export LLM_THINKING='disabled'
python3 tests/live_model_smoke.py
```

脚本调用一次生成与一次输出核验，把结果写入被忽略的 `data/llm_smoke_report.json`。该报告只含模拟提问与模型回复，可供研究者复核。网页服务器需要从环境变量或本机私有配置读取相同的模型设置。DeepSeek 官方 API 支持 `deepseek-flash` 与 `/chat/completions`；`/v1/chat/completions` 已用无密钥请求确认存在（返回 401）。

### Codex 或其他终端看不到 API Key 时

在**已经设置 `LLM_API_KEY` 的 Mac 终端**运行一次：

```sh
python3 scripts/save_local_config.py
```

脚本把密钥和 DeepSeek 服务配置写入 `data/private_config.json`，文件权限为 `0600`，不打印密钥；`data/` 已被 Git 忽略。服务端优先使用运行进程的环境变量，缺失时才加载此本机私有配置。隔离测试库可通过 `LLM_CONFIG_FILE` 指向该文件，无需复制密钥。该文件不要上传、分享或放进任何公开备份；需要撤销时删除该文件并轮换密钥。
