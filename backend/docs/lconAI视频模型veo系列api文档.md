# 异步视频生成

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/videos:
    post:
      summary: 异步视频生成
      deprecated: false
      description: ''
      tags:
        - 视频生成
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{key}}
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                model:
                  description: 模型名称，veo_3_1-fast和sora-2等都可使用
                  example: sora-2
                  type: string
                prompt:
                  description: 提示词
                  example: 猫咪听歌摇头晃脑，下大雨
                  type: string
                size:
                  type: string
                  description: 尺寸，默认为 720x1280。可选：720x1280，1280x720 （竖屏或者横屏的意思）
                  example: 720x1280
                seconds:
                  type: integer
                  description: 秒数
                  example: 10
                input_reference:
                  description: 图片参考-使用 File格式 ，可传多张
                  example: data:image/jpeg;base64
                  type: string
                  format: binary
                character_url:
                  description: 创建角色需要的视频链接，注意视频中一定不能出现真人，否则会失败
                  example: >-
                    https://filesystem,site/cdn/20251030/javYrU4etHVFDgg8by7mVTWHIMOZy.mp4
                  type: string
                character_timestamps:
                  description: 视频角色出现的秒数范围，格式{start},{end},注意end-start 的范围 1~3秒
                  example: 1,3
                  type: string
                image:
                  description: 图片参考-如需Base64的时候使用
                  example: '**'
                  type: string
                images:
                  type: array
                  items:
                    type: string
                  description: 多图数组-如需BASE64数组的时候可传输
                  example:
                    - png1
                    - png2
              required:
                - model
                - prompt
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  object:
                    type: string
                  model:
                    type: string
                  status:
                    type: string
                    title: 状态码
                    description: queued，processing，completed，failed，cancelled
                  progress:
                    type: integer
                  created_at:
                    type: integer
                  size:
                    type: string
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - size
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - size
              example:
                id: video_bbfbc1d2-ab22-44ca-b9dd-bc16983acac2
                object: video
                model: sora_video2
                status: queued
                progress: 0
                created_at: 1761635478
                size: 720x720
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/7641932/apis/api-399018224-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://n.lconai.com
    description: 主站环境
  - url: https://v.lconai.com
    description: 分站环境
security: []

```


# 任务查询进度

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/videos/{task_id}:
    get:
      summary: 任务查询进度
      deprecated: false
      description: ''
      tags:
        - 视频生成/Veo3
      parameters:
        - name: task_id
          in: path
          description: ''
          required: true
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          example: application/json
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: true
          example: '{{Authorization}}'
          schema:
            type: string
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  object:
                    type: string
                  model:
                    type: string
                  status:
                    description: 任务状态
                    type: string
                  progress:
                    description: 进度百分比
                    type: integer
                  created_at:
                    type: integer
                  completed_at:
                    type: integer
                  expires_at:
                    type: integer
                  seconds:
                    type: string
                  size:
                    type: string
                  remixed_from_video_id:
                    type: string
                  error:
                    type: object
                    properties:
                      message:
                        type: string
                      code:
                        type: string
                    required:
                      - message
                      - code
                    x-apifox-orders:
                      - message
                      - code
                  video_url:
                    type: string
                    description: 视频地址
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - expires_at
                  - seconds
                  - size
                  - remixed_from_video_id
                  - error
                  - video_url
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - expires_at
                  - seconds
                  - size
                  - video_url
                  - remixed_from_video_id
                  - error
              example:
                id: string
                object: string
                model: string
                status: string
                progress: 0
                created_at: 1234567890
                completed_at: 1234567890
                expires_at: 1234567890
                seconds: string
                size: string
                remixed_from_video_id: string
                error:
                  message: string
                  code: string
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成/Veo3
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/7641932/apis/api-399018229-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://n.lconai.com
    description: 主站环境
  - url: https://v.lconai.com
    description: 分站环境
security: []

```