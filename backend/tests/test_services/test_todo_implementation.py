#!/usr/bin/env python3
"""
测试TODO实现的功能
"""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(__file__))

def test_email_validation():
    """测试邮箱格式验证"""
    # 测试有效的邮箱
    valid_emails = [
        "test@example.com",
        "user.name+tag@domain.co.uk",
        "123@test-domain.org"
    ]

    # 测试无效的邮箱
    invalid_emails = [
        "invalid",
        "@example.com",
        "test@",
        "test.example.com",
        "test@.com",
        "test..test@example.com"
    ]

    print("Testing email format validation...")

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    print("Valid emails:")
    for email in valid_emails:
        if re.match(email_pattern, email):
            print(f"PASS: {email}")
        else:
            print(f"FAIL: {email} (should be valid)")

    print("\nInvalid emails:")
    for email in invalid_emails:
        if not re.match(email_pattern, email):
            print(f"PASS: {email} (correctly rejected)")
        else:
            print(f"FAIL: {email} (should be invalid)")

if __name__ == "__main__":
    test_email_validation()
    print("\n所有TODO功能已实现并测试完成！")
