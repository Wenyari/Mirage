# 用户 CDK 兑换接口

接口路径：`POST /api/wallet/redeem`
权限：需要登录（JWT）

请求 Body：
```json
{
  "code": "CDK-XXXX-YYYY"
}
```

成功响应：
```json
{
  "code": 200,
  "msg": "CDK redeemed successfully",
  "data": {
    "added_points": 500,
    "current_balance": 1500.0
  }
}
```

错误响应举例：
- 兑换码不存在 / 无效：
```json
{ "code": 400, "msg": "Invalid CDK code", "data": null }
```
- 兑换码已使用：
```json
{ "code": 400, "msg": "CDK has already been used", "data": null }
```
- 兑换码已过期：
```json
{ "code": 400, "msg": "CDK has expired", "data": null }
```

行为说明：
- 后端使用 `app.services.pay_service.redeem_cdk(user_id, code)` 执行兑换逻辑（事务 + 悲观锁）。
- 成功后会更新用户余额并写入流水（`transactions`）。


