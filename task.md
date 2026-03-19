1. 读取 target.md 的系统目标。
2. 读取 claude-suggestions.md 中关于系统设计的讨论。
3. 读取 requirements.md 的需求描述。
4. 完成系统设计，并生成主要的逻辑代码，要求：
    1. 明确架构约束（Architecture Constraints）
    2. 明确模块化边界（Modularity）
    3. 明确配置化要求（Configuration）
    4. 明确 Mock 规范（Mock Strategy）
    5. 明确错误处理规范（Error Handling）
    6. 明确可观测性（Observability）
    7. 确保代码可执行


注意： 
1. Mock需要的所有的中间件，比如数据库、缓存、消息队列等等。
2. Mock供应商的API，配置
3. Mock各个业务系统及事件生成
