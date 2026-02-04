"""
极验 (Geetest) 行为验证 4.0 工具类
"""
import hmac
import hashlib
import time
import requests
import os
from flask import current_app

def verify_geetest(lot_number: str, captcha_output: str, pass_token: str, gen_time: str) -> bool:
    """
    验证极验 (Geetest) 4.0 验证码

    Args:
        lot_number: 验证流水号
        captcha_output: 验证输出信息
        pass_token: 验证通过标识
        gen_time: 验证生成时间

    Returns:
        bool: 验证是否通过
    """
    # 1. 获取配置
    captcha_id = os.getenv("GEETEST_ID")
    captcha_key = os.getenv("GEETEST_KEY")
    api_server = "http://gcaptcha4.geetest.com/validate"

    if not captcha_id or not captcha_key:
        current_app.logger.error("GEETEST_ID or GEETEST_KEY not configured")
        # 如果未配置，开发环境下可能允许通过，但在生产环境应失败
        # 这里为了安全默认失败，或者根据需要调整
        return False

    # 2. 生成签名
    # sign_token = hmac_sha256(lot_number, captcha_key)
    if not lot_number:
        return False
        
    try:
        sign_token = hmac.new(
            captcha_key.encode('utf-8'), 
            lot_number.encode('utf-8'), 
            digestmod=hashlib.sha256
        ).hexdigest()
    except Exception as e:
        current_app.logger.error(f"Geetest signature generation failed: {e}")
        return False

    # 3. 构造请求参数
    query = {
        "lot_number": lot_number,
        "captcha_output": captcha_output,
        "pass_token": pass_token,
        "gen_time": gen_time,
        "sign_token": sign_token
    }

    # 4. 发送验证请求
    try:
        response = requests.post(api_server, params=query, timeout=5)
        
        if response.status_code != 200:
            current_app.logger.error(f"Geetest API error: {response.status_code}")
            return False

        result = response.json()
        
        # result: {"result": "success", "reason": "", "captcha_args": {...}}
        if result.get('result') == 'success':
            current_app.logger.info(f"Geetest verification passed for lot_number: {lot_number}")
            return True
        else:
            current_app.logger.warning(f"Geetest verification failed: {result.get('reason')} (lot: {lot_number})")
            return False

    except Exception as e:
        current_app.logger.error(f"Geetest validation request failed: {e}")
        # Fail open or closed? 通常为了安全 fail closed
        return False
