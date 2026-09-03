from app.network import protocol


def test_envelope_roundtrip():
    env = protocol.sms_job("msg-1", "camp-1", "+919876543210", "Hello Rahul", sim_slot=1)
    raw = env.to_json()
    parsed = protocol.Envelope.from_json(raw)

    assert parsed.type == protocol.SMS_JOB
    assert parsed.id == env.id
    assert parsed.payload["message_id"] == "msg-1"
    assert parsed.payload["campaign_id"] == "camp-1"
    assert parsed.payload["phone_number"] == "+919876543210"
    assert parsed.payload["text"] == "Hello Rahul"
    assert parsed.payload["sim_slot"] == 1


def test_pair_request_shape():
    env = protocol.pair_request("dev-1", "My PC", "123456")
    assert env.type == protocol.PAIR_REQUEST
    assert env.payload == {"device_id": "dev-1", "device_name": "My PC", "pairing_code": "123456"}


def test_auth_shape():
    env = protocol.auth("dev-1", "token-abc")
    assert env.type == protocol.AUTH
    assert env.payload == {"device_id": "dev-1", "pairing_token": "token-abc"}
