安装requirements.txt依赖： pip install -r requirements.txt

运行后端：python -u -m uvicorn app.main:app --host 0.0.0.0 --port 8000

另起一个终端进行测试：python test_api.py