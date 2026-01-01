#!/usr/bin/env python3
"""
Test script to reproduce register 500 error
"""
import requests
import json

def test_register():
    # First, send verification code
    print("Sending verification code...")
    code_resp = requests.post(
        "http://localhost:5000/api/auth/code",
        params={"email": "2536331283@qq.com"}
    )
    print(f"Code response: {code_resp.status_code} {code_resp.text}")

    if code_resp.status_code != 200:
        return

    # Try to register with the code we just got
    print("\nTrying to register...")
    register_resp = requests.post(
        "http://localhost:5000/api/auth/register",
        params={
            "email": "2536331283@qq.com",
            "code": "494023",  # We'll get this from the email
            "password": "wanglei123."
        }
    )
    print(f"Register response: {register_resp.status_code} {register_resp.text}")

if __name__ == "__main__":
    test_register()
