# 创建图片（也可编辑图片，推荐使用）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/images/generations:
    post:
      summary: 创建图片（也可编辑图片，推荐使用）
      deprecated: false
      description: "给定文本提示和/或输入图片，模型将生成新的图片。OpenAI 提供多种强大的图像生成模型，可以根据自然语言描述创建、编辑和修改图像。目前支持的模型包括：\nGPT-Image-1.5\tOpenAI最新图片模型，支持多图片编辑功能，能够基于多个输入图像创建新的组合图像"
      tags:
        - 图片生成/通用接口
      parameters:
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
      requestBody:
        content:
          application/json:
            schema:
              type: object
              title: 创建图片请求
              description: 用于创建AI生成图片的请求参数
              properties:
                prompt:
                  type: string
                  title: 提示词
                  description: 期望生成图片的文本描述，建议使用具体和详细的描述，包含关键的视觉元素，指定期望的艺术风格，描述构图和视角。
                  maxLength: 4000
                model:
                  type: string
                  title: 模型
                  description: 用于图像生成的模型。
                  enum:
                    - gpt-image-1.5
                    - gemini-2.5-flash-image
                    - gemini-3-pro-image-preview
                  default: gpt-image-1.5
                  x-apifox-enum:
                    - value: gpt-image-1.5
                      name: ''
                      description: ''
                    - value: gemini-2.5-flash-image
                      name: ''
                      description: ''
                    - value: gemini-3-pro-image-preview
                      name: ''
                      description: ''
                'n':
                  type: integer
                  title: 生成数量
                  description: 要生成的图片数量。
                  minimum: 1
                  maximum: 10
                  default: 1
                  nullable: true
                response_format:
                  type: string
                  title: 响应格式
                  description: 返回生成图片的格式，有些是强制返回固定格式。
                  enum:
                    - url
                    - b64_json
                  default: url
                  nullable: true
                size:
                  type: string
                  title: 图片尺寸
                  description: 生成图片的尺寸（每个模型的尺寸请参考对应模型说明）。
                  enum:
                    - 256x256
                    - 512x512
                    - 1024x1024
                    - 1792x1024
                    - 1024x1792
                  default: 1024x1024
                  nullable: true
                image:
                  type: array
                  items:
                    type: string
                  title: 需要编辑的图片（文生图移除参数）
                  description: 可以是链接，可以是 b64
              required:
                - prompt
              x-apifox-orders:
                - prompt
                - model
                - 'n'
                - response_format
                - size
                - image
            examples:
              '1':
                value:
                  model: gpt-image-1.5
                  prompt: 一只可爱的小海獭
                  'n': 1
                  size: 1024x1024
                  response_format: url
                summary: 文生图
              '2':
                value:
                  model: gemini-3-pro-image-preview
                  prompt: 画个类似的图
                  image:
                    - >-
                      https://res-oiioii-sg.hogiai.cn/mkbe58xz_c231bdaae5a013ae.png?Content-Disposition=inline&x-tos-process=image%2Fresize%2Cw_2048%2Fformat%2Cjpeg&X-Tos-Algorithm=TOS4-HMAC-SHA256&X-Tos-Content-Sha256=UNSIGNED-PAYLOAD&X-Tos-Credential=AKLTYWQ3Y2QxN2I2ZmJiNGU0MzhjNWFhYzU5M2JhZGUxZTA%2F20260112%2Ftos-ap-southeast-1.volces.com%2Ftos%2Frequest&X-Tos-Date=20260112T164224Z&X-Tos-Expires=259200&X-Tos-SignedHeaders=host&X-Tos-Signature=5f1e92085a1ef7dc88ff31bb748ebb690cbf944afb23664d5e60150a80c9534f
                  'n': 1
                  size: 1024x1024
                summary: 单图生图
              '3':
                value:
                  prompt: 合并两张图片
                  image:
                    - >-
                      https://cdn.apifox.com/app/project-icon/custom/20251230/a7af9651-4bb9-4dcc-a908-5f4013b529cb.png
                    - >-
                      https://video.aicns.cn/uploads/logo/logo_1763545703449_ea6c0056.png
                  model: gemini-2.5-flash-image
                  'n': 1
                  size: 832x1248
                  response_format: url
                summary: 多图生图
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                title: 图片生成响应
                description: 所有图片生成接口的统一响应格式
                properties:
                  created:
                    type: integer
                    title: 创建时间戳
                    description: 响应创建的时间戳
                  data:
                    type: array
                    title: 图片数据列表
                    description: 生成的图片对象列表
                    items:
                      type: object
                      title: 图片对象
                      description: 单个生成的图片信息
                      properties:
                        b64_json:
                          type: string
                          title: Base64编码图片
                          description: 如果response_format为b64_json，则包含生成图片的base64编码JSON
                        url:
                          type: string
                          title: 图片URL
                          description: 如果response_format为url（默认），则包含生成图片的URL
                          format: uri
                        revised_prompt:
                          type: string
                          title: 修改后的提示词
                          description: 如果提示有任何修改，则包含用于生成图片的修改后的提示
                      x-apifox-orders:
                        - b64_json
                        - url
                        - revised_prompt
                  usage:
                    type: object
                    title: 使用情况统计
                    description: API调用的令牌使用情况（仅适用于gpt-image-1）
                    properties:
                      total_tokens:
                        type: integer
                        title: 总令牌数
                        description: 使用的总令牌数
                      input_tokens:
                        type: integer
                        title: 输入令牌数
                        description: 输入使用的令牌数
                      output_tokens:
                        type: integer
                        title: 输出令牌数
                        description: 输出使用的令牌数
                      input_tokens_details:
                        type: object
                        title: 输入令牌详情
                        description: 输入令牌的详细信息（文本令牌和图像令牌）
                        properties:
                          text_tokens:
                            type: integer
                            title: 文本令牌数
                            description: 文本输入使用的令牌数
                          image_tokens:
                            type: integer
                            title: 图像令牌数
                            description: 图像输入使用的令牌数
                        x-apifox-orders:
                          - text_tokens
                          - image_tokens
                    x-apifox-orders:
                      - total_tokens
                      - input_tokens
                      - output_tokens
                      - input_tokens_details
                required:
                  - created
                  - data
                x-apifox-orders:
                  - created
                  - data
                  - usage
              example:
                created: 1753687182
                data:
                  - revised_prompt: >-
                      A cute little sea otter floating on its back in a calm,
                      clear blue ocean. The sea otter has a playful expression,
                      with soft brown fur and little whiskers. There are gentle
                      ripples in the water, and the sunlight creates sparkling
                      reflections. In the background, distant greenery and
                      cliffs can be seen.
                    url: >-
                      https://dalleprodsec.blob.core.windows.net/private/images/48a5fef6-e2db-4c0f-98ad-1441f36ebdff/generated_00.png?se=2025-07-29T07%3A19%3A51Z&sig=CinStVp6nIPqx2SJ41qjQoEscnWcxz9H4iyrVn853jo%3D&ske=2025-08-04T06%3A20%3A20Z&skoid=e52d5ed7-0657-4f62-bc12-7e5dbb260a96&sks=b&skt=2025-07-28T06%3A20%3A20Z&sktid=33e01921-4d64-4f8c-a055-5bdaffd5e33d&skv=2020-10-02&sp=r&spr=https&sr=b&sv=2020-10-02
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 图片生成/通用接口
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/7641932/apis/api-399018201-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: https://n.lconai.com
    description: 主站环境
security: []

```