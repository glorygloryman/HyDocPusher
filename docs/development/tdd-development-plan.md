# HyDocPusher TDD 开发计划

## 项目背景 (Project Context)

* **项目名称:** HyDocPusher (内容发布数据归档同步服务)
* **核心目标:** 构建一个稳定、高效的异步数据同步服务，用于将内容发布系统的消息自动转换为档案系统格式并推送到第三方电子档案管理系统
* **技术栈/语言:** Python 3.9.6, FastAPI, Apache Pulsar, Pydantic, httpx, structlog, pytest
* **关键特性列表 (简述):**
    * **特性1：配置管理模块** - 统一管理应用配置、Pulsar连接、档案系统集成和分类映射规则
    * **特性2：消息消费模块** - 实现Pulsar消息的可靠消费和处理
    * **特性3：数据转换模块** - 将源JSON数据转换为档案系统标准格式
    * **特性4：HTTP客户端模块** - 实现与档案系统的可靠HTTP通信
    * **特性5：异常处理和错误恢复** - 完善的异常处理和重试机制
    * **特性6：监控和健康检查** - 系统状态监控和健康检查接口

## 任务拆解和输出格式要求 (Task Breakdown and Output Format)

### 配置管理模块

**TASK001: 应用配置管理类**

* **功能描述 (Functional Description):**
    * 创建一个统一的应用配置管理类，使用Pydantic Settings管理所有配置项，包括Pulsar连接配置、档案系统API配置、业务配置等。支持环境变量注入和配置验证。

* **前置任务 (Prerequisites):**
    * 无

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用Python和Pydantic BaseSettings，创建一个名为`AppConfig`的配置管理类，它需要继承自`BaseSettings`，并实现以下功能：
    1. 定义Pulsar配置项（cluster_url、topic、subscription、dead_letter_topic）
    2. 定义档案系统配置项（api_url、timeout、重试次数、认证信息）
    3. 定义业务配置项（公司名称、保留期限等）
    4. 定义域名配置项（domain），用于附件地址转换功能
    5. 支持从环境变量读取配置，使用`Field(..., env='ENV_VAR_NAME')`
    6. 实现配置验证，确保必需的配置项不为空，包括域名格式验证
    7. 提供配置加载和验证方法，支持域名配置的动态更新

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功加载完整配置**
        * **Given:** 所有必需的环境变量都已设置，包括PULSAR_CLUSTER_URL、ARCHIVE_API_URL等。
        * **When:** 调用`AppConfig()`创建配置实例。
        * **Then:** 系统应成功创建配置实例，所有配置项正确映射到环境变量值。
    * **Test Case 2: 缺少必需配置项**
        * **Given:** 缺少必需的环境变量（如PULSAR_CLUSTER_URL）。
        * **When:** 调用`AppConfig()`创建配置实例。
        * **Then:** 系统应抛出ValidationError，指出缺少必需的配置项。
    * **Test Case 3: 使用默认配置**
        * **Given:** 只设置了部分环境变量，其他配置项有默认值。
        * **When:** 调用`AppConfig()`创建配置实例。
        * **Then:** 系统应使用设置的值和默认值成功创建配置实例。
    * **Test Case 4: 配置验证**
        * **Given:** 设置了无效的配置值（如负数的超时时间）。
        * **When:** 调用`AppConfig()`创建配置实例。
        * **Then:** 系统应抛出ValidationError，指出配置值无效。
    * **Test Case 5: 域名配置验证**
        * **Given:** 设置了无效的域名格式（如缺少协议或格式错误）。
        * **When:** 调用`AppConfig()`创建配置实例。
        * **Then:** 系统应抛出ValidationError，指出域名格式无效。
    * **Test Case 6: 域名配置成功加载**
        * **Given:** 设置了有效的域名配置（如"https://example.com"）。
        * **When:** 调用`AppConfig()`创建配置实例。
        * **Then:** 系统应成功创建配置实例，域名配置正确映射。

**TASK002: 分类映射配置管理**

* **功能描述 (Functional Description):**
    * 创建分类映射配置管理类，负责从YAML文件加载频道到档案分类的映射规则，支持默认分类和动态映射查询。

* **前置任务 (Prerequisites):**
    * TASK001

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建一个名为`ClassificationConfig`的配置管理类，它需要实现以下功能：
    1. 从YAML文件加载分类映射规则（channel_id -> classfyname, classfy）
    2. 提供根据channel_id查询分类信息的方法
    3. 支持默认分类配置
    4. 实现配置热重载功能
    5. 添加配置验证和错误处理

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功加载分类映射配置**
        * **Given:** 存在有效的classification-rules.yaml文件，包含多个频道映射规则。
        * **When:** 调用`ClassificationConfig.load_from_file()`加载配置。
        * **Then:** 系统应成功加载所有映射规则，并能正确查询指定频道的分类信息。
    * **Test Case 2: 查询存在的频道**
        * **Given:** 配置中存在channel_id为"2240"的映射规则。
        * **When:** 调用`get_classification("2240")`方法。
        * **Then:** 系统应返回对应的分类信息（classfyname="新闻头条", classfy="XWTT"）。
    * **Test Case 3: 查询不存在的频道**
        * **Given:** 配置中不存在channel_id为"9999"的映射规则。
        * **When:** 调用`get_classification("9999")`方法。
        * **Then:** 系统应返回默认分类信息。
    * **Test Case 4: 配置文件不存在**
        * **Given:** 指定的配置文件不存在。
        * **When:** 调用`ClassificationConfig.load_from_file()`方法。
        * **Then:** 系统应抛出FileNotFoundError，并包含适当的错误信息。

### 消息消费模块

**TASK003: Pulsar消费者类**

* **功能描述 (Functional Description):**
    * 创建Pulsar消息消费者类，负责连接到Pulsar集群(可配置)、订阅指定Topic(可配置)、接收消息并调用消息处理器进行处理。

* **前置任务 (Prerequisites):**
    * TASK001, TASK002

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用Python和pulsar-client库，创建一个名为`PulsarConsumer`的类，它需要实现以下功能：
    1. 异步连接到Pulsar集群
    2. 订阅指定的Topic和Subscription
    3. 实现消息接收和分发逻辑
    4. 支持消息确认和重试机制
    5. 处理连接异常和重连逻辑
    6. 提供优雅关闭功能

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功连接到Pulsar**
        * **Given:** 有效的Pulsar集群URL和Topic配置。
        * **When:** 调用`PulsarConsumer.connect()`方法。
        * **Then:** 系统应成功建立连接，并订阅指定的Topic。
    * **Test Case 2: 接收并处理消息**
        * **Given:** Pulsar消费者已连接，Topic中有新消息到达。
        * **When:** 消息到达时触发消息处理回调。
        * **Then:** 系统应正确解析消息内容，并调用消息处理器进行处理。
    * **Test Case 3: 连接失败处理**
        * **Given:** 无效的Pulsar集群URL或网络不可达。
        * **When:** 调用`PulsarConsumer.connect()`方法。
        * **Then:** 系统应捕获连接异常，记录错误日志，并实现重连逻辑。
    * **Test Case 4: 优雅关闭**
        * **Given:** Pulsar消费者正在运行并处理消息。
        * **When:** 调用`PulsarConsumer.close()`方法。
        * **Then:** 系统应停止接收新消息，完成当前消息处理，并释放所有资源。
    * **Test Case 5: 标准消息格式处理**
        * **Given:** Pulsar消费者已连接，Topic中有符合系统集成文档2.2章节格式的完整消息（包含MSG、DATA、ISSUCCESS字段，DATA中包含SITENAME、CRTIME、CHANNELID、VIEWID、DOCID、OPERTYPE等必要字段，以及APPENDIX附件信息）。
        * **When:** 消息到达时触发消息处理回调。
        * **Then:** 系统应正确解析消息的所有字段（MSG状态、DATA业务数据、CHNLDOC频道文档信息、APPENDIX附件列表），验证消息格式完整性，并成功调用数据转换器处理包含图片、视频等多种附件类型的复杂消息结构。

**TASK004: 消息处理器类**

* **功能描述 (Functional Description):**
    * 创建消息处理器类，负责验证、解析接收到的Pulsar消息，并调用数据转换器进行处理，支持错误处理和死信队列。

* **前置任务 (Prerequisites):**
    * TASK001, TASK002, TASK003

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建一个名为`MessageHandler`的类，它需要实现以下功能：
    1. 验证接收到的消息格式和必需字段
    2. 解析JSON消息数据
    3. 调用数据转换器进行数据转换
    4. 处理转换结果和异常
    5. 实现消息确认和重试逻辑
    6. 支持死信队列处理

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功处理有效消息**
        * **Given:** 接收到格式正确的消息，包含所有必需字段。
        * **When:** 调用`MessageHandler.handle_message()`方法。
        * **Then:** 系统应成功解析消息，调用数据转换器，并确认消息处理成功。
    * **Test Case 2: 处理格式无效消息**
        * **Given:** 接收到格式无效的消息（如JSON格式错误）。
        * **When:** 调用`MessageHandler.handle_message()`方法。
        * **Then:** 系统应捕获解析异常，记录错误日志，并将消息发送到死信队列。
    * **Test Case 3: 缺少必需字段**
        * **Given:** 接收到的消息缺少必需字段（如DOCID）。
        * **When:** 调用`MessageHandler.handle_message()`方法。
        * **Then:** 系统应验证失败，记录错误日志，并将消息发送到死信队列。
    * **Test Case 4: 数据转换失败**
        * **Given:** 消息格式正确，但数据转换过程中出现异常。
        * **When:** 调用`MessageHandler.handle_message()`方法。
        * **Then:** 系统应捕获转换异常，记录错误日志，并实现重试机制。

### 数据转换模块

**TASK005: 数据转换器主类**

* **功能描述 (Functional Description):**
    * 创建数据转换器主类，协调整个数据转换过程，包括字段映射、附件构建和格式转换。

* **前置任务 (Prerequisites):**
    * TASK001, TASK002

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建一个名为`DataTransformer`的类，它需要实现以下功能：
    1. 接收源消息数据作为输入
    2. 协调字段映射器进行字段转换
    3. 调用附件构建器处理附件信息
    4. 生成符合档案系统格式的输出数据
    5. 实现数据验证和错误处理
    6. 支持转换日志记录

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功转换完整消息**
        * **Given:** 接收到完整的源消息数据，包含所有必需字段。
        * **When:** 调用`DataTransformer.transform()`方法。
        * **Then:** 系统应成功生成符合档案系统格式的数据，包含所有映射字段和附件信息。
    * **Test Case 2: 处理部分字段缺失**
        * **Given:** 接收到的消息缺少一些可选字段。
        * **When:** 调用`DataTransformer.transform()`方法。
        * **Then:** 系统应使用默认值填充缺失字段，并成功完成转换。
    * **Test Case 3: 附件处理**
        * **Given:** 接收到的消息包含多种类型的附件（图片、视频、文档）。
        * **When:** 调用`DataTransformer.transform()`方法。
        * **Then:** 系统应正确解析和转换所有附件信息，生成符合要求的附件数组。
    * **Test Case 4: 转换验证失败**
        * **Given:** 接收到的消息数据无法通过业务验证。
        * **When:** 调用`DataTransformer.transform()`方法。
        * **Then:** 系统应抛出DataTransformException，并包含详细的错误信息。

**TASK006: 字段映射器类**

* **功能描述 (Functional Description):**
    * 创建字段映射器类，负责将源消息字段映射到档案系统字段，包括数据类型转换和格式标准化。

* **前置任务 (Prerequisites):**
    * TASK001, TASK002, TASK005

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建一个名为`FieldMapper`的类，它需要实现以下功能：
    1. 定义源字段到目标字段的映射规则
    2. 实现字段值的类型转换和格式化
    3. 处理日期格式转换（如CRTIME到docdate）
    4. 支持分类映射（通过ClassificationConfig）
    5. 实现字段验证和默认值处理
    6. 支持自定义映射规则

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 基本字段映射**
        * **Given:** 源消息包含DOCTITLE字段。
        * **When:** 调用`FieldMapper.map_field("DOCTITLE", "裸眼3D看云能")`方法。
        * **Then:** 系统应返回映射结果{"title": "裸眼3D看云能"}。
    * **Test Case 2: 日期格式转换**
        * **Given:** 源消息包含CRTIME字段，值为"2025-04-09 15:46:25"。
        * **When:** 调用`FieldMapper.map_field("CRTIME", "2025-04-09 15:46:25")`方法。
        * **Then:** 系统应返回映射结果{"docdate": "2025-04-09", "year": "2025"}。
    * **Test Case 3: 分类映射**
        * **Given:** 源消息包含CHANNELID字段，值为"2240"。
        * **When:** 调用`FieldMapper.map_classification("2240")`方法。
        * **Then:** 系统应返回映射结果{"classfyname": "新闻头条", "classfy": "XWTT"}。
    * **Test Case 4: 处理空值和默认值**
        * **Given:** 源消息中某些字段为空或不存在。
        * **When:** 调用`FieldMapper.map_field()`方法。
        * **Then:** 系统应使用预定义的默认值填充空字段。

**TASK007: 附件构建器类**

* **功能描述 (Functional Description):**
    * 创建附件构建器类，负责从源消息中提取和构建附件信息，支持多种附件字段（APPENDIX、appdix、attachments等）和地址转换功能，实现灵活的附件处理逻辑。

* **前置任务 (Prerequisites):**
    * TASK001, TASK005, TASK006

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建一个名为`AttachmentBuilder`的类，它需要实现以下功能：
    1. 解析源消息中的多种附件字段（APPENDIX数组、appdix字段、attachments字段等）
    2. 实现HTML内容解析，从正文中提取图片和链接地址
    3. 支持地址转换功能，将相对路径转换为绝对路径（使用配置的域名）
    4. 根据附件类型（图片、视频、文档、正文）进行分类处理
    5. 构建符合档案系统要求的附件格式，包含name、ext、file、type字段
    6. 处理JSON格式的附件字段，支持嵌套结构解析
    7. 实现附件验证和错误处理，支持容错机制
    8. 保持向后兼容，支持原有APPENDIX字段处理逻辑

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 处理APPENDIX字段附件**
        * **Given:** 源消息包含APPENDIX数组，包含视频附件信息（APPFLAG为50）。
        * **When:** 调用`AttachmentBuilder.build_attachments()`方法。
        * **Then:** 系统应正确解析视频附件，生成包含name、ext、file、type字段的附件对象。
    * **Test Case 2: 处理appdix字段附件**
        * **Given:** 源消息包含appdix字段，为JSON格式的附件数组。
        * **When:** 调用`AttachmentBuilder.build_attachments()`方法。
        * **Then:** 系统应正确解析JSON格式附件，生成相应的附件对象数组。
    * **Test Case 3: HTML内容解析和地址转换**
        * **Given:** 源消息包含HTML正文，内含相对路径的图片链接。
        * **When:** 调用`AttachmentBuilder.parse_html_content()`方法。
        * **Then:** 系统应提取图片链接，并使用配置的域名转换为绝对路径。
    * **Test Case 4: 多种附件字段优先级处理**
        * **Given:** 源消息同时包含APPENDIX、appdix和attachments字段。
        * **When:** 调用`AttachmentBuilder.build_attachments()`方法。
        * **Then:** 系统应按优先级处理各字段，合并生成完整的附件列表。
    * **Test Case 5: 构建正文附件**
        * **Given:** 源消息包含DOCPUBURL字段。
        * **When:** 调用`AttachmentBuilder.build_html_attachment()`方法。
        * **Then:** 系统应使用DOCPUBURL构建正文附件，type为"正文"。
    * **Test Case 6: 处理无效附件和容错**
        * **Given:** 源消息包含格式无效的附件信息。
        * **When:** 调用`AttachmentBuilder.build_attachments()`方法。
        * **Then:** 系统应跳过无效附件，记录警告日志，并继续处理其他有效附件。

### HTTP客户端模块

**TASK008: 档案系统HTTP客户端类**

* **功能描述 (Functional Description):**
    * 创建档案系统HTTP客户端类，负责与档案系统API进行HTTP通信，支持同步和异步调用。

* **前置任务 (Prerequisites):**
    * TASK001, TASK005, TASK006, TASK007

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用Python和httpx库，创建一个名为`ArchiveClient`的类，它需要实现以下功能：
    1. 实现HTTP客户端，支持POST请求发送档案数据
    2. 配置请求超时、重试机制和认证信息
    3. 处理HTTP响应和状态码
    4. 实现请求和响应日志记录
    5. 支持连接池和会话管理
    6. 处理网络异常和服务器错误

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功发送档案数据**
        * **Given:** 档案系统API正常运行，有效的档案数据。
        * **When:** 调用`ArchiveClient.send_archive_data()`方法。
        * **Then:** 系统应成功发送HTTP POST请求，返回200状态码和成功响应。
    * **Test Case 2: 处理服务器错误**
        * **Given:** 档案系统API返回500错误。
        * **When:** 调用`ArchiveClient.send_archive_data()`方法。
        * **Then:** 系统应捕获HTTP异常，记录错误日志，并实现重试机制。
    * **Test Case 3: 请求超时处理**
        * **Given:** 档案系统API响应超时。
        * **When:** 调用`ArchiveClient.send_archive_data()`方法。
        * **Then:** 系统应捕获超时异常，记录错误日志，并重试请求。
    * **Test Case 4: 认证失败处理**
        * **Given:** 档案系统API返回401认证失败。
        * **When:** 调用`ArchiveClient.send_archive_data()`方法。
        * **Then:** 系统应记录认证失败错误，不重试请求。

**TASK009: 重试处理器类**

* **功能描述 (Functional Description):**
    * 创建重试处理器类，实现指数退避重试逻辑，用于HTTP请求失败后的自动重试。

* **前置任务 (Prerequisites):**
    * TASK008

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建一个名为`RetryHandler`的类，它需要实现以下功能：
    1. 实现指数退避重试算法
    2. 配置最大重试次数和基础延迟时间
    3. 支持可重试和不可重试异常的区分
    4. 实现重试日志记录
    5. 支持重试回调函数
    6. 处理重试超时和取消

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功重试后恢复**
        * **Given:** HTTP请求第一次失败，第二次成功。
        * **When:** 调用`RetryHandler.execute_with_retry()`方法。
        * **Then:** 系统应在第一次失败后等待指定时间，然后重试并成功返回结果。
    * **Test Case 2: 达到最大重试次数**
        * **Given:** HTTP请求连续失败，达到最大重试次数。
        * **When:** 调用`RetryHandler.execute_with_retry()`方法。
        * **Then:** 系统应在达到最大重试次数后抛出最后一个异常。
    * **Test Case 3: 指数退避延迟**
        * **Given:** 配置基础延迟为1秒，最大重试次数为3次。
        * **When:** 连续重试时。
        * **Then:** 系统应按照1秒、2秒、4秒的间隔进行重试。
    * **Test Case 4: 不可重试异常**
        * **Given:** 抛出认证失败等不可重试异常。
        * **When:** 调用`RetryHandler.execute_with_retry()`方法。
        * **Then:** 系统应立即抛出异常，不进行重试。

### 数据模型模块

**TASK010: 源消息数据模型**

* **功能描述 (Functional Description):**
    * 创建源消息的Pydantic数据模型，用于验证和序列化来自Pulsar的消息数据。

* **前置任务 (Prerequisites):**
    * TASK001

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用Pydantic创建源消息数据模型，包括：
    1. 主消息模型（包含MSG、DATA、ISSUCCESS字段）
    2. 数据内容模型（包含文档基本信息、频道信息等）
    3. 传统附件信息模型（包含APPFILE、APPFLAG等字段，用于APPENDIX数组）
    4. 新增附件字段模型（支持appdix、attachments等JSON格式字段）
    5. 数据容器模型（包含appdix字段，支持多种附件格式）
    6. 实现字段别名和验证规则，支持多种附件字段的灵活解析
    7. 支持嵌套模型和数组类型，兼容新旧附件格式
    8. 添加自定义验证方法，确保附件字段的数据完整性

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 验证完整消息**
        * **Given:** 完整的JSON消息数据，包含所有必需字段。
        * **When:** 使用`SourceMessageSchema`验证数据。
        * **Then:** 系统应成功验证并创建模型实例，所有字段正确映射。
    * **Test Case 2: 验证缺少必需字段**
        * **Given:** 缺少必需字段（如DOCID）的消息数据。
        * **When:** 使用`SourceMessageSchema`验证数据。
        * **Then:** 系统应抛出ValidationError，指出缺少必需字段。
    * **Test Case 3: 验证字段类型**
        * **Given:** 包含错误类型字段的消息数据。
        * **When:** 使用`SourceMessageSchema`验证数据。
        * **Then:** 系统应抛出ValidationError，指出字段类型错误。
    * **Test Case 4: 验证传统附件数组**
        * **Given:** 包含多个APPENDIX附件的消息数据。
        * **When:** 使用`SourceMessageSchema`验证数据。
        * **Then:** 系统应正确验证传统附件数组，每个附件都符合附件模型。
    * **Test Case 5: 验证新附件字段**
        * **Given:** 包含appdix或attachments等JSON格式附件字段的消息数据。
        * **When:** 使用`SourceMessageSchema`验证数据。
        * **Then:** 系统应正确验证新格式附件字段，支持嵌套结构解析。
    * **Test Case 6: 验证多种附件格式兼容**
        * **Given:** 同时包含APPENDIX数组和appdix字段的消息数据。
        * **When:** 使用`SourceMessageSchema`验证数据。
        * **Then:** 系统应正确验证所有附件格式，保持数据完整性和优先级处理。

**TASK011: 档案请求数据模型**

* **功能描述 (Functional Description):**
    * 创建档案系统请求的Pydantic数据模型，用于验证和序列化发送到档案系统的数据。

* **前置任务 (Prerequisites):**
    * TASK001, TASK010

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用Pydantic创建档案请求数据模型，包括：
    1. 主请求模型（包含AppId、AppToken、CompanyName等字段）
    2. 档案数据模型（包含did、wzmc、title等字段）
    3. 附件模型（包含name、ext、file、type等字段）
    4. 实现字段验证和格式检查
    5. 支持数据序列化和反序列化
    6. 添加自定义验证方法

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 验证完整档案请求**
        * **Given:** 完整的档案请求数据，包含所有必需字段。
        * **When:** 使用`ArchiveRequestSchema`验证数据。
        * **Then:** 系统应成功验证并创建模型实例，所有字段正确映射。
    * **Test Case 2: 验证附件数组**
        * **Given:** 包含多个附件的档案请求数据。
        * **When:** 使用`ArchiveRequestSchema`验证数据。
        * **Then:** 系统应正确验证附件数组，每个附件都符合附件模型要求。
    * **Test Case 3: 序列化为JSON**
        * **Given:** 有效的档案请求模型实例。
        * **When:** 调用`model_dump_json()`方法。
        * **Then:** 系统应生成符合要求的JSON字符串。
    * **Test Case 4: 验证业务规则**
        * **Given:** 违反业务规则的数据（如retention_period为负数）。
        * **When:** 使用`ArchiveRequestSchema`验证数据。
        * **Then:** 系统应抛出ValidationError，指出业务规则违反。

### 异常处理模块

**TASK012: 自定义异常类**

* **功能描述 (Functional Description):**
    * 创建项目自定义异常类，用于处理各种业务异常和系统异常。

* **前置任务 (Prerequisites):**
    * 无

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建以下自定义异常类：
    1. `HyDocPusherException` - 基础异常类
    2. `ConfigurationException` - 配置相关异常
    3. `MessageProcessException` - 消息处理异常
    4. `DataTransformException` - 数据转换异常
    5. `ArchiveClientException` - 档案系统客户端异常
    6. 实现异常链和错误码
    7. 添加详细的错误信息和上下文

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 抛出和捕获自定义异常**
        * **Given:** 模拟配置错误场景。
        * **When:** 抛出`ConfigurationException`。
        * **Then:** 系统应正确抛出异常，包含错误信息和错误码。
    * **Test Case 2: 异常链处理**
        * **Given:** 底层异常触发上层异常。
        * **When:** 抛出包含原因的自定义异常。
        * **Then:** 系统应保持异常链，可以通过`__cause__`访问原始异常。
    * **Test Case 3: 异常序列化**
        * **Given:** 自定义异常实例。
        * **When:** 调用`str()`或`repr()`方法。
        * **Then:** 系统应返回格式化的错误信息字符串。
    * **Test Case 4: 异常日志记录**
        * **Given:** 自定义异常被抛出。
        * **When:** 使用日志系统记录异常。
        * **Then:** 系统应正确记录异常信息和堆栈跟踪。

### 主应用和集成

**TASK013: 主应用入口**

* **功能描述 (Functional Description):**
    * 创建主应用入口点，集成所有模块，启动消息处理循环。

* **前置任务 (Prerequisites):**
    * TASK001-TASK012

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请创建主应用入口文件`main.py`，实现以下功能：
    1. 初始化配置管理
    2. 设置日志系统
    3. 创建消息消费者和数据转换器实例
    4. 启动消息处理循环
    5. 实现优雅关闭处理
    6. 添加命令行参数支持

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 成功启动应用**
        * **Given:** 所有配置正确，依赖服务可用。
        * **When:** 运行主应用。
        * **Then:** 系统应成功启动，初始化所有组件，并开始监听消息。
    * **Test Case 2: 处理启动异常**
        * **Given:** 配置错误或依赖服务不可用。
        * **When:** 运行主应用。
        * **Then:** 系统应捕获启动异常，记录错误日志，并优雅退出。
    * **Test Case 3: 优雅关闭**
        * **Given:** 应用正在运行，接收到关闭信号。
        * **When:** 处理关闭信号。
        * **Then:** 系统应停止接收新消息，完成当前处理，并释放资源。
    * **Test Case 4: 命令行参数处理**
        * **Given:** 不同的命令行参数（如--config, --log-level）。
        * **When:** 启动应用时传递参数。
        * **Then:** 系统应正确解析和应用命令行参数。

**TASK014: 健康检查服务**

* **功能描述 (Functional Description):**
    * 创建健康检查服务，提供系统状态监控和健康检查API端点。

* **前置任务 (Prerequisites):**
    * TASK001-TASK013

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用FastAPI创建健康检查服务，实现以下功能：
    1. 创建`/health`端点，返回基本健康状态
    2. 创建`/health/liveness`端点，用于Kubernetes存活探针
    3. 创建`/health/readiness`端点，用于Kubernetes就绪探针
    4. 检查各组件状态（Pulsar连接、档案系统API等）
    5. 实现健康状态缓存
    6. 添加指标收集功能

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 基本健康检查**
        * **Given:** 应用正常运行。
        * **When:** 访问`/health`端点。
        * **Then:** 系统应返回200状态码和健康状态信息。
    * **Test Case 2: 存活探针检查**
        * **Given:** 应用进程正在运行。
        * **When:** 访问`/health/liveness`端点。
        * **Then:** 系统应返回200状态码，表示应用存活。
    * **Test Case 3: 就绪探针检查**
        * **Given:** 所有依赖服务都可用。
        * **When:** 访问`/health/readiness`端点。
        * **Then:** 系统应返回200状态码，表示应用就绪。
    * **Test Case 4: 依赖服务不可用**
        * **Given:** 档案系统API不可用。
        * **When:** 访问`/health/readiness`端点。
        * **Then:** 系统应返回503状态码，表示应用未就绪。

### 测试和部署

**TASK015: 单元测试套件**

* **功能描述 (Functional Description):**
    * 为所有核心组件编写完整的单元测试，确保代码质量和功能正确性。

* **前置任务 (Prerequisites):**
    * TASK001-TASK014

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请使用pytest框架编写单元测试，包括：
    1. 为每个类和方法编写测试用例
    2. 使用mock对象模拟外部依赖
    3. 实现测试夹具（fixtures）和参数化测试
    4. 测试覆盖率达到80%以上
    5. 添加异步测试支持
    6. 集成代码覆盖率报告

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 配置管理测试**
        * **Given:** 配置管理类实例。
        * **When:** 测试各种配置加载和验证场景。
        * **Then:** 所有配置相关的功能都应正确工作。
    * **Test Case 2: 消息处理测试**
        * **Given:** 消息处理器实例和模拟消息。
        * **When:** 测试各种消息处理场景。
        * **Then:** 消息处理器应正确处理各种消息格式。
    * **Test Case 3: 数据转换测试**
        * **Given:** 数据转换器实例和测试数据。
        * **When:** 测试各种数据转换场景。
        * **Then:** 数据转换器应正确转换各种输入数据。
    * **Test Case 4: HTTP客户端测试**
        * **Given:** HTTP客户端实例和模拟响应。
        * **When:** 测试各种HTTP请求场景。
        * **Then:** HTTP客户端应正确处理各种响应和异常。

**TASK016: 集成测试套件**

* **功能描述 (Functional Description):**
    * 编写集成测试，验证各模块之间的协作和端到端功能。

* **前置任务 (Prerequisites):**
    * TASK001-TASK015

* **编码提示词 (Coding Prompt for Developer/AI):**
    * 请编写集成测试，包括：
    1. 端到端消息处理流程测试
    2. 与真实Pulsar集群的集成测试
    3. 与档案系统API的集成测试
    4. 错误恢复和重试机制测试
    5. 性能和负载测试
    6. 使用Testcontainers进行依赖服务测试

* **TDD测试用例 (TDD Test Cases):**
    * **Test Case 1: 完整消息处理流程**
        * **Given:** 完整的测试环境，包括Pulsar和档案系统。
        * **When:** 发送测试消息到Pulsar。
        * **Then:** 系统应完整处理消息并成功发送到档案系统。
    * **Test Case 2: 错误恢复测试**
        * **Given:** 档案系统暂时不可用。
        * **When:** 发送测试消息。
        * **Then:** 系统应实现重试机制，在服务恢复后成功处理消息。
    * **Test Case 3: 性能测试**
        * **Given:** 正常运行的测试环境。
        * **When:** 发送大量并发消息。
        * **Then:** 系统应保持稳定的性能，满足吞吐量要求。
    * **Test Case 4: 资源使用测试**
        * **Given:** 长时间运行的测试环境。
        * **When:** 持续发送消息。
        * **Then:** 系统应保持稳定的资源使用，无内存泄漏。

## 开发执行建议

### 开发顺序
1. **阶段1：基础设施** (TASK001-TASK002, TASK012) - 配置管理和异常处理
2. **阶段2：数据处理** (TASK005-TASK007, TASK010-TASK011) - 数据转换和模型
3. **阶段3：消息处理** (TASK003-TASK004) - 消息消费和处理
4. **阶段4：HTTP通信** (TASK008-TASK009) - 档案系统客户端
5. **阶段5：应用集成** (TASK013-TASK014) - 主应用和健康检查
6. **阶段6：测试验证** (TASK015-TASK016) - 单元测试和集成测试

### 质量保证
- 每个TASK完成后立即运行对应的测试用例
- 保持代码覆盖率在80%以上
- 定期进行代码审查和重构
- 使用静态代码分析工具（flake8, mypy）

### 部署准备
- 创建Docker镜像和docker-compose配置
- 编写部署脚本和文档
- 配置监控和日志收集
- 准备生产环境配置