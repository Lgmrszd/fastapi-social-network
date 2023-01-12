from fastapi.testclient import TestClient

from fastapi_social_network.app import app

client = TestClient(app)


# @pytest.fixture(scope="session")
# def prepare_memory_db(tmp_path_factory):
#     pass


def notest_read_main():
    response = client.get("/")
    assert response.status_code == 404
