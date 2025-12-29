"""
Flask API 服务启动入口
生产环境使用: gunicorn -w 4 -b 0.0.0.0:5000 run:app
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # 开发环境直接运行
    app.run(host='0.0.0.0', port=5000, debug=True)
