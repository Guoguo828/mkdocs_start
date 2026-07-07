# Glyphs概念讲解

## Glyphs基础定义与核心职责

# 幻灯片内容完整翻译+讲解：Glyphs（字形/图元类，排版渲染核心概念）
## 一、原文逐句翻译
### 1. 基础定义
> An abstract class for all objects that can appear in a document structure
**翻译**：Glyphs 是一个**抽象基类**，文档结构里出现的所有可视元素，都继承自它。

> Subclasses define both primitive graphical elements (characters, images, ...) and structural elements (rows, columns, ...)
**翻译**：它的子类分为两大类：
1. 基础图形元素：文字字符、图片等最小可视单元
2. 布局结构元素：行、列、段落、容器这类负责排版分组的容器

### 2. Glyph 的三大核心职责（Glyphs’ responsibilities）
1. **Know how to draw themselves**
   知道如何把自己绘制到画布上（自带渲染绘制逻辑）
2. **Know what space they occupy**
   能计算、上报自身占用的尺寸/边界盒（排版布局的基础）
3. **Know their children and parent**
   持有父子节点引用，构成树形文档结构（DOM/排版树的基础）

## 二、通俗解释这页在讲什么
这是**文字排版、PDF/浏览器渲染、桌面文档引擎（如Word、LaTeX、浏览器Layout）** 里的经典 `Glyph`（图元/字形）模型：
1. **Glyph 是一切文档可视内容的统一父类**
   不管是一个汉字、一张图片，还是一整行文本、一列表格，在代码里全都是 `Glyph` 的子类对象，统一一套接口管理。
2. **它把两种东西统一抽象了**
   - 叶子节点：单个字符、图片、图标（最小渲染单元）
   - 容器节点：行、列、段落、表格单元格（用来分组、控制布局）
3. 所有 Glyph 必须实现三个核心能力：
   - 自绘制：自己管自己怎么画
   - 尺寸测量：排版时引擎要靠它算出自己占多大地方
   - 树形关联：保存父节点、子节点，整份文档就是一棵 Glyph 树

## 三、举个现实例子（浏览器网页渲染）
网页里的每一个元素，在渲染层都会被转成类似 Glyph 的对象：
- 字符「A」→ 基础图形 Glyph
- `<img>` 图片 → 基础图形 Glyph
- `<p>` 段落、`<div>` 容器、表格行/列 → 结构容器 Glyph
渲染引擎遍历这棵树时，会依次：测量每个Glyph尺寸 → 排布位置 → 调用各自的draw方法绘制到屏幕。

## 补充术语
- Glyph：直译「字形」，在排版引擎里广义叫**图元**，代表任意可绘制的文档节点
- Abstract class：抽象类，只定义通用接口，不能直接实例化，必须写子类实现
- Document structure：文档树形结构（类似DOM树、排版树）

## Formatting排版与算法封装

# 两张幻灯片完整翻译+串联讲解
## 第一张：Formatting（排版/格式化，排版引擎做什么）
### 原文逐句翻译
1. **Lexi must break text into lines, lines into columns, ...**
Lexi（这套文档系统的名字）必须完成文本拆分排版：把长文本拆成一行一行，再把行分到分栏里，层层划分布局。
> 底层逻辑：一堆字符Glyph是线性的，排版要把它们重新组织成「行Glyph→栏Glyph→页面Glyph」的树形容器结构，就是上一页讲的Glyph树。

2. **Consider user’s high-level desires：**
排版算法要遵从用户设置的高层样式需求：
- Margin widths, indentation, tabulation, …
  页边距、段落首行缩进、制表符对齐、段间距等基础文本样式
- Single/double column
  单栏排版 / 双栏分栏（杂志、论文常用）
- and so on
  还有页眉页脚、行距、对齐方式、图片环绕等所有排版规则

### 通俗总结这一页
**Formatting = 布局规划**
输入：一串纯文字、图片Glyph；
输出：规整好的分层Glyph容器树（行、栏、段落、页面）；
约束：严格遵守用户设置的所有页面、段落、分栏样式参数。

---

## 第二张：Encapsulating the Formatting Algorithm（封装排版算法，软件设计思想）
核心主题：把**排版算法**和**Glyph文档结构**彻底解耦，做到高内聚、低耦合。
### 1. Trade-off between formatting quality and speed
排版存在「美观质量」和「运行速度」的取舍平衡
- User’s demands may changeable
  用户的排版需求是多变的：有人要极速实时预览，有人要极致美观的断行（比如LaTeX高质量排版，但计算慢）；
  所以系统要能切换不同排版算法（快速简易版 / 精细优化版），不能写死一套逻辑。

### 2. Well contained or completely independent of the document structure
排版算法和Glyph文档结构完全隔离、互不侵入，两大好处：
1. **can add new Glyph subclass without modifying the formatting algorithm**
新增一种Glyph（比如新增代码块、公式、流程图Glyph子类），**不用改一行排版代码**。
   原理：所有Glyph统一提供「测量自身占用空间」接口，排版器只调用通用接口，不关心Glyph具体是什么类型。
2. **can add formatting algorithm without modifying Glyphs**
新增一套全新排版规则（比如多栏杂志排版、报纸复杂分栏、手机自适应流式排版），**不用修改任何Glyph类代码**。
   原理：排版逻辑单独封装成独立模块，Glyph只负责提供尺寸、父子关系数据，不绑定任何排版策略。

### 通俗总结这一页的设计目的
1. 分离变化点：
   - Glyph负责「内容与渲染」，稳定少变；
   - Formatting排版算法负责「布局拆分规则」，需求多变；
2. 不用改另一边代码，就能自由扩展内容类型、自由切换排版方案；
3. 同时支持快慢两种排版模式，兼顾预览速度和最终导出美观度。

---

# 三页PPT完整串联逻辑（Glyph → Formatting → 封装排版算法）
1. 底层数据模型：所有文档元素都是Glyph抽象类，分叶子（字、图）和容器（行、栏），自带测量、绘制、父子树形能力；
2. 中间业务流程：Formatting排版模块，读取用户样式参数，把线性Glyph拆分成层级容器树，完成页面布局规划；
3. 上层软件架构：把排版算法单独封装、和Glyph解耦，实现双向自由扩展，同时兼容不同性能/质量的排版策略。

## 举个现实类比（Word/WPS）
- Glyph：单个文字、图片、段落框、表格单元格；
- Formatting：Word里的「自动换行、分栏、缩进、页边距计算」这套布局计算；
- 封装解耦设计：
  1. 新增「思维导图」元素（新Glyph子类），原有分栏、换行逻辑完全不用改动；
  2. 新增「书籍精美排版引擎」，不用修改文字、图片、表格的底层Glyph代码，直接接入新算法即可。

## Compositor排版器与策略模式

# 三张幻灯片完整拆解：Compositor（排版器）+ Composition（排版文档容器）
结合前面讲的 **Glyph 图元**、**Formatting 排版算法**，这页是整套文档引擎的核心分层设计，属于经典**策略模式（Strategy Pattern）**。

## 一、第一张：Compositor 与 Composition 基础定义
### 1. Compositor 类：封装排版算法的载体
> Compositor class is for objects that can encapsulate a formatting algorithm.
翻译：Compositor 是专门用来**封装一套完整排版/格式化算法**的抽象父类。

它对外只暴露两个标准接口，用来控制排版的「对象」和「时机」：
| 职责 | 接口方法 | 作用 |
|------|---------|------|
| What to format（要排版谁） | `void SetComposition(Composition *)` | 绑定要处理的文档容器 Composition，告诉排版器操作哪份文档 |
| When to format（什么时候排版） | `virtual void Compose()` | 触发排版计算的入口函数，子类在这里实现换行、分栏、布局逻辑 |

### 2. Composition 对象（承载所有Glyph的顶层容器）
1. **排版前（未格式化状态）**
> Initially, an unformatted Composition object contains only the visible child Glyphs.
初始时，Composition 里只有**可见叶子Glyph**：单个字符、图片、空格，没有行、列这类容器。
简单理解：就是一串平铺的文字/图片，还没分行分栏。

2. **运行 Compositor 排版后**
> After running a Compositor, it will also contain invisible, structural glyphs that define the format.
调用 `Compose()` 执行排版后，Compositor 会自动生成**不可见的结构容器Glyph**（row行、column栏），插入到 Composition 的树结构里。
这些行、列是纯布局容器，不渲染内容，只用来划分排版层级。

## 二、第二张：结构图直观展示排版后的Glyph树
标题：`Object structure reflecting compositor-directed linebreaking`
翻译：这棵对象树，就是 Compositor 执行**自动换行**后生成的层级结构。

从上到下树形结构：
1. `composition` 顶层容器（持有一个 Compositor 排版器实例）
2. `column` 分栏容器（Compositor 生成的结构Glyph）
3. `row` 文本行容器（Compositor 生成的结构Glyph）
4. 行内部叶子Glyph：字母G/g、空格space、图片图标
- `compositor-generated glyphs`：标注说明 column、row 都是排版算法自动创建出来的，不是用户原始输入。

流程可视化：
原始平铺字符 → Compositor 执行换行分栏 → 插入 row / column 容器 → 形成分层排版树。

## 三、第三张：完整UML类图，讲清类之间依赖、继承关系
### 1. 继承关系（Compositor 策略多态）
`Compositor` 是抽象父类，有多个不同排版策略的子类，各自重写 `Compose()`：
- `SimpleCompositor`：简易快速排版（实时预览用，牺牲美观换速度）
- `ArrayCompositor`：数组流式简单分行
- `TeXCompositor`：专业高质量排版（类似LaTeX精细断行，计算慢、效果精致）

完美对应上一页提到的「排版质量与速度的取舍」：需要哪种排版，就挂载对应的 Compositor 子类，**不用修改Glyph和Composition代码**。

### 2. 类之间关联与调用流程
1. **Composition 继承自 Glyph**
   顶层文档容器本身也是一个特殊Glyph，所以拥有所有Glyph能力：测量尺寸、绘制、`Insert(Glyph, int)` 插入子图元。
2. Composition 持有一个 Compositor 引用
   通过 `SetComposition()` 双向绑定，排版器知道要处理哪个文档。
3. 自动触发排版的逻辑：
   每当我们往文档里插入新字符/图片 `Composition.Insert(g, i)`，内部会自动调用绑定好的 `compositor.Compose()`，实时重新排版整份文档。

### 3. 核心解耦设计亮点（呼应之前封装排版算法的PPT）
1. **新增Glyph子类（如新公式、图表）**：完全不用改任何 Compositor 代码
   Compositor 只依赖Glyph统一接口（测量尺寸、父子节点），不关心Glyph具体类型。
2. **新增排版算法（如新杂志多栏排版）**：只写一个新 Compositor 子类，不用修改Glyph、Composition
   策略模式把多变的排版逻辑抽离成独立一族类，和稳定的文档Glyph模型彻底分离。

# 四、整套知识点串联（完整文档渲染流水线）
1. **底层数据：Glyph**
   所有可视元素统一抽象，分叶子（字、图）、结构容器（行、栏），自带绘制、尺寸测量、父子树形。
2. **顶层载体：Composition**
   整份文档的根Glyph，存放所有原始内容，绑定一个排版器。
3. **排版逻辑层：Compositor（策略）**
   封装所有换行、分栏、缩进、页边距计算算法；多子类实现「快预览 / 精美导出」两种模式。
4. **完整工作流**
   用户输入一串文字图片（平铺Glyph存入Composition）
   → 调用 `Compositor.Compose()`
   → 算法自动拆分文本、生成row/column结构Glyph插入树中
   → 形成分层排版树
   → 渲染引擎递归遍历整棵Glyph树，依次绘制容器背景边框、内部字符图片

# 通俗类比（Word软件）
- `Glyph`：单个汉字、图片、段落框
- `Composition`：整篇Word文档
- `Compositor`：Word的排版引擎
  - `SimpleCompositor`：普通页面实时预览（快速分行）
  - `TeXCompositor`：导出PDF时的精细优化排版（对齐、断行更美观）
- 编辑打字插入文字 → 自动调用Compositor重新计算换行、段落布局 → 页面实时刷新排版。

## MonoGlyph与装饰器模式

# 三张PPT完整拆解：MonoGlyph + 装饰器模式（Decorator Pattern）
## 一、第一张：MonoGlyph 抽象父类
### 逐句翻译+人话解释
1. **Serve as an abstract class for embellishment glyphs.**
MonoGlyph 是**抽象父类**，专门给所有「装饰美化类Glyph」做顶层模板。
- embellishment glyphs = 装饰图元：就是前面讲的 Border（边框）、Scroller（滚动条），用来给内容加额外外观功能。
- abstract class：不能直接 new MonoGlyph，只能写它的子类（Border/Scroller）。

2. **It stores a reference to a component and forwards all requests to it.**
内部只存**唯一一份子组件指针（component）**，收到的所有接口请求（Draw、GetBounds等）默认全部转发给这个内部子对象。
对应之前说的 **single-child 单子包裹**：
MonoGlyph 内部只有一个 `Glyph* component`，没有数组，只能装1个内容；
默认实现里，调用 `Draw()`、测量尺寸时，直接把操作丢给 `component`，自己啥额外事都不干。

3. **Its subclasses reimplement at least one of the forwarding operations.**
它的子类（Border、Scroller）**重写至少一个转发函数**，在转发前后插入自己独有的美化逻辑。
- Border 重写 `Draw()`，先画边框，再转发绘制内部内容；
- Scroller 重写 `Draw()`，先做滚动裁剪，再转发绘制内容，最后画滚动滑块。

### 核心定位
MonoGlyph = 装饰器模式里通用的「装饰器抽象基类」，把“存单个子组件、默认转发所有调用”的公共逻辑抽出来，Border/Scroller 只需要重写自己要增强的方法，不用重复写转发代码。

## 二、第二张：UML类图 + Border执行流程
### 1. UML继承链
```
Glyph（顶层所有图元父类）
   ↑
MonoGlyph（装饰器抽象父类，持有component单子指针，默认转发Draw）
   ├─ Border（边框装饰子类，重写Draw，新增DrawBorder）
   └─ Scroller（滚动条装饰子类，重写Draw）
```
关联线：MonoGlyph 有一条 `component` 指向任意 Glyph，代表它包裹的内部内容。

### 2. Border 的 Draw 执行逻辑
`Border.Draw() { MonoGlyph::draw(); drawBorder(); }`
拆解执行顺序：
1. `MonoGlyph::draw()`：调用父类默认实现，把绘制请求**转发给内部 component**，画出里面的文字/分栏内容；
2. `drawBorder()`：Border 自己新增的方法，在内容画完之后，绘制外围边框线条。
> 也可以反过来：先画边框再转发内容，只是顺序差异，核心是「转发+额外增强逻辑」。

### 3. 对应你之前的嵌套代码
```cpp
Glyph* column = new Column();        // 原始内容（Glyph子类）
Glyph* scroll = new Scroller(column);// Scroller继承MonoGlyph，component=column
Glyph* border = new Border(scroll);  // Border继承MonoGlyph，component=scroll
```
- Scroller、Border 都复用 MonoGlyph 里存 `component`、转发接口的公共代码；
- 各自只重写 Draw，实现专属美化效果，代码无冗余。

## 三、第三张：Decorator Pattern（装饰器模式）定义
### 逐句翻译+串联前面知识点
1. **It captures class and object relationships that support embellishment by transparent enclosure.**
装饰器模式，定义了一套类与对象的关系，通过**透明包裹**的方式给对象增加美化/附加功能。
- transparent enclosure 透明包裹：所有装饰器（Border/Scroller）和原始内容（Row/Column）同属 Glyph，对外接口完全一致，上层代码区分不出有没有被包装；
- 不用继承扩展功能，靠「对象嵌套组合」实现美化。

2. **In decorator pattern, embellishment refers to anything that adds responsibilities to an object.**
在这个模式里，“美化/装饰（embellishment）”泛指**给原有对象新增任意职责**：
- Border 新增职责：绘制边框、扩大内容边界；
- Scroller 新增职责：滚动偏移、内容裁剪、绘制滚动滑块；
原始Column只负责排版文字，不具备这些能力，通过外层装饰器动态附加。

# 整套知识点串联（打通所有PPT）
1. **基础骨架 Glyph**：所有文档元素统一抽象，提供Draw、测量尺寸通用接口；
2. **排版策略 Compositor（策略模式）**：自动生成Row、Column纯排版容器，只处理文字分行分栏，和装饰无关；
3. **装饰器抽象 MonoGlyph**：专门封装“单子包裹、默认转发调用”的公共逻辑；
4. **具体装饰 Border/Scroller（MonoGlyph子类）**：重写接口，叠加边框、滚动条附加功能；
5. **整体是 Decorator 装饰器模式**：用组合嵌套代替类爆炸继承，运行时灵活增删外观装饰，对上层渲染代码完全透明。

# 极简代码示例，直观体现 MonoGlyph 转发逻辑
```cpp
// 抽象装饰父类 MonoGlyph
class MonoGlyph : public Glyph {
protected:
    Glyph* component; // 唯一单子节点
public:
    MonoGlyph(Glyph* c) : component(c) {}

    // 默认全部转发给内部组件
    virtual void Draw() override {
        component->Draw(); 
    }
};

// 边框子类，重写Draw增强
class Border : public MonoGlyph {
public:
    Border(Glyph* c) : MonoGlyph(c) {}

    void Draw() override {
        MonoGlyph::Draw(); // 调用父类，转发绘制内部内容
        DrawBorderLine();  // 自己新增的装饰逻辑
    }
    void DrawBorderLine() { /* 绘制边框 */ }
};
```
这里 `MonoGlyph` 承担了所有公共转发逻辑，Border 只需要加自己独有的边框绘制代码，这就是这三张PPT的核心设计目的。

## 抽象工厂模式与多平台UI

# 整套幻灯片完整讲解：抽象工厂模式（Abstract Factory），解决 Lexi 多平台UI皮肤切换
## 整体背景
Lexi 文档编辑器需要同时兼容 **Motif、Windows、Mac、PM** 多套系统UI外观（Look-and-Feel）：按钮、滚动条、菜单每个系统长得不一样，但功能完全一致。
这套PPT讲用**抽象工厂模式**统一管理不同平台UI控件的创建，实现运行时切换皮肤。

---

## 1. 第一张：Supporting Multiple Look-and-Feel Standards（多皮肤支持目标）
### 三大设计目标
1. 让 Lexi 能适配多种现有系统UI规范（Mac/Windows/Motif）
2. 后续新增一套系统皮肤时，扩展成本极低，不用大面积改代码
3. **程序运行过程中，可以动态切换整套界面风格**（比如软件里点“切换Mac风格”立刻换全部按钮、滚动条样式）

### 两套控件Glyph类分层（产品层级）
1. **abstract 抽象产品类（统一接口）**
`ScrollBar`、`Button`、`Menu`，全部继承顶层 `Glyph`
只定义统一功能接口，不写绘制样式：
- ScrollBar：`ScrollTo(int)` 滚动到指定位置
- Button：`Press()` 点击按下
- Menu：`Popup()` 弹出菜单

2. **concrete 具体产品类（对应各平台样式）**
每个抽象类派生对应系统的实现：
- MotifScrollBar、WinScrollBar、MacScrollBar
- MotifButton、MacButton、PMButton
每个子类重写绘制逻辑，画出对应系统的外观，但对外接口完全一样。

---

## 2. 第二张：Abstracting Object Creation（抽象对象创建的好处）
### 原始硬编码写法（坏方案）
```cpp
ScrollBar sb = new MotifScrollBar();
```
- 问题：代码写死了 Motif 版本滚动条，想换 Mac 皮肤，所有创建控件的代码都要改；
- 运行时无法切换风格，编译时就定死平台。

### 工厂抽象创建的两大优势
1. **消除硬编码，运行时自由选风格**
不直接 new 具体平台控件，统一交给工厂生成，程序跑起来再决定用Mac/Windows/Motif哪套UI。
2. **整套UI一键替换**
只需要更换工厂对象，全局所有按钮、滚动条、菜单全部同步切换风格，不用逐个修改控件创建代码。

---

## 3. 第三张：Factories and Product Classes（工厂UML结构）
### 对比两种创建方式
1. 传统硬编码（耦合严重）
```cpp
ScrollBar sb = new MotifScrollBar();
```
代码直接绑定 Motif 具体类，换皮肤就要全项目搜索替换。

2. 工厂统一创建（解耦）
```cpp
ScrollBar sb = guiFactory.createScrollBar();
```
只调用抽象工厂的通用创建方法，**完全不关心底层是 Mac / Motif / Windows 实现**。

### UML工厂层级（抽象工厂模式核心）
1. **顶层抽象工厂：GUIFactory**
定义一套通用创建接口：
`CreateScrollBar()`、`CreateButton()`、`CreateMenu()`
2. **具体平台工厂（子类）**
- MotifFactory：创建所有 Motif 风格控件
- MacFactory：创建所有 Mac 风格控件
- PMFactory：创建PM系统风格控件
每个工厂内部 new 对应平台的具体控件返回。

### 核心约束：一个工厂 = 一整套配套UI
`MotifFactory` 产出的滚动条、按钮、菜单全是 Motif 风格，不会混搭Mac控件，保证界面风格统一。

---

## 4. 第四张：产品类完整继承树
```
                Glyph（所有图元顶层父类）
       /            |             \
ScrollBar        Button          Menu  【抽象产品，统一接口】
   /|\             /|\            /|\
MotifScrollBar MacScrollBar PMScrollBar 【各平台具体实现】
MotifButton    MacButton    PMButton
MotifMenu      MacMenu      PMMenu
```
- abstract：ScrollBar/Button/Menu，规定控件能干什么；
- concrete：MotifXXX/MacXXX，规定控件长什么样。
所有UI控件本质都是Glyph，和之前排版、装饰器体系完全打通。

---

## 5. 第五张：Building the Factory（工厂三种初始化方式，对应三个Lexi版本迭代）
### 方式1：编译期固定（Lexi v1.0，仅支持Motif）
```cpp
GUIFactory guiFactory = new MotifFactory();
```
编译代码写死工厂，只能用Motif皮肤，无法切换。

### 方式2：程序启动时读取配置切换（Lexi v2.0）
软件打开时读取配置文件里的风格参数，动态创建对应工厂：
```java
String LandF = appProps.getProperty("LandF");
GUIFactory guiFactory;
if(LandF.equals("Motif"))
    guiFactory = new MotifFactory();
else if(LandF.equals("Mac"))
    guiFactory = new MacFactory();
```
重启软件才能换风格，运行中不能实时切换。

### 方式3：运行时菜单一键切换（Lexi v3.0，最终目标）
软件运行过程中，用户点击菜单栏「切换Mac界面」：
1. 销毁旧的 `guiFactory`，重新 new 一个 MacFactory 赋值；
2. 清空当前所有UI控件；
3. 用新工厂重新生成整套按钮、滚动条、菜单，界面立刻换风格。
完全实现PPT开头「run-time动态更换外观」的需求。

# 整套设计串联（和之前所有模式打通）
1. **Glyph**：文档、文字、UI控件统一顶层父类；
2. **Compositor（策略模式）**：负责文字排版分行分栏；
3. **MonoGlyph/Decorator装饰器模式**：给页面加边框、滚动条外观；
4. **Abstract Factory抽象工厂模式**：统一管理多平台UI控件（按钮、滚动条）的创建，实现全局皮肤动态切换。

# 通俗类比
- `GUIFactory` = 家具厂标准生产线（抽象工厂）
- `MotifFactory` = 中式家具厂；`MacFactory` = 北欧家具厂
- `ScrollBar/Button` = 家具品类（桌子、椅子，抽象产品）
- `MotifScrollBar` = 中式桌子；`MacScrollBar` = 北欧桌子
想要全屋换风格，只需要换一家工厂供货，不用逐个替换每件家具，就是抽象工厂的核心价值。

## 抽象工厂与跨窗口系统移植

# 四张PPT逐页完整拆解：抽象工厂模式 + Lexi跨多窗口系统（Mac/Windows/X11）移植方案
## 一、第一张：Abstract Factory Pattern（抽象工厂模式官方定义）
### 三句核心翻译+人话解释
1. **It captures how to create families of related product objects without instantiating classes directly.**
抽象工厂专门解决「**一整套相互配套的产品族**」创建问题，上层代码**不直接 new 具体实现类**，全部交给工厂生成。
- 例子：整套Mac风格UI = 一套产品族（Mac滚动条、Mac按钮、Mac菜单，三者配套成套）；整套Windows是另一套产品族。
- 上层只操作抽象`ScrollBar/Button`，永远不写`new MacScrollBar()`硬编码。

2. **It is most appropriate when the number and general kinds of product objects stay constant, and there are differences in specific product families.**
适用场景铁律：
产品**大类固定不变**（永远只有滚动条、按钮、窗口、菜单这几类控件），但**有多套不同实现系列**（Mac/Windows/Motif三套外观），这时用抽象工厂最合适。
如果频繁新增控件大类（比如突然新增树形控件、表格控件），抽象工厂会变得笨重，不适合。

3. **The Abstract Factory pattern’s emphasis on families of products distinguishes it from other creational patterns.**
它和其他创建型模式（工厂方法、建造者）最大区别：**核心聚焦「成套产品族」**，一次切换直接替换整套UI控件，而不是只创建单个对象。

## 二、第二张：Supporting Multiple Window Systems（需求背景：让Lexi跨平台可移植）
1. 现状：市面上存在多种互不兼容的窗口系统：Macintosh、Presentation Manager、Windows、X Window（X11），底层绘图API完全不一样。
2. 核心目标：让Lexi编辑器具备**可移植性 portable**，同一套代码能跑在所有窗口系统上，不用为每个系统重写整套绘图、窗口逻辑。
- 痛点：直接调用原生Mac/Windows绘图API会深度绑定系统，换系统就要全量改写渲染代码。

## 三、第三张：Multiple GUI Libraries（能不能用抽象工厂？窗口抽象分层设计）
### 1. 问题：第三方GUI库互不兼容
每个系统自带GUI库都有自己独立的窗口、绘图类，它们**没有统一公共父类**，不能直接继承复用；但所有窗口系统底层逻辑是相通的（窗口显示、最小化、画线、文字绘制）。
### 2. 解决方案：搭建一层和底层GUI库完全解耦的抽象Window层级
#### UML结构说明
1. 顶层抽象父类 `Window`（**不依赖任何系统底层API**）
定义通用抽象接口：窗口管理（Redraw重绘、Iconify最小化、Lower置底）、绘图（DrawLine画线等）。
2. Window 三大子类（业务窗口类型，和系统无关）
- `ApplicationWindow`：软件主窗口
- `IconWindow`：最小化后的图标窗口
- `DialogWindow`：弹窗对话框
3. 和Glyph的关联：Window持有Glyph，窗口重绘时调用`glyph->Draw(this)`，把文档里所有文字、边框、UI控件全部绘制到窗口上，打通之前Glyph排版体系。
4. 底层实现：后面会用抽象工厂，给每个Window子类生成对应Mac/Windows/X的平台实现，上层Window业务代码完全不用改。

### 核心思路
用一层**独立抽象层**隔离上层Lexi业务代码和底层各个系统GUI库，上层只调用抽象Window接口，底层不同系统各自实现一套Window子类。

## 四、第四张：Encapsulating Implementation Dependencies（封装底层系统依赖）
把所有和操作系统绑定的实现细节，全部封装在抽象`Window`类的虚接口内部，上层业务代码完全感知不到底层是Mac还是Windows。
### Window接口分为两大职责
1. **窗口管理 window management**
纯窗口行为：刷新界面、前置窗口、后置窗口、最小化窗口。
```cpp
virtual void Redraw();
virtual void Raise();
virtual void Lower();
virtual void Iconify();
```
2. **基础绘图 graphics**
所有Glyph（文字、图片、边框、按钮）绘制都会调用这些绘图接口：画线、矩形、多边形、文字渲染。
```cpp
virtual void DrawLine();
virtual void DrawRect();
virtual void DrawPolygon();
virtual void DrawText();
```
### 封装带来的好处
1. 上层Lexi、Glyph、Compositor、装饰器全部只依赖这份抽象接口，**不包含任何平台相关代码**；
2. 移植到新窗口系统时，只新增一套Window的具体实现，上层代码一行不用修改；
3. 系统底层API的差异被完全隐藏在虚函数实现内部，实现依赖隔离。

# 整套知识点串联（打通前面所有PPT）
1. **Glyph**：文档最小可视单元（文字、图片、边框、UI按钮滚动条），统一绘制接口；
2. **Compositor（策略模式）**：排版拆分文字生成行、栏容器；
3. **MonoGlyph/Decorator装饰器**：给页面加边框、滚动条外观；
4. **Abstract Factory抽象工厂**：
   - 第一层用途：切换多平台UI控件（Mac/Windows按钮、滚动条整套皮肤）；
   - 第二层用途：跨窗口系统，生成Mac/X/Windows三套底层Window实现；
5. **抽象Window封装层**：隔离上层业务和各系统原生GUI库，实现软件跨平台可移植。

# 通俗一句话总结
这四页PPT讲：用**抽象工厂模式**，给Lexi做两层抽象隔离：
1. 隔离不同平台UI控件外观（按钮、滚动条皮肤一键整套切换）；
2. 隔离Mac/Windows/X不同底层窗口绘图系统，让软件一套代码跨系统运行，把系统相关的底层实现全部封装隐藏，上层业务完全不用关心底层平台差异。

## 桥接模式：Window与WindowImp

# 两张PPT完整讲解：Window + WindowImp = **桥接模式（Bridge Pattern）**
## 核心背景
之前我们有两套独立变化的维度：
1. **窗口业务类型（上层抽象，会变）**：主窗口`ApplicationWindow`、弹窗`DialogWindow`、图标窗口`IconWindow`
2. **底层操作系统窗口实现（底层平台，会变）**：Mac、PM、X11 三套互不兼容的系统API

如果只用**单一继承**会出现类爆炸：`MacApplicationWindow`、`MacDialogWindow`、`XApplicationWindow`……组合爆炸、无法维护。
所以用**桥接模式**把两套变化维度拆成两条独立继承树，用「组合持有」关联，彻底解耦。

---

## 第一张PPT：Window & WindowImp 设计目标
### 三句逐句翻译+通俗解释
1. **Define a separate WindowImp class hierarchy to hide different window system implementations.**
单独开辟一套 `WindowImp` 继承树，用来**隔离、隐藏各个操作系统底层窗口的实现差异**。
上层业务代码完全看不到Mac/X11原生API，全部封装在WindowImp子类里。

2. **WindowImp is an abstract class for objects that encapsulate window system-dependent code.**
`WindowImp` 是抽象基类，专门存放**和操作系统强绑定的底层原生代码**：调用Mac绘图API、X11窗口接口全部写在它的子类中。

3. **Configure each window object with an instance of a WindowImp subclass for that system.**
每一个上层`Window`窗口对象，内部都会持有一个对应平台的`WindowImp`实现对象（成员变量`imp`）。
程序启动时根据当前系统，给Window绑定`MacWindowImp` / `XWindowImp`，运行时切换底层平台实现。

---

## 第二张PPT：UML类图拆解两条独立继承树
### 树1：上层业务窗口树（Window 分支，面向Lexi业务）
```
Window（上层抽象接口，对外暴露Raise()、DrawRect()）
├─ ApplicationWindow 主程序窗口
├─ IconWindow 最小化图标窗口
└─ DialogWindow 弹窗对话框
```
- 职责：处理Lexi软件业务逻辑，和文档Glyph交互、管理界面内容；
- **完全不包含任何平台原生API**，只调用内部`imp`成员完成底层操作。

### 树2：底层平台实现树（WindowImp 分支，面向操作系统）
```
WindowImp（底层抽象设备接口，定义设备操作：DeviceRaise()、DeviceRect()）
├─ MacWindowImp  Mac系统底层实现
├─ PMWindowImp   PM系统底层实现
└─ XWindowImp    X11窗口系统底层实现
```
- 职责：封装对应系统的原生窗口、绘图API；
- 每个子类重写`DeviceRaise()`、`DeviceRect()`，调用各自系统专属函数。

### 两者关联：Window 持有 WindowImp 成员 `imp`（桥接的核心）
`Window` 内部有一个成员 `WindowImp* imp;`，相当于搭了一座“桥”，连接上层业务和底层平台。

## 完整调用流程（举个Raise置顶窗口例子）
```cpp
// 1. 上层业务代码调用窗口置顶（完全不关心底层是Mac还是X）
void Window::Raise() {
    // 2. 转发给持有的底层实现对象imp
    imp->DeviceRaise();
}

// MacWindowImp 底层实现（Mac专属系统调用）
void MacWindowImp::DeviceRaise() {
    MacAPI_MoveWindowToFront(); // Mac原生API
}

// XWindowImp 底层实现（X11专属系统调用）
void XWindowImp::DeviceRaise() {
    X11_XRaiseWindow(rawXWindowHandle); // X11原生API
}
```

绘图同理：
```cpp
void Window::DrawRect() {
    imp->DeviceRect(); // 转发到底层平台绘图实现
}
```

## 桥接模式解决的核心痛点
1. **两套变化维度完全独立扩展**
   - 新增窗口业务：只加`Window`子类（如`TooltipWindow`），不用改任何底层平台代码；
   - 新增操作系统：只加`WindowImp`子类（如`WinWindowImp`），上层所有窗口类一行不动。
2. 避免“双重继承”带来的类爆炸
   不用写 `MacDialogWindow`、`XDialogWindow` 这种组合子类，无限扩展不会出现类数量暴涨。
3. 上层业务代码完全跨平台、可移植
   Lexi的Glyph、排版、UI工厂全部只依赖上层`Window`抽象，编译、运行时切换底层WindowImp即可适配不同系统。

## 和之前知识点串联
1. `Glyph`：窗口里渲染的所有文档/UI内容；
2. `Window`：上层画布抽象，接收Glyph的绘制请求；
3. `WindowImp`：桥接的底层，真正对接Mac/X/PM操作系统原生绘图窗口API；
4. 抽象工厂：运行时创建对应系统的`WindowImp`实例，注入Window完成平台适配。

## 生活化类比
- `Window` = 画图软件的画布（上层业务：主画布、弹窗画布、小图标画布）
- `WindowImp` = 不同品牌的显卡驱动（Mac显卡驱动、X11显卡驱动）
画布本身只管接收绘图指令，真正和显卡硬件交互、渲染像素的工作，全部交给底层驱动`imp`。换电脑系统只需要换驱动，画布逻辑完全不用改。

