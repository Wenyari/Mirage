# 创建视频

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
      summary: 创建视频
      deprecated: false
      description: ''
      tags:
        - 视频模型/veo 视频生成/视频统一格式
      parameters:
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Accept
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: stri...                - id
                  - status
                  - status_update_time
                  - enhanced_prompt
                x-apifox-orders:
                  - id
                  - status
                  - status_update_time
                  - enhanced_prompt
              example:
                id: veo3-fast-frames:1757555257-PORrVn9sa9
                status: pending
                status_update_time: 1757555257582
          headers: {}
          x-apifox-name: 成功
      security:
        - bearer: []
      x-apifox-folder: 视频模型/veo 视频生成/视频统一格式
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/7841483/apis/api-418775215-run
components:
  schemas: {}
  securitySchemes:
    BearerAuth:
      type: bearer
      scheme: bearer
      description: 在 Authorization header 中使用 Bearer token 认证
    bearer:
      type: http
      scheme: bearer
servers:
  - url: https://lnapi.com
    description: 正式环境
security:
  - bearer: []

```


# 查询任务

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/video/query:
    get:
      summary: 查询任务
      deprecated: false
      description: |+
        给定一个提示，该模型将返回一个或多个预测的完成，并且还可以返回每个位置的替代标记的概率。

        为提供的提示和参数创建完成

      tags:
        - 视频模型/veo 视频生成/视频统一格式
      parameters:
        - name: id
          in: query
          description: |
            任务ID
          required: true
          example: veo3.1-fast:1770350082-trii1OXZc3
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Accept
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: false
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
        - name: X-Forwarded-Host
          in: header
          description: ''
          required: false
          example: localhost:5173
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties: {}
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
                  status:
                    type: string
                  video_url:
                    type: 'null'
                  enhanced_prompt:
                    type: string
                  status_update_time:
                    type: integer
                required:
                  - id
                  - status
                  - video_url
                  - enhanced_prompt
                  - status_update_time
                x-apifox-orders:
                  - id
                  - status
                  - video_url
                  - enhanced_prompt
                  - status_update_time
              example:
                id: veo3.1-fast:1770350082-trii1OXZc3
                detail:
                  id: veo3.1-fast:1770350082-trii1OXZc3
                  req:
                    model: veo3.1-fast
                    images:
                      - >-
                        https://filesystem.site/cdn/20250702/w8AauvxxPhYoqqkFWdMippJpb9zBxN.png
                    prompt: make animate
                    aspect_ratio: '16:9'
                    enhance_prompt: true
                    enable_upsample: true
                  images:
                    - url: >-
                        https://filesystem.site/cdn/20250702/w8AauvxxPhYoqqkFWdMippJpb9zBxN.png
                      status: completed
                      mediaId: >-
                        CAMaJGUwOTE4MTA4LWQ3MTgtNDk0OS05ZDNiLTIxMjBkM2M5ZGFkYyIDQ0FFKiQzYzY4MjJhZi05ZTVkLTRhNjktOGQ5NC1jYmNjYWVjNDhkMjM
                  status: completed
                  running: false
                  video_url: >-
                    https://pro.filesystem.site/cdn/20260206/9ddbd3bdc67f75a02f766363ebf8eb.mp4
                  created_at: 1770350082099
                  error_sleep: 5000
                  max_retries: 3
                  retry_count: 3
                  completed_at: 1770350328994
                  error_message: >-
                    [403] Request failed with status code 403 | Message:
                    reCAPTCHA evaluation failed | Code: 403 | Status:
                    PERMISSION_DENIED | Reason:
                    PUBLIC_ERROR_SOMETHING_WENT_WRONG | Type:
                    type.googleapis.com/google.rpc.ErrorInfo | URL:
                    /v1/video:batchAsyncGenerateVideoStartImage
                  video_media_id: >-
                    CAUSJDU1YzFjNTliLWYxNzctNGYwYy04YTJkLTI3MGFkMWE4YjkyMxokMTZjYjk1NzUtYWY4Yy00MzQzLWI4NjMtNGQ5YWFiZTZmNzMzIgNDQUUqJGQxZjBhOGExLTUxYjYtNDk5Yy04YWJlLWFhZTU0YzZiMjIxZQ
                  enhanced_prompt: >-
                    Create a vibrant and whimsical animation that features a
                    joyful scene of colorful animals playing together in a sunny
                    meadow, surrounded by blooming flowers and butterflies
                    fluttering by.
                  upsample_status: MEDIA_GENERATION_STATUS_SUCCESSFUL
                  startImageMediaId: >-
                    CAMaJGUwOTE4MTA4LWQ3MTgtNDk0OS05ZDNiLTIxMjBkM2M5ZGFkYyIDQ0FFKiQzYzY4MjJhZi05ZTVkLTRhNjktOGQ5NC1jYmNjYWVjNDhkMjM
                  status_update_time: 1770350329098
                  upsample_video_url: >-
                    https://pro.filesystem.site/cdn/20260206/1b50395bad4c6c7bc22e6ada144951.mp4
                  video_generation_id: 608c00e8de85d8856554201ae115b7c2
                  veo3StartImageMediaId: >-
                    CAMaJGUwOTE4MTA4LWQ3MTgtNDk0OS05ZDNiLTIxMjBkM2M5ZGFkYyIDQ0FFKiQzYzY4MjJhZi05ZTVkLTRhNjktOGQ5NC1jYmNjYWVjNDhkMjM
                  needs_safe_enhancement: true
                  upsample_generation_id: d1f0a8a1-51b6-499c-8abe-aae54c6b221e_upsampled
                  video_generation_error: >-
                    your request contains unsafe prompt or images, such as porn,
                    violence, minors etc., has been rejected by google, please
                    change your prompt or images and try again
                  video_generation_status: MEDIA_GENERATION_STATUS_SUCCESSFUL
                status: completed
                video_url: >-
                  https://pro.filesystem.site/cdn/20260206/1b50395bad4c6c7bc22e6ada144951.mp4
                status_update_time: 1770350329098
          headers: {}
          x-apifox-name: 成功
      security:
        - bearer: []
      x-apifox-folder: 视频模型/veo 视频生成/视频统一格式
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/7841483/apis/api-418775217-run
components:
  schemas: {}
  securitySchemes:
    BearerAuth:
      type: bearer
      scheme: bearer
      description: 在 Authorization header 中使用 Bearer token 认证
    bearer:
      type: http
      scheme: bearer
servers:
  - url: https://lnapi.com
    description: 正式环境
security:
  - bearer: []

```