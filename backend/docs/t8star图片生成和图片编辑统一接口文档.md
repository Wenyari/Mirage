# Generations 通用 (图生图&文生图)

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
      summary: Generations 通用 (图生图&文生图)
      deprecated: false
      description: 如果支持参考图，例如 flux-kontext ，参考图url 放 prompt 中空格隔开
      tags:
        - 绘图模型/OpenAI Dall-e 格式
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
            default: Bearer {{YOUR_API_KEY}}
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                prompt:
                  type: string
                size:
                  type: string
                  description: 最终会转换成比例，建议直接使用 aspect_ratio
                aspect_ratio:
                  type: string
                  description: 21:9, 16:9, 4:3, 3:2, 1:1, 2:3, 3:4, 9:16, 9:21
                image:
                  type: array
                  items:
                    type: string
                  description: 部分模型支持
              required:
                - model
                - prompt
              x-apifox-orders:
                - model
                - prompt
                - size
                - aspect_ratio
                - image
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
                x-apifox-orders: []
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 绘图模型/OpenAI Dall-e 格式
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-302915860-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```

# Edits 通用 (图像编辑)

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/images/edits:
    post:
      summary: Edits 通用 (图像编辑)
      deprecated: false
      description: >+
        official docs:  

        https://platform.openai.com/docs/api-reference/images/createEdit


        ## Image Editing Request Parameters


        | Parameter         | Type                | Required |
        Description                                                                                                                                          
        |

        |------------------|---------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------|

        | **image**         | `file` or `file array` | ✅       | The image(s) to
        edit. Must be a supported image file or array. <br> - **gpt-image-1**:
        PNG, WEBP, or JPG, each <25MB. <br> - **dall-e-2**: 1 square PNG <4MB. |

        | **prompt**        | `string`            | ✅       | A text description
        of the desired image(s). <br> - Max length: 1000 chars for **dall-e-2**,
        32000 chars for **gpt-image-1**.                          |

        | **mask**          | `file`              |         | Optional PNG mask
        image. Transparent areas (alpha = 0) indicate regions to edit. <br> Must
        match size of image and be <4MB. Applies to first image.   |

        | **model**         | `string`            |         | Model to use:
        `"dall-e-2"` or `"gpt-image-1"`. <br> Defaults to `"dall-e-2"`, unless
        `gpt-image-1`-specific parameters are used.                       |

        | **n**             | `integer` or `null` |         | Number of images
        to generate. Must be between 1 and 10. <br> Default:
        `1`.                                                                           
        |

        | **quality**       | `string` or `null`  |         | For
        **gpt-image-1** only. Options: `"high"`, `"medium"`, `"low"`. <br>
        Default:
        `"auto"`.                                                             |

        | **response_format** | `string` or `null` |         | Response format.
        Options: `"url"` or `"b64_json"`. <br> Only `"dall-e-2"` supports
        `"url"` (valid for 60 minutes).                                     |

        | **size**          | `string` or `null`  |         | Image size: <br> -
        **gpt-image-1**: `"1024x1024"`, `"1536x1024"`, `"1024x1536"`, `"auto"`
        (default) <br> - **dall-e-2**: `"256x256"`, `"512x512"`, `"1024x1024"` |

      tags:
        - 绘图模型/OpenAI Dall-e 格式
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
            default: Bearer {{YOUR_API_KEY}}
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                image:
                  description: 支持多图
                  example: E:\\Desktop\\gpt\\icon_samll2.png
                  type: string
                  format: binary
                prompt:
                  example: 带上眼镜
                  type: string
                model:
                  description: 支持 gpt-image-1、flux-kontext-pro、flux-kontext-max
                  example: gpt-image-1
                  type: string
              required:
                - image
                - prompt
                - model
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
                x-apifox-orders: []
              example:
                created: 1713833628
                data:
                  - b64_json: ...
                usage:
                  total_tokens: 100
                  input_tokens: 50
                  output_tokens: 50
                  input_tokens_details:
                    text_tokens: 10
                    image_tokens: 40
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 绘图模型/OpenAI Dall-e 格式
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3868318/apis/api-288978020-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```