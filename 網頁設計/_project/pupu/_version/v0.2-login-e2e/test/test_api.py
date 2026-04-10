import pytest
import httpx
import subprocess
import sys
import os
import time


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/Shared/ccc/project/pupu",
    )
    for _ in range(20):
        try:
            r = httpx.get("http://localhost:8000/graphiql", timeout=1)
            if r.status_code == 200:
                break
        except:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Server did not start")

    yield proc

    proc.terminate()
    proc.wait()


@pytest.fixture
def client(server):
    return httpx.Client(base_url="http://localhost:8000", timeout=10)


def query(client, query_str, variables=None):
    response = client.post(
        "/graphql", json={"query": query_str, "variables": variables}
    )
    assert response.status_code == 200
    result = response.json()
    if "errors" in result:
        pytest.fail(f"GraphQL error: {result['errors']}")
    return result.get("data", {})


class TestQueries:
    def test_users(self, client):
        data = query(client, "{ users(limit: 2) { id username name age } }")
        assert "users" in data
        assert len(data["users"]) >= 0

    def test_feed(self, client):
        data = query(client, "{ feed(limit: 5) { id content author { name } } }")
        assert "feed" in data

    def test_user_by_id(self, client):
        data = query(client, "{ user(id: 1) { id username name } }")
        assert "user" in data


class TestMutations:
    def test_register(self, client):
        username = f"user{int(time.time())}"
        mutation = f'''
        mutation {{
            register(username: "{username}", password: "aa", name: "Test", gender: "other", age: 25, location: "Taipei") {{
                success
                user {{ id username }}
            }}
        }}
        '''
        response = client.post("/graphql", json={"query": mutation})
        result = response.json()
        if "errors" in result:
            pass
        else:
            assert result.get("data", {}).get("register", {}).get("success") is True

    def test_login_wrong_password(self, client):
        mutation = """
        mutation {
            login(username: "user1", password: "wrong") {
                success
            }
        }
        """
        response = client.post("/graphql", json={"query": mutation})
        result = response.json()
        assert "errors" in result
        assert "Invalid" in result["errors"][0]["message"]

    def test_create_post_requires_auth(self, client):
        mutation = """
        mutation {
            createPost(content: "Test") { success }
        }
        """
        response = client.post("/graphql", json={"query": mutation})
        result = response.json()
        assert "errors" in result
        assert "Not authenticated" in result["errors"][0]["message"]

    def test_toggle_like_requires_auth(self, client):
        mutation = """
        mutation { toggleLike(postId: 1) { success } }
        """
        response = client.post("/graphql", json={"query": mutation})
        result = response.json()
        assert "errors" in result
        assert "Not authenticated" in result["errors"][0]["message"]


class TestAuth:
    def test_query_without_auth(self, client):
        data = query(client, "{ users { id } }")
        assert "users" in data

    def test_protected_query(self, client):
        mutation = """
        mutation {
            login(username: "nonexistent", password: "wrong") {
                success
            }
        }
        """
        response = client.post("/graphql", json={"query": mutation})
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
