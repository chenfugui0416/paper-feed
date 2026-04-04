# Paper-Feed: 自动化文献精准筛选与推送系统

[![GitHub Actions](https://img.shields.io/badge/Actions-Automated-blue.svg)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### 系统概述
本工具是一个基于 GitHub Actions 的全自动文献监测系统。它旨在解决科研工作中的信息筛选效率问题，功能逻辑如下：
1.  **抓取**：定时从指定的期刊 RSS 源获取最新发表的论文。
2.  **筛选**：根据预设的关键词逻辑（支持 `AND` 组合）对标题和摘要进行匹配。
3.  **分发**：将命中的论文重组为标准化的 RSS 订阅源，供 Zotero 等阅读器订阅。

---

## 🛠 功能特性

*   **全自动运行**：无需服务器，利用 GitHub Actions 每 6 小时自动执行一次检索。
*   **多维度检索**：支持简单的关键词匹配及 `Keyword A AND Keyword B` 的组合逻辑检索。
*   **数据清洗**：内置 XML 字符清洗程序，自动移除非法字符，确保订阅源的兼容性与稳定性。
*   **隐私保护**：支持通过 GitHub Secrets 注入配置，隐藏用户的研究领域与关注列表。
*   **多订阅输出**：除旧版总订阅 `filtered_feed.xml` 外，还会生成 `AI核心`、`热点追踪`、`创新交叉` 3 个独立 RSS。
*   **重点标记**：高优先级论文会在分类订阅标题前显示 `【精选S】` 或 `【精选A】`。
*   **通用兼容**：生成的 RSS 遵循 RSS 2.0 标准，适配 Zotero 和其他主流 RSS 阅读器。

---

## 🚀 部署流程

### 1. 初始化项目
1.  点击本页面右上角的 **Fork**，将仓库复制到你的账号下。
2.  在你的仓库中，删除根目录下的 `filtered_feed.xml` 文件（清除示例数据）。

### 2. 配置参数
提供两种配置方式，**涉及未发表 Idea 或敏感方向建议使用方式 B**。

#### 方式 A：文件配置（公开可见）
直接编辑仓库中的以下文件：
*   `journals.dat`：填入期刊 RSS 链接，一行一个。
*   `keywords.dat`：填入筛选关键词，一行一个。
    *   示例：`Perovskite AND Stability`

#### 方式 B：环境变量配置（私密不可见）
1.  进入仓库 **Settings** -> **Secrets and variables** -> **Actions**。
2.  点击 **New repository secret** 添加以下两个变量：
    *   **Name**: `RSS_JOURNALS` | **Secret**: 填入期刊链接（换行分隔）。
    *   **Name**: `RSS_KEYWORDS` | **Secret**: 填入关键词（换行分隔）。

### 3. 启动服务
1.  **配置 Pages**：
    *   进入 **Settings** -> **Pages**。
    *   **Build and deployment** 下，Source 选择 `Deploy from a branch`。
    *   Branch 选择 `main` 分支的 `/(root)` 目录。
    *   点击 **Save**。
2.  **激活 Workflow**：
    *   进入 **Actions** 页面。
    *   若提示 "Workflows aren't being run..."，点击绿色按钮 **I understand my workflows, go ahead and enable them**。
    *   选中左侧 **Auto RSS Fetch** -> **Run workflow** 手动触发首次运行。

---

## 📈 客户端接入 (以 Zotero 为例)

当前仓库的可用订阅地址如下：

- 论文总订阅（兼容旧订阅）：
  `https://chenfugui0416.github.io/paper-feed/filtered_feed.xml`
- AI核心：
  `https://chenfugui0416.github.io/paper-feed/feeds/ai_core.xml`
- 热点追踪：
  `https://chenfugui0416.github.io/paper-feed/feeds/hot_now.xml`
- 创新交叉：
  `https://chenfugui0416.github.io/paper-feed/feeds/innovation_cross.xml`

如果你 fork 到自己的账号，请将上面的域名替换为：
`https://{你的GitHub用户名}.github.io/{仓库名}/...`

1.  **选择订阅方式**：
    *   想保留原有体验：订阅 `filtered_feed.xml`
    *   想在 Zotero 里分方向阅读：分别添加 3 个分类订阅
2.  **添加订阅**：
    *   Zotero 菜单栏：`文件` -> `新建文献库` -> `新建订阅` -> `从网址`。
    *   粘贴任一上述链接。
3.  **设置同步频率**：
    *   建议在 Zotero 订阅设置中将更新时间设为 **6小时** 或更短，以匹配后端的更新频率。

---

## 📖 期刊显示名称映射

Zotero 列表中的「出版物」列默认显示期刊的正式缩写（如 `JACS`、`PRB`、`Nat. Commun.`），标题列也会自动去除来源标注前缀（如 `[Journal of the American Chemical Society: Latest Articles (ACS Publications)] [ASAP]`）。

此功能由 `journal_map.py` 实现，**无需修改主程序**即可扩展。

### 新增期刊映射

在 `journal_map.py` 的 `JOURNAL_MAP` 列表末尾添加一条记录：

```python
{"prefix": "RSS 标题中方括号内的原始文字", "abbr": "期刊标准缩写"},
```

**如何获取 prefix？**

运行一次后，在生成的 `filtered_feed.xml` 中找任意一条该期刊的条目，`<author>` 标签内的文字即为对应的 prefix（在映射生效前，author 字段存储的就是 RSS 频道标题原文）。

**示例：**

```python
# 在 JOURNAL_MAP 列表末尾追加：
{"prefix": "ACS Catalysis: Latest Articles (ACS Publications)", "abbr": "ACS Catal."},
{"prefix": "Wiley: Chemistry of Materials: Table of Contents",  "abbr": "Chem. Mater."},
```

提交更改后，下次 GitHub Actions 运行时自动生效。

---

## ⚠️ 维护说明

1.  **关键词优化**：若订阅源中无关论文过多，请检查 `keywords.dat` 是否过于宽泛；若漏掉重要论文，请检查是否拼写错误或逻辑过严。
2.  **活跃度维持**：GitHub 可能会暂停长期无代码提交仓库的 Actions 定时任务。若发现停止更新，请进入 Actions 页面手动启用或提交一次空的 Commit。(真的吗，AI说的我也不知道)
3.  **解析失败**：部分期刊 RSS 格式不规范。若遇到特定期刊抓取失败，请检查其 RSS XML 结构的合法性。

## 友情链接

`https://linux.do/`
