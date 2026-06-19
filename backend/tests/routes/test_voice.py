# backend/test/routes/test_voice.py
import io
import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime

from backend.main import app
import backend.routes.voice as voice_mod
from backend.services import stt as stt_mod


@pytest.fixture(scope="function")
def client(monkeypatch):
    # Activa GRIDFS y provee fakes
    monkeypatch.setattr(voice_mod, "GRIDFS_ENABLED", True, raising=False)

    class FakeGridOut:
        def __init__(self, _id, data, meta, filename="file.webm"):
            self._id = _id
            self._data = data
            self.metadata = meta
            self.length = len(data)
            self.filename = filename
            self._pos = 0

        async def read(self, n):
            if self._pos >= len(self._data):
                return b""
            chunk = self._data[self._pos:self._pos+n]
            self._pos += len(chunk)
            return chunk

    class FakeBucket:
        def __init__(self):
            self.store = {}

        async def upload_from_stream(self, filename, source, metadata, chunk_size_bytes=262144):
            _id = ObjectId()
            self.store[str(_id)] = {"filename": filename, "data": source, "metadata": metadata, "uploadDate": datetime.utcnow()}
            return _id

        async def open_download_stream(self, oid):
            doc = self.store.get(str(oid))
            if not doc:
                raise RuntimeError("not found")
            return FakeGridOut(str(oid), doc["data"], doc["metadata"], filename=doc["filename"])

    class FakeCursor:
        def __init__(self, docs):
            self._docs = docs

        def sort(self, *args, **kwargs):  # chainable
            return self

        def skip(self, n):
            self._docs = self._docs[n:]
            return self

        def limit(self, n):
            self._docs = self._docs[:n]
            return self

        def __aiter__(self):
            self._it = iter(self._docs)
            return self

        async def __anext__(self):
            try:
                return next(self._it)
            except StopIteration:
                raise StopAsyncIteration

    class FakeFilesCol:
        def __init__(self, bucket):
            self.bucket = bucket

        async def count_documents(self, filt):
            return len([
                1 for _id, d in self.bucket.store.items()
                if d["metadata"].get("kind") == "voice"
            ])

        def find(self, filt):
            docs = []
            for _id, d in self.bucket.store.items():
                if d["metadata"].get("kind") != "voice":
                    continue
                doc = {
                    "_id": ObjectId(_id),
                    "filename": d["filename"],
                    "length": len(d["data"]),
                    "metadata": d["metadata"],
                    "uploadDate": d["uploadDate"],
                }
                docs.append(doc)
            return FakeCursor(docs)

    fake_bucket = FakeBucket()
    fake_files = FakeFilesCol(fake_bucket)

    monkeypatch.setattr(voice_mod, "_fs_bucket", fake_bucket, raising=False)
    monkeypatch.setattr(voice_mod, "_fs_files", fake_files, raising=False)

    # Parchea STT para no depender de servicio externo
    async def _fake_transcribe_audio(data: bytes, mime: str, lang: str = "es"):
        return {"text": "hola mundo", "language": lang, "model": "test", "confidence": 0.99}

    monkeypatch.setattr(stt_mod, "transcribe_audio", _fake_transcribe_audio, raising=False)

    return TestClient(app)


def test_transcribe_and_list(client):
    # Transcribe (sube audio)
    audio = b"\x00\x01fakewebmdata"
    files = {"file": ("prueba.webm", io.BytesIO(audio), "audio/webm")}
    data = {"sender": "web-123", "session_id": "sess-1", "lang": "es", "stt": "auto"}
    r = client.post("/api/voice/transcribe", files=files, data=data)
    assert r.status_code == 200, r.text
    res = r.json()
    # Debe regresar id (no None), transcript y mime
    assert res["id"] is not None
    assert res["transcript"] == "hola mundo"
    assert res["mime"] == "audio/webm"

    # List (debe traer 1)
    r_list = client.get("/api/voice/list")
    assert r_list.status_code == 200
    payload = r_list.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["transcript"] == "hola mundo"
    assert item["sender"] == "web-123"
    assert item["session_id"] == "sess-1"

    # Stream directo (atajo)
    _id = item["id"]
    r_stream = client.get(f"/api/voice/{_id}")
    assert r_stream.status_code == 200
    assert r_stream.headers.get("Content-Type") == "audio/webm"
    assert r_stream.content == audio
