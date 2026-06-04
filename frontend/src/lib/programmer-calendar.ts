// 程序员黄历词库 —— 摸鱼站私货版
// 用当日日期做种子，挑出固定的「宜 / 忌 / 编程吉位 / 凶位 / 幸运编辑器 / 幸运语言」。
// 不调用第三方接口，永远在线。

export interface ProgrammerAlmanac {
  date: string;        // YYYY-MM-DD
  dos: string[];       // 宜
  donts: string[];     // 忌
  luckyEditor: string;
  unluckyEditor: string;
  luckyLang: string;
  luckyDir: string;    // 编程吉位
  unluckyDir: string;  // 编程凶位
  fortune: string;     // 一句话签文
}

const DOS: string[] = [
  "写单元测试",
  "重构祖传代码",
  "摸鱼",
  "看 B 站新番",
  "喝一杯黑咖啡",
  "早退",
  "在工位假装思考",
  "提 PR",
  "代码 Review",
  "看技术博客",
  "写文档",
  "删冗余代码",
  "升级依赖",
  "和 ChatGPT 聊天",
  "给变量取个好名字",
  "修一个老 bug",
  "逛 GitHub Trending",
  "打开 IDE 关机走人",
  "在群里发表情包",
  "装作在调研技术方案",
  "伸懒腰",
  "吃下午茶",
  "加一行 console.log",
  "研究新框架",
  "写注释",
  "摸黑发版（其实没发）",
  "开个空白文档假装在写方案",
  "远程会议关摄像头",
  "用快捷键",
  "看股市行情",
  "把工位收拾干净",
  "去茶水间续命",
  "假装在画架构图",
  "听一首白噪音",
  "把待办清空一半",
  "把 README 写完整",
  "把 CHANGELOG 补上",
  "把变量名改短",
  "顺手 format 一下",
  "提交一次小步快跑",
  "把 TODO 真的做掉一个",
  "用上新学的快捷键",
  "把屏幕亮度调暗",
  "升级一下 Node 版本",
  "把 lint 警告全清掉",
  "把 console.log 删干净",
  "试一下深色主题",
  "整理一下书签栏",
  "看完一篇 RFC",
  "复盘上周的 bug",
  "整理桌面图标",
  "把 chrome 标签合并",
  "发个朋友圈",
  "拍一下今天的咖啡",
  "晒一下显示器",
  "把外卖订早一点",
  "去散个步",
  "翻翻招聘网站",
  "看看自己的 LeetCode",
  "在群里夸夸同事",
  "申请远程办公一天",
  "听播客",
  "把椅子调高一点",
  "做个深呼吸",
  "把水喝完",
  "买个机械键盘",
  "把鼠标垫换新的",
  "买杯奶茶犒劳自己",
  "看一集纪录片",
  "默默给 PR 点赞",
  "假装在做代码评审",
  "假装在 debug",
  "把开发分支推一下",
  "把 main 拉到最新",
  "rebase 一下",
  "把 stash 翻出来看看",
  "用一次新工具",
  "学一个 vim 命令",
  "学一个 git 命令",
  "学一个 SQL 函数",
  "把 dotfiles 同步一下",
  "备份一次代码",
  "记一笔技术日记",
  "回答一个 issue",
  "关掉提示音",
  "关闭非必要通知",
  "认真听一次站会",
  "认真吃一顿午饭",
  "下楼晒太阳",
  "和同事闲聊",
  "找产品对一下需求",
  "把疑问列个清单",
];

const DONTS: string[] = [
  "周五发版",
  "在主分支直接 push",
  "删数据库",
  "force push",
  "和产品经理硬刚",
  "承诺工期",
  "接需求",
  "开会",
  "重启服务",
  "动祖传代码",
  "改线上配置",
  "加班",
  "未测试就合并",
  "半夜 hotfix",
  "忽略报警邮件",
  "和老板讨论涨薪",
  "打开钉钉",
  "回复\"在的\"",
  "试用新 IDE 主题",
  "无脑复制 Stack Overflow",
  "装作很忙",
  "猜测 bug 原因",
  "问 DBA 借权限",
  "清缓存",
  "删 node_modules 重装",
  "在文档里写 TODO",
  "打开任务管理工具",
  "和测试争执",
  "周一早会发言",
  "摸到忘了打卡",
  "在群里发\"好的\"",
  "答应今天能做完",
  "改 prod 数据库 schema",
  "在 main 上调试",
  "凌晨改密码",
  "凌晨改 DNS",
  "和运维抢权限",
  "随手 kill -9",
  "随手 rm -rf",
  "随手 git reset --hard",
  "用 sudo 解决一切",
  "在生产环境 print 日志",
  "在群里 @所有人",
  "回老板\"马上好\"",
  "回测试\"在我这没问题\"",
  "回产品\"这是个 feature\"",
  "周五下午合并大 PR",
  "周末手动跑脚本",
  "节前发版",
  "节后立刻发版",
  "节前接需求",
  "和前端争边距",
  "和后端争字段",
  "和设计争颜色",
  "和老板谈情怀",
  "升级核心依赖大版本",
  "随手覆盖配置",
  "随手 push 二进制文件",
  "把 .env 提交了",
  "把 token 写在代码里",
  "把账号密码写在群里",
  "在公网开 root 端口",
  "凭印象写正则",
  "凭印象写时区",
  "凭印象写编码",
  "盲改时间格式",
  "盲改字符集",
  "盲改字段类型",
  "随手关报警",
  "随手 mute 群",
  "把 CI 跳过",
  "用 --no-verify",
  "用 --force",
  "随便点 \"忽略\"",
  "在客户面前演示新功能",
  "向产品保证零 bug",
  "向 QA 保证全覆盖",
  "向老板演示半成品",
  "拍胸脯估工时",
  "拍胸脯说没问题",
  "假装看懂了 Kafka",
  "假装看懂了 K8s",
  "假装看懂了 Webpack 配置",
  "硬看 Webpack 报错",
  "硬看 Gradle 报错",
  "在 Excel 里改线上数据",
  "用 root 跑测试脚本",
  "把日志关掉",
  "把监控关掉",
  "下班前最后一次提交",
  "下班前最后一次发版",
  "下班前最后一次改配置",
];

const EDITORS: string[] = [
  "VSCode", "Vim", "Neovim", "JetBrains 全家桶", "Emacs",
  "Cursor", "Sublime Text", "Notepad++", "记事本", "nano",
];

const LANGS: string[] = [
  "TypeScript", "Python", "Go", "Rust", "Java",
  "JavaScript", "C++", "Kotlin", "PHP", "Bash",
  "SQL", "Lua", "Ruby", "Swift",
];

const DIRS: string[] = [
  "工位正北 · 茶水间方向",
  "工位东南 · 打印机方向",
  "工位正南 · 厕所方向",
  "工位西北 · 老板工位方向",
  "工位正西 · 窗户方向",
  "工位东北 · 前台方向",
  "显示器后方",
  "键盘正前方",
];

const FORTUNES: string[] = [
  "今日合并必过，build 必绿。",
  "今日 bug 自愈，不查也行。",
  "今日代码一气呵成，注释靠脑补。",
  "今日适合躺平，编译器替你思考。",
  "今日会议必延期，宜伪装在听。",
  "今日产品需求清晰，概率为零。",
  "今日上线必出事，宜请假。",
  "今日心情如 404，找不到方向。",
  "今日运势 99%，剩 1% 在 CI 里挂着。",
  "今日宜静默，群里别冒头。",
  "今日适合摸鱼，老板出差。",
  "今日代码与你心意相通，一次跑通。",
];

// 简单字符串哈希（FNV-1a 简化版）
function hashSeed(seed: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < seed.length; i += 1) {
    h ^= seed.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return h >>> 0;
}

function pick<T>(arr: T[], seed: number): T {
  return arr[seed % arr.length];
}

function pickN<T>(arr: T[], n: number, seed: number): T[] {
  const copy = arr.slice();
  const out: T[] = [];
  let s = seed;
  for (let i = 0; i < n && copy.length > 0; i += 1) {
    s = (s * 1664525 + 1013904223) >>> 0;
    const idx = s % copy.length;
    out.push(copy[idx]);
    copy.splice(idx, 1);
  }
  return out;
}

export function getProgrammerAlmanac(date: Date = new Date()): ProgrammerAlmanac {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const dateStr = `${y}-${m}-${d}`;
  const baseSeed = hashSeed(dateStr);

  const dos = pickN(DOS, 3, baseSeed);
  const donts = pickN(DONTS, 3, hashSeed(dateStr + "#donts"));
  const luckyEditor = pick(EDITORS, hashSeed(dateStr + "#editor+"));
  let unluckyEditor = pick(EDITORS, hashSeed(dateStr + "#editor-"));
  if (unluckyEditor === luckyEditor) {
    unluckyEditor = EDITORS[(EDITORS.indexOf(luckyEditor) + 1) % EDITORS.length];
  }
  const luckyLang = pick(LANGS, hashSeed(dateStr + "#lang"));
  const [luckyDir, unluckyDir] = pickN(DIRS, 2, hashSeed(dateStr + "#dir"));
  const fortune = pick(FORTUNES, hashSeed(dateStr + "#fortune"));

  return {
    date: dateStr,
    dos,
    donts,
    luckyEditor,
    unluckyEditor,
    luckyLang,
    luckyDir,
    unluckyDir,
    fortune,
  };
}
