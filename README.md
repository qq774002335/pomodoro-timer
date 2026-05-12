# Pomodoro Timer

基于 Python tkinter 的番茄钟桌面应用。

## 功能

- 25 分钟工作 / 5 分钟短休息 / 15 分钟长休息
- 每 4 个番茄后自动进入长休息
- 计时结束声音提醒
- 自动开始下一阶段（可关闭）
- 窗口始终置顶（可关闭）

## 快捷键

| 键 | 功能 |
|----|------|
| `Space` | 开始 / 暂停 |
| `R` | 重置当前阶段 |
| `S` | 跳过当前阶段 |
| `T` | 切换置顶 |

## 运行

```
python pomodoro.py
```

## 打包为 exe

```
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name Pomodoro pomodoro.py
```

生成文件在 `dist/Pomodoro.exe`。
