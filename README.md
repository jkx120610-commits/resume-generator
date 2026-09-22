# Resume Generator

一个本地运行的 Windows 简历生成程序。填写个人信息后，可同时生成高清 PNG 和标准 A4 PDF，适合发送、存档或直接打印。

## 下载

Windows 用户可直接下载免安装版本：

- [ResumeGenerator.exe v1.0.0](https://github.com/jkx120610-commits/resume-generator/releases/download/v1.0.0/ResumeGenerator.exe)

## 功能

- 图形化表单，不需要编辑 HTML 或代码
- 基本信息、教育背景、技能特长、联系方式四个简历模块
- 支持上传头像并自动裁剪为圆形
- 校验必填项、手机号码、电子邮箱和技能评分
- 输出 2480 × 3508、300 DPI 的 PNG
- 输出内容一致的单页 A4 PDF
- 所有个人资料仅在本机处理，不上传服务器

## 界面字段

程序启动后包含以下标签页：

1. 基本信息
2. 教育背景
3. 技能特长
4. 联系方式
5. 导出设置

姓名、求职意向和第一段教育经历为必填项；手机号码、电子邮箱与评价内容为空时会提示确认。

## 直接运行

### 环境要求

- Windows 10 或 Windows 11
- Python 3.10 或更高版本

双击 `run.bat`。脚本会检查依赖，缺失时自动安装，然后启动图形界面。

也可以在命令行中运行：

```powershell
py -3 -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "$PWD\src"
py -3 main.py
```

## 生成可执行文件

双击 `build_exe.bat`。构建完成后，程序位于：

```text
dist\ResumeGenerator.exe
```

构建脚本会创建本地 `.venv` 虚拟环境，不会修改系统 Python。

## 运行测试

```powershell
py -3 -m pip install -r requirements.txt
$env:PYTHONPATH = "$PWD\src"
py -3 -m unittest discover -s tests -v
```

测试会生成临时简历文件，验证表单校验、PNG 分辨率、PNG 尺寸和 PDF A4 页面。

## 项目结构

```text
resume-generator/
├─ src/resume_generator/
│  ├─ app.py          # Tkinter 图形界面
│  ├─ generator.py    # PNG 与 PDF 渲染
│  ├─ models.py       # 数据模型
│  └─ validator.py    # 表单校验
├─ tests/
├─ main.py
├─ run.bat
├─ build_exe.bat
└─ requirements.txt
```

## 字体

Windows 版本优先使用系统自带的微软雅黑。Linux 环境需要安装思源黑体；macOS 版本优先使用苹方。
