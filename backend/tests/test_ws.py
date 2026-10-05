import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import (
    OTHER_USER,
    TEST_USER,
    auth_header,
    connect_socket,
    create_room,
    join_room,
    login,
    register_user,
    ws_token,
)

import models
from connection_manager import manager


@pytest.fixture
def room(client):
    register_user(client)
    return create_room(client, auth_header(client))


def join_as_other_user(client, room_id):
    register_user(client, OTHER_USER)
    join_room(client, room_id, auth_header(client, OTHER_USER))


def close_code(client, token, room_id):
    with connect_socket(client, token, room_id) as socket:
        with pytest.raises(WebSocketDisconnect) as rejection:
            socket.receive_json()
    return rejection.value.code


def test_two_members_exchange_message(client, db, room):
    join_as_other_user(client, room["id"])
    owner_token = ws_token(client)
    other_token = ws_token(client, OTHER_USER)

    with connect_socket(client, owner_token, room["id"]) as owner_socket:
        with connect_socket(client, other_token, room["id"]) as other_socket:
            assert len(manager.connections[room["id"]]) == 2

            owner_socket.send_json({"type": "message.send", "content": "hello room"})

            received = other_socket.receive_json()
            assert received["type"] == "message.new"
            assert received["message"]["content"] == "hello room"
            assert received["message"]["room_id"] == room["id"]
            assert received["message"]["sender_id"] == room["created_by"]
            assert received["message"]["id"] >= 1
            assert received["message"]["created_at"]

            # The sender gets its own message back, with the server id and timestamp.
            echoed = owner_socket.receive_json()
            assert echoed["type"] == "message.new"
            assert echoed["message"]["id"] == received["message"]["id"]
            assert echoed["message"]["created_at"] == received["message"]["created_at"]

            stored = (
                db.query(models.Message)
                .filter(models.Message.id == received["message"]["id"])
                .one()
            )
            assert stored.content == "hello room"
            assert stored.sender_id == room["created_by"]
            assert stored.room_id == room["id"]

    assert room["id"] not in manager.connections


def test_non_member_is_rejected(client, room):
    register_user(client, OTHER_USER)
    token = ws_token(client, OTHER_USER)

    assert close_code(client, token, room["id"]) == 4403
    assert room["id"] not in manager.connections


def test_invalid_token_is_rejected(client, room):
    join_as_other_user(client, room["id"])
    access_token = login(client)
    valid_ws_token = ws_token(client)

    rejected = [
        "not-a-token",
        "Bearer something",
        access_token,  # a long lived access token is not a websocket ticket
        valid_ws_token[:-2] + "xx",  # tampered signature
    ]
    for token in rejected:
        assert close_code(client, token, room["id"]) == 4401

    with client.websocket_connect(f"/ws?room_id={room['id']}") as socket:
        with pytest.raises(WebSocketDisconnect) as rejection:
            socket.receive_json()
    assert rejection.value.code == 4401
    assert room["id"] not in manager.connections


def test_typing_is_broadcast_to_the_room(client, room):
    join_as_other_user(client, room["id"])
    owner_token = ws_token(client)
    other_token = ws_token(client, OTHER_USER)

    with connect_socket(client, owner_token, room["id"]) as owner_socket:
        with connect_socket(client, other_token, room["id"]) as other_socket:
            owner_socket.send_json({"type": "typing", "is_typing": True})

            assert other_socket.receive_json() == {
                "type": "typing",
                "user_id": room["created_by"],
                "username": TEST_USER["username"],
                "is_typing": True,
            }

            owner_socket.send_json({"type": "typing", "is_typing": False})
            assert other_socket.receive_json()["is_typing"] is False

    assert room["id"] not in manager.connections


def test_message_longer_than_limit_is_rejected(client, db, room):
    token = ws_token(client)

    with connect_socket(client, token, room["id"]) as socket:
        socket.send_json({"type": "message.send", "content": "x" * 2001})

        error = socket.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "invalid_event"
        assert "2000" in error["detail"]

        socket.send_json({"type": "message.send", "content": "x" * 2000})
        assert socket.receive_json()["type"] == "message.new"

    assert db.query(models.Message).count() == 1
    assert room["id"] not in manager.connections


def test_invalid_events_return_errors(client, db, room):
    token = ws_token(client)

    with connect_socket(client, token, room["id"]) as socket:
        socket.send_text("definitely not json")
        assert socket.receive_json()["code"] == "invalid_json"

        socket.send_json({"type": "room.destroy"})
        assert socket.receive_json()["code"] == "invalid_event"

        socket.send_json({"type": "message.send"})
        assert socket.receive_json()["code"] == "invalid_event"

        socket.send_json(["not", "an", "object"])
        assert socket.receive_json()["code"] == "invalid_event"

    assert db.query(models.Message).count() == 0
    assert room["id"] not in manager.connections


def test_disconnect_removes_socket_from_manager(client, room):
    join_as_other_user(client, room["id"])
    token = ws_token(client)
    other_token = ws_token(client, OTHER_USER)

    with connect_socket(client, token, room["id"]) as socket:
        with connect_socket(client, other_token, room["id"]):
            assert len(manager.connections[room["id"]]) == 2

        # The second socket is gone, the first one is still connected.
        assert len(manager.connections[room["id"]]) == 1
        socket.send_json({"type": "message.send", "content": "still here"})
        assert socket.receive_json()["type"] == "message.new"

    assert manager.connections == {}