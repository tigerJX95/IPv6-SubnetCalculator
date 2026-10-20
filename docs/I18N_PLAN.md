# V1.7 国际化实现 / Internationalization Implementation

## 已实现 / Implemented

同一 EXE 内置简体中文与英语，地球菜单提供“简体中文 / English”。右上角顺序为语言、主题、关于。即时切换，保存 appearance/language 偏好，下次恢复；无效偏好回退简体中文。界面标题按语言显示，EXE 与仓库继续使用 IPv6SubnetCalculator 名称。

页面、工具提示、错误、状态、表头、标准弹窗及离线帮助覆盖双语。已打开的关于窗口保留标签、许可选择及阅读位置；许可原文不改。语言切换不重建页面、不调用业务计算、不重置模型，不触发组合框选择事件，因而保留结果、分页、选择、定位及规划状态。后台完成消息在 GUI 展示时使用当前语言。

## 模块 / Modules

- assets/i18n/app_en.ts：自有文本与格式模板，使用 Qt Linguist 维护。
- assets/i18n/app_en.qm：由 Qt lrelease 编译，随 EXE 内置；常规构建无需安装翻译编辑工具。
- assets/qtbase_zh_CN.qm：现有 Qt 中文标准控件资源；英语使用 Qt 原始英文。
- services/language_service.py：QTranslator、QLocale、偏好及切换通知。
- core/localized_text.py：不导入 Qt；文本保留原文和结构化参数，计算及 JSON 始终使用原文。仅展示时由翻译函数生成译文，用户原文作为参数保留，避免按词替换用户数据。
- ui/localized_widgets.py：绑定源文本并更新现有控件属性；可编辑内容不绑定译文。组合框索引／数据与显示文字分离。
- ui/standard_dialogs.py：当前语言的标准弹窗和文件选择器，保留默认安全按钮与用户输入文件名。
- docs/about/USAGE_EN.md 与 LEGAL_EN.md：离线英文说明；许可文件保留原文。

## 维护与验证 / Maintenance and Validation

修改译文后运行 `lrelease assets/i18n/app_en.ts -qm assets/i18n/app_en.qm`，提交 TS 与 QM。Qt Linguist/lrelease 为翻译维护工具，不是运行依赖，不加入 requirements。新增可见文字使用 text(source, *arguments)，保留模板参数，勿把用户字符串作为翻译键或根据译文判断业务分支。表格在切换时只通知表头／展示数据变化，不重置数据。

测试检查源模板与译文占位符、TS/QM 一致、语言偏好及重启恢复、非法偏好、保存失败、语言无关方案、精确整数、错误恢复、已有关于窗口、异步任务及最小窗口。Windows 人工验收、DPI、实际拖放与持续使用结果在完成后记录，不以 Linux offscreen 代替。

V1.7 后续重点为国际化后的布局、翻译完整性和兼容收敛；按实际反馈调整，不为版本数量堆叠功能。


## V1.7 导出国际化 / Export Localization

- `App` 上下文保留界面“序号 → Index”；新增 `Export` 上下文将同一中文源词译为“No.”，并提供“IPv6 Subnet”“IPv6 Subnets”。维护目录时按上下文检查，不能只按源文字去重。
- GUI 线程在任务实际开始时解析导出标签并冻结；即使文件选择期间或导出期间切换语言，也以任务开始时为准。完成提示使用完成时的界面语言。
- 核心写入器不依赖 Qt，默认保留中文兼容；TXT 不添加标题，JSON 不加入语言字段。
- Qt 页签内部滚动按钮的悬停提示需要显式刷新，不能只重译页签标题。

The `Export` context separates file wording (“No.”) from UI wording (“Index”). Resolve labels at actual task start on the GUI thread and pass an immutable snapshot to the Qt-free writer. Completion feedback follows the current interface language. Refresh internal tab-scroll tooltips explicitly; keep TXT and JSON language-independent.
