from storage.session_store import create_session, save_json, load_json


sid = create_session()
print("Session created:", sid)

sample = {"test": "working"}
save_json(sid, "test.json", sample)

loaded = load_json(sid, "test.json")
print("Loaded:", loaded)
