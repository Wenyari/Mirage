#!/usr/bin/env python3
"""
Debug script to get detailed error information for register endpoint
"""
import requests
import json
import sys
import traceback

def debug_register():
    try:
        print("Testing register endpoint...")

        # Test with query parameters (same as user's curl)
        response = requests.post(
            "http://localhost:5000/api/auth/register",
            params={
                "email": "2536331283@qq.com",
                "code": "494023",
                "password": "wanglei123."
            },
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
                "Accept": "*/*",
                "Host": "localhost:5000",
                "Connection": "keep-alive"
            }
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")

        if response.status_code == 500:
            print("\n500 Error detected. Checking current code...")

            # Import app to check current code
            sys.path.insert(0, '.')
            try:
                from app.api.auth import register
                print("Register function imported successfully")
                print(f"Function: {register}")
            except Exception as e:
                print(f"Error importing register function: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"Error in debug script: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_register()
