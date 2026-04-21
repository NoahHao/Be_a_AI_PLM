昨晚AI圈最热闹的就是Claude Code的代码泄露事件，除了直接翻译一下破解者的 GitHub 首页的营销号外，还有对代码的分析，我这里从另一个角度分析一下，就是企业级 agent 解决方案的角度，以及 AI 全栈产品管理的角度来分析一下。

## 对 Agent 解决方案提供商的影响
之所以从企业解决方案的角度来分析，是因为很多人只是号称熟悉企业解决方案，但是看的出来当前人是没有在这里投入的，所以不知道这些 ISV 当前的能力，以及客户最主要的诉求，或者说最担心的点。

**整个 Agent 解决方案依旧会围绕着 openclaw 展开 **
首先，这个代码泄露的事儿肯定有 Antropic 公司自身的安全问题，但是某种程度上也是一种被动开源，吸引关注度的一种方式。 作为 Agent 管理平台的开创者，自己本身做的是一个通用话的 Agent 调用平台，但是却把产品命名为 XX Code，这样在宣传面上就不占优。 用户，尤其是企业的决策者就会倾向于认为这里偏编码业务，采购场景就受限。 再加上 Openclaw 通过接入了大量渠道软件的方式，引发了大众的关注，openclaw 当前已经成为 Agent 管理平台的事实标准。

至少你跟领导汇报，要采购一个类 Openclaw 产品，领导能觉得自己明白在采购什么。

我不觉得 Claude Code 这种方式，会把用户重新引导回来，我是这么说的

**“别说泄露了，就是现在裸奔都没有人看你”；当你遍览无码大片之后，还在乎别人擦个边么？**

**未来基本会朝这样的方向走，就是 Openclaw 吸取 Claude Code 中的关键技术细节，取长补短，把关键技术合入到自己的代码库中，Openclaw 继续保持当前的领先位置。**



## 具体是哪些技术 （当前展开不完，进入 todo list 跟踪）
- **安全**：这是影响企业解决方案最重要的一环，也是政企客户决策层最关注的一点，是准入门槛。 对于多 Agent 调度过程中，Claude 如何控制权限，能够作为一种参考架构，给所有 Agent 平台商借鉴意义。 主要是多层限制，最后选出最强限制，作为权限的最终结果。 四个限制包括 对当前 permisison Mode 的确认，4 路 Race 解析（User，Hook，Classifier，Bridge），Bash 分类 （就是 Linux 下的各种指令 比如 RM 这种删除指令，肯定风险最高） ， 规则引擎 （这个比较好理解，在我们使用 ClaudeCode 的时候，会有 Config 文件，让我们对工具配置权限，就是 allow，deny，ask 这种）。 这么多的配置路径，难免有前后冲突的部分，所以最后由 ResolveOnce 来做最后的裁定，选择一个最保守，最安全的策略。 （越安全，越繁琐，解决问题的能力越差，因为最保守的策略就是读都不让读）

- **上下文压缩技术+记忆机制** ： 很容易理解，这个对成本影响最大。 顺便提一句，我觉得当前之所以上下文内容这么冗余，没有人去优化，是因为有 Code plan 这种商业模式，反正不管用多少，都是按月付费，谁在乎用了多少 token，后面的 GPU 被怎样的消耗呢？ 供应商在乎，或者说一次性买断的用户在乎。 在同样的硬件底座上，肯定是能使用的越充分越好。 这就带来了两个关注点。 一个就是上下文的拼接，压缩技术。 这决定了 Prompt 的长度，和后端的计算，存储资源直接挂钩，Prompt 越长，计算量指数级增加，大量的 KVcache 对显存的占用也越来越多，能够大量命中 KVcache，减少重复计算肯定是最好的。 Prompt 的拼接规则越规范，后端越清楚如何命中这个 prompt。 （但是，实际在企业应用中，ISV 决定了如何拼接 Prompt 所以不那么容易命中） ClaudeCode 提供了这样的一种拼接机制，就是 “固定 Prompt （被缓存）+ SYSTEM_PROMPT_DYNAMIC_BOUNDARY + 动态 Prompt ” 中间的 Boundary 是一个分界线，可以理解成，所有的固定 prompt 是不去更改的，这样能够方便在后面的推理过程中，更好的命中 固定 prompt 中的 Token ，KVcache 被利用，节省了算力 。 其实这里能够展开很多细节讨论，我在 GitHub 中简单的讨论过，今天先不展开。 多段上下文压缩机制， 简单梳理下流程，当上下文达到阈值附近时 比如80%，进入上下文压缩，举例，已经问了21轮问题，此时会把前面的20轮压缩到8k，然后拼接第21轮问题，那么具体是怎么压缩的？ 此处调用大模型能力，通过prompt工程来实现，我把这里的提示词粘贴出来，供参考
```
Please create a comprehensive yet concise summary of the conversation transcript below. The summary will be used as context for continuing the conversation, so include all important decisions, code changes, findings, and context that would be needed to continue seamlessly.

Focus on:
- Key decisions made and their rationale
- Code or files that were created/modified
- Important findings or conclusions
- The current state of any ongoing tasks
- Any constraints or requirements discovered

“请根据以下对话记录创建一份全面而简洁的摘要。该摘要将用作继续对话的上下文，因此需要包含所有重要决策、代码变更、发现以及无缝继续所需的相关背景信息。

重点关注：
- 已做出的关键决策及其理由
- 创建/修改的代码或文件
- 重要发现或结论
- 当前进行中任务的状态
- 发现的任何限制条件或需求”。 
```
这里还有一个 “dream”做梦机制，就是在空闲时整理一下历史记忆，这个后续再仔细研究下。 
- **多Agent协调机制**：其实这个问题不大，整体和Opencode的思路差不多。 1. 研究阶段 (Research Phase)- 使用Agent Tool并行生成多个worker Agent - 各自独立进行信息收集 2 综合阶段 (Synthesis Phase) - 使用SendMessage收集worker的发现 - 合并多个worker的结果 3 实现阶段，任务分配 4 验证阶段 生成验证 结果 （这个opencode不支持，至少一个月前不支持，因为我当时在生成测试代码）

- **Tools** ： 这个其实相当于有了官方背书的tools，功能不复杂，但是可以拿来直接用

今天先写这些

最近在准备找新工作，创建了个github项目整理AI知识，https://github.com/NoahHao/Be_a