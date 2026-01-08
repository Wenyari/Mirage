"""
Cloudflare Turnstile 验证工具
用于防止机器人攻击
"""
import os
import requests
from flask import current_app


def verify_turnstile(token: str, ip: str = None) -> bool:
    """
    验证 Cloudflare Turnstile Token

    Args:
        token: 前端 Turnstile 组件返回的 token
        ip: 用户 IP 地址 (可选)

    Returns:
        bool: 验证是否通过
    """
    if not token:
        current_app.logger.warning("Turnstile token is missing")
        return False

    # Cloudflare Turnstile 验证 URL
    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    # 从环境变量读取 Secret Key
    secret_key = os.getenv("TURNSTILE_SECRET_KEY")
    if not secret_key:
        current_app.logger.error("TURNSTILE_SECRET_KEY not configured in environment variables")
        return False

    # 构建验证请求
    payload = {
        "secret": secret_key,
        "response": token
    }

    # 如果提供了 IP 地址，加入请求
    if ip:
        payload["remoteip"] = ip

    try:
        # 发送验证请求
        response = requests.post(verify_url, data=payload, timeout=10)
        result = response.json()

        # 检查验证结果
        if result.get("success"):
            current_app.logger.info(f"Turnstile verification successful for IP: {ip}")
            return True
        else:
            error_codes = result.get("error-codes", [])
            current_app.logger.warning(f"Turnstile verification failed: {error_codes}")
            return False

    except requests.exceptions.Timeout:
        current_app.logger.error("Turnstile verification timeout - failing closed for security")
        return False
    except Exception as e:
        current_app.logger.exception(f"Turnstile verification error: {e}")
        return False
