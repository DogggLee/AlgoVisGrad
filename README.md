# Algorithm Visualization Platform
Gradio-based visualization platform for external Flask algorithm services.

# 1. 设计边界
* 所有的算法都有以Flask Server的形式存在（大致实现方式可以参考对应的mock_server.py），并对外提供以下请求：
  * /health: 
    * 接收到请求后，返回算法Server的名称以及状态
  * /render: 
    * 接收到请求后，返回渲染好的可视化图像
    * 输入的请求会分为input和visualization两组参数，前者为对算法本身调用的输入参数封装，后者为可视化所需的各类参数，通常用于控制可视化结果中具体要绘制的内容
     
* 平台不关注可视化的具体实现方式，只要求算法在接收完整请求后可以将绘制好的可视化图片返回

## Usage
* 安装相关依赖
```bash
pip install -r requirements.txt
```

* 启动mock server 或算法Server (可选)
  * 一次性启动全部 mock server (可选)
  ```bash
  ./start_mock_demo.sh
  ```
  其会启动以下三个mock server：
  ```text
  perception_demo   http://127.0.0.1:5001
  path_planner_demo http://127.0.0.1:5002
  json_demo         http://127.0.0.1:5003
  ```

  * 单个 JSON demo mock server (可选)
  ```bash
  python -m components.json_demo.mock_server
  ```



* 启动可视化平台
```bash
python app.py
```

* 登录可视化平台页面: http://0.0.0.0:7860

## 2. 项目结构
``` bash
.
├── app.py
├── components      # 各算法对应的可视化页面组件
    ├── <component_name>        # 算法页面组件名称
        ├── __init__.py
        ├── mock_server.py      # 算法Mock Server（可选，仅用于离线调试）
        ├── resources           # 放置算法示例输入文件，可以是原始json，也可也是图像或.npy文件
            ├── inputs
            │   └── XX.json
            └── manifest.json   # 要加载的算法示例文件列表管理，需要说明对应示例的具体格式以便于有效解析处理
        └── vis_window.py       # 算法可视化页面UI定义
├── config.yaml     # 可视化平台配置，用于指定要加载的算法Server的请求地址与server-key
└── utils           # 基础工具函数
```

### 2.1 Developer Workflow
当要集成一个新的算法可视化页面时，需要在 components 文件夹中新建一个对应的 <component_name> 子文件夹，并实现其中的以下几个核心代码：

* vis_window.py: 整个算法页面的UI定义与请求响应逻辑
  * 其核心目的是提供必要的交互手段来构造算法输入的完整Json

  ```python
  class MyVisWindow(BaseVisWindow):
      def build(ctx):
          ...
  ```

  `build(ctx)` 是构造本算法页面的UI控件以及对应的CallBack函数，要注意VisWindow不是一个独立的网页，而是一组UI控件集合（可以理解为PPT里的组合），可以随时被顶层的app.py重新整体排布到其他位置。

Do not create `gr.Blocks` or top-level tabs inside a `VisWindow`; `app.py` owns the top-level layout.

  目前的典型页面可以大致分为以下4个部分：
  - title row：页面标题、算法Server状态、状态刷新按钮
  - Input column: 算法输入相关UI，通常包括一个输入示例selector、previewer以及部分参数输入栏；
  - Render column: 算法输出相关UI，通常包括可视化内容checkbox、结果渲染窗口以及响应状态.
  - Debug row: 用于完整展示请求和响应的Json体以便于复现调试


  在请求响应过程中，可以直接通过传入的ctx来对分配好的指定算法Server进行调用，不需要显式编码对应的算法Server地址，其由config.yaml统一管理

  ```python
  ctx.render_client.render_image_response(server_key, payload)
  ctx.health_client.check(server_key)
  ctx.component_resource_path("json_demo")
  ```

  

* resources/manifest.json: 所有算法示例的说明列表
  * 一个典型的示例文件包含以下字段：
  ```json
  {
      "id": "50_10p",               // 示例文件的检索ID
      "name": "10% Obs 50x50",      // 示例文件在可视化页面中展示的名字
      "data": "maps/50_10p.npy",    // 文件路径
      "content_type": "array/npy",  // 文件数据形式
      "shape": [50, 50],            // 文件尺寸
      "dtype": "uint8"              // 数据类型
  }
  ```
  content_type预先定义了以下几类，以便于可视化平台可以正常将其序列化传输：
  ```
  image/png     // `data` is PNG file bytes encoded as base64.
  image/jpeg    // `data` is JPEG file bytes encoded as base64.
  array/list    // `data` is a JSON list and is not base64 encoded.
  array/npy     // `data` is `.npy` file bytes encoded as base64.
  application/json   // `data` is original .json file
  ```

### 2.2 算法 Server 协议

Health check:

```http
GET /health
```

Render request:

```http
POST /render
```

Request shape:

```json
{
  "input": {
    "map": {
      "content_type": "array/npy",
      "filename": "50_20p.npy",
      "shape": [
        50,
        50
      ],
      "dtype": "uint8",
      "data": "k05VTVBZAQB2AHsnZGVzY3InOiAnfHUxJywgJ2ZvcnRyYW5fb3JkZXInOiBGYWxzZSwgJ3NoYXBlJzogKDUwLCA1MCksIH0gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAoBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAAAAAAAAAAAAAAAAAQABAAABAAAAAAAAAQAAAQABAAAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAABAAAAAAAAAAAAAAEAAQAAAAAAAQAAAAAAAAEAAQAAAAABAAEAAAABAQEBAAABAAAAAAABAQAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAQAAAAABAAAAAAEAAAAAAQEAAQAAAAAAAAAAAQAAAAAAAQAAAAAAAQEBAAAAAAAAAAEAAAEAAQAAAAAAAAAAAAABAQAAAAAAAAAAAQAAAAAAAAAAAQABAAAAAAAAAQABAAABAAAAAAAAAAABAAAAAAAAAAEBAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAABAAEAAAAAAQAAAQAAAAEAAQEAAAABAAEAAAABAAEAAAAAAAABAAEAAAAAAQABAAAAAAABAAAAAAEAAAAAAAAAAAABAQEBAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAEAAQAAAAAAAAAAAQEBAAABAQEBAAEAAAABAQABAQEBAAABAAEAAAAAAAEBAAAAAAABAQAAAAEAAAAAAAAAAQEAAAEAAAAAAAEAAAAAAAAAAAAAAAEAAQAAAAAAAQAAAQAAAAEAAAEAAAAAAAEAAAABAQABAQAAAAAAAAAAAQEAAQAAAAABAAEAAAAAAAAAAAEAAAAAAQAAAAAAAAEAAAAAAAEBAAABAAAAAAAAAAABAQAAAAAAAAAAAAAAAAEAAAABAAEAAAAAAAAAAAAAAAEAAAAAAQEAAAABAAAAAAAAAQEAAQEAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAQAAAQAAAAAAAAABAQEAAAABAAEBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAEAAAEAAAEBAAEAAAEAAAEAAAAAAQAAAAEAAAAAAAAAAAEAAAAAAAAAAQABAAAAAAEAAAEAAQAAAQEAAAAAAQAAAQAAAAEAAAAAAAAAAAAAAQAAAAABAAAAAAAAAAEAAAAAAAABAQAAAQABAQAAAAAAAQAAAAABAAAAAAAAAAEAAAABAAAAAAABAAAAAAABAAAAAAABAAAAAAABAAEBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAEAAAABAQABAQAAAQEBAAAAAQAAAQAAAAAAAAAAAAAAAAAAAAABAAEAAAABAQAAAAABAAAAAAAAAQABAAABAQEAAAAAAAAAAAAAAQAAAQAAAAAAAAABAAAAAQAAAAEAAAAAAQAAAAAAAAAAAAAAAAEBAQAAAAAAAQABAAABAAABAAAAAAAAAAEAAAAAAAAAAAAAAQAAAAABAAAAAAAAAAAAAQEAAAAAAQAAAAEAAQABAAAAAAAAAAEAAAAAAAABAAAAAAEAAAAAAAAAAAAAAAAAAQABAQAAAAEAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAABAAABAAAAAAAAAQAAAAAAAAEBAAABAAAAAQABAQAAAQAAAAAAAAAAAQABAAAAAAEAAAABAAAAAQEAAAAAAAABAAAAAQEAAAAAAAAAAQEAAAABAQEAAAEAAAABAAAAAAAAAAEBAAAAAQAAAAABAQAAAQABAAABAQAAAQABAAAAAQAAAQAAAAAAAAEAAAAAAQABAQEAAQEAAAAAAAAAAQABAAAAAAEAAQEBAAEAAAAAAAEAAAABAAAAAAABAAAAAQABAAAAAAAAAAEAAQAAAAAAAAAAAAABAAEAAQEAAAAAAAAAAAAAAAAAAAAAAQABAAAAAAABAAAAAAABAAABAAAAAQAAAQAAAAAAAQABAQEBAQAAAQEAAAAAAAEAAAEAAAAAAAEBAAABAAAAAQAAAAAAAAAAAAEAAAEAAQAAAAEBAQABAAEAAAAAAAEBAQAAAAAAAAABAAEAAAEAAAAAAAABAAAAAAAAAAABAAABAAABAQEAAAAAAQAAAAAAAQAAAAAAAAEBAAAAAAEBAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAQABAAAAAQAAAAAAAAEBAAAAAQABAAAAAAAAAAABAAAAAAAAAQAAAAEBAQAAAAAAAAEBAAAAAAAAAQAAAAAAAAAAAAEBAAEAAAAAAAABAAAAAAAAAAEAAAAAAAAAAAEAAAAAAQEBAQAAAQABAAEAAAAAAAABAAAAAAAAAAAAAAEBAAABAAEAAQAAAAAAAAABAAAAAQABAQAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAABAAAAAQAAAAAAAAAAAAEAAAEBAAAAAAEBAAABAAAAAAAAAAEAAQAAAAABAAAAAAAAAAABAAEAAAAAAQABAQEAAAAAAAAAAAEBAQEAAQAAAAAAAAAAAAEBAAEAAAAAAAABAAAAAAEAAAEAAAAAAAEAAAAAAAEAAAAAAQEBAQAAAAAAAAEAAAAAAQAAAAABAAAAAAAAAAABAAEAAAAAAAEAAAAAAQAAAQAAAAAAAAEBAQEAAAAAAAAAAAAAAAEAAAEAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAQEAAAAAAAAAAAABAAAAAQAAAAAAAAEAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAAAAAEAAAAAAAAAAAABAAAAAQABAAEAAAAAAAAAAAAAAAAAAQAAAQEBAQEBAAAAAQEBAAAAAAEAAAAAAAAAAAAAAAABAQEAAAAAAAEBAAAAAAABAAAAAAAAAAAAAQEBAAABAAAAAAAAAAAAAAAAAQAAAAABAQAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAABAQAAAAAAAAAAAAEBAAAAAAAAAAABAAEAAAAAAAAAAAEBAAEAAAAAAAAAAAAAAQEAAAEBAAABAQABAAEAAAEBAAAAAAABAQAAAAAAAAEAAQAAAAAAAAEAAAAAAQABAQAAAAEAAQEAAQAAAAAAAQAAAQAAAAAAAAAAAAAAAAAAAAAAAAEAAAEAAAABAAAAAAAAAAAAAQABAQAAAAAAAAAAAAEBAAEAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAABAAEBAQAAAQABAAAAAAAAAQEAAAAAAQAAAAAAAQAAAAABAAAAAAAAAAAAAAAAAAAAAAABAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
    },
    "start": [
      0,
      0
    ],
    "goal": [
      49,
      49
    ],
    "inflation_radius": 1
  },
  "visualization": {
    "show_start": true,
    "show_goal": true,
    "show_path_cost": true,
    "show_candidate_paths": false,
    "show_inflation_area": false
  },
  "request_id": "path_planner_demo-render"
}

```

Successful image response:

```json
{
  "status": "success",
  "image": {
    "content_type": "image/png",
    "data": "base64..."
  },
  "meta": {}
}
```


Error response:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "human-readable error"
  },
  "meta": {}
}
```

## Map And Coordinate Convention

Map array shapes use `[H, W]` or `[H, W, C]`.

Point coordinates use `[x, y]`.

- `x` is the horizontal coordinate and maps to the array column index.
- `y` is the vertical coordinate and maps to the array row index.

Server-side array indexing should use:

```python
value = array[y, x]
```

## Tests

Run the test suite:

```bash
conda activate algo_vis
python -m pytest -q
```
