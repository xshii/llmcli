#!/usr/bin/env python3
"""
测试 RPC Server - 简单的客户端测试脚本
"""
import json
import subprocess
import sys
import time


class RPCTestClient:
    """简单的 RPC 测试客户端"""

    def __init__(self):
        self.request_id = 0
        self.process = None

    def start_server(self):
        """启动 RPC server"""
        print("Starting RPC server...")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "aicode.cli.main", "server", "--mode", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        time.sleep(1)  # 等待服务器启动
        print("Server started")

    def send_request(self, method: str, params: dict = None) -> dict:
        """发送 RPC 请求"""
        if not self.process:
            raise RuntimeError("Server not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }

        # 发送请求
        request_line = json.dumps(request) + "\n"
        print(f"\n>>> Sending: {method}")
        print(f"    Request: {request}")
        self.process.stdin.write(request_line)
        self.process.stdin.flush()

        # 读取响应（跳过空行和非JSON行）
        max_attempts = 10
        for attempt in range(max_attempts):
            response_line = self.process.stdout.readline()
            if not response_line:
                time.sleep(0.5)
                continue

            response_line = response_line.strip()
            if not response_line:
                continue

            try:
                response = json.loads(response_line)
                print(f"<<< Response: {json.dumps(response, indent=2)}")
                return response
            except json.JSONDecodeError:
                print(f"    Skipping non-JSON line: {response_line[:100]}")
                continue

        raise RuntimeError("No valid response from server")

    def stop_server(self):
        """停止服务器"""
        if self.process:
            try:
                self.send_request("shutdown")
            except:
                pass
            self.process.terminate()
            self.process.wait(timeout=5)
            print("\nServer stopped")

    def run_tests(self):
        """运行测试"""
        try:
            self.start_server()

            # 测试 1: 初始化
            print("\n" + "=" * 50)
            print("TEST 1: Initialize")
            print("=" * 50)
            response = self.send_request("initialize", {"model": "gpt-4"})
            assert response["result"]["success"], "Initialize failed"
            print("✓ Initialize successful")

            # 测试 2: 获取模型列表
            print("\n" + "=" * 50)
            print("TEST 2: Get Models")
            print("=" * 50)
            response = self.send_request("getModels")
            assert response["result"]["success"], "Get models failed"
            models = response["result"]["models"]
            print(f"✓ Found {len(models)} model(s)")
            for model in models:
                print(f"  - {model['name']} ({model['provider']})")

            # 测试 3: 获取配置
            print("\n" + "=" * 50)
            print("TEST 3: Get Config")
            print("=" * 50)
            response = self.send_request("getConfig", {"key": "global.default_model"})
            assert response["result"]["success"], "Get config failed"
            print(f"✓ Default model: {response['result']['value']}")

            # 测试 4: 聊天（会失败因为是 mock API）
            print("\n" + "=" * 50)
            print("TEST 4: Chat")
            print("=" * 50)
            response = self.send_request(
                "chat", {"message": "Hello, AI!", "context": [], "temperature": 0.7}
            )
            if response["result"]["success"]:
                print(f"✓ Chat successful")
                print(f"  Response: {response['result']['response'][:100]}...")
                print(f"  Tokens: {response['result']['tokens']}")
            else:
                print(
                    f"⚠ Chat failed (expected with mock API): {response['result']['error']}"
                )

            # 测试 5: 获取历史
            print("\n" + "=" * 50)
            print("TEST 5: Get History")
            print("=" * 50)
            response = self.send_request("getHistory")
            assert response["result"]["success"], "Get history failed"
            messages = response["result"]["messages"]
            print(f"✓ Found {len(messages)} message(s) in history")

            # 测试 6: 清除历史
            print("\n" + "=" * 50)
            print("TEST 6: Clear History")
            print("=" * 50)
            response = self.send_request("clearHistory")
            assert response["result"]["success"], "Clear history failed"
            print("✓ History cleared")

            print("\n" + "=" * 50)
            print("ALL TESTS PASSED!")
            print("=" * 50)

        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback

            traceback.print_exc()
        finally:
            self.stop_server()


if __name__ == "__main__":
    client = RPCTestClient()
    client.run_tests()
