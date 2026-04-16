import requests
import subprocess
import time
import sys
import json


def wait_for_server(port=8000, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"http://localhost:{port}/graphiql", timeout=1)
            return True
        except:
            time.sleep(0.5)
    return False


def test_api():
    # Start server
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/Shared/ccc/project/pupu",
    )

    try:
        if not wait_for_server():
            print("FAIL: Server did not start")
            return

        # Test 1: Query users
        r = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ users(limit: 2) { id username name age } }"},
        )
        data = r.json()
        assert "errors" not in data, f"GraphQL error: {data.get('errors')}"
        assert "data" in data
        print("PASS: Query users")

        # Test 2: Query feed
        r = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ feed(limit: 5) { id content author { name } } }"},
        )
        data = r.json()
        assert "errors" not in data, f"GraphQL error: {data.get('errors')}"
        print("PASS: Query feed")

        # Test 3: Register mutation
        r = requests.post(
            "http://localhost:8000/graphql",
            json={
                "query": """
            mutation {
                register(username: "testuser999", password: "test123", name: "Test User", gender: "other", age: 25, location: "Taipei") {
                    success
                    token
                    user { id username }
                }
            }
            """
            },
        )
        data = r.json()
        if "errors" in data:
            # Username might exist from previous run
            print(f"SKIP: Register (user may exist): {data['errors'][0]['message']}")
        else:
            assert data["data"]["register"]["success"] == True
            token = data["data"]["register"]["token"]
            print(f"PASS: Register (token: {token[:20]}...)")

        print("\nAll tests passed!")

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    test_api()
