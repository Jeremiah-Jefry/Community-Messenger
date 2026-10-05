from conftest import (
    OTHER_USER,
    auth_header,
    create_room,
    join_room,
    register_user,
    seed_messages,
)

import models


def test_create_room_adds_creator_as_owner(client, db):
    user = register_user(client)
    headers = auth_header(client)

    response = client.post("/rooms", json={"name": "  General  "}, headers=headers)

    assert response.status_code == 201
    room = response.json()
    assert room["name"] == "General"
    assert room["created_by"] == user["id"]

    membership = db.query(models.RoomMember).filter_by(room_id=room["id"]).one()
    assert membership.user_id == user["id"]
    assert membership.role == "owner"


def test_list_rooms_returns_only_my_rooms(client):
    register_user(client)
    mine = create_room(client, auth_header(client), name="Mine")

    register_user(client, OTHER_USER)
    other_headers = auth_header(client, OTHER_USER)
    theirs = create_room(client, other_headers, name="Theirs")

    response = client.get("/rooms", headers=other_headers)

    assert response.status_code == 200
    body = response.json()
    assert [room["id"] for room in body] == [theirs["id"]]

    owner_response = client.get("/rooms", headers=auth_header(client))
    assert [room["id"] for room in owner_response.json()] == [mine["id"]]


def test_join_room_adds_member(client, db):
    register_user(client)
    room = create_room(client, auth_header(client))
    register_user(client, OTHER_USER)
    joiner_headers = auth_header(client, OTHER_USER)
    joiner = client.get("/me", headers=joiner_headers).json()

    joined = join_room(client, room["id"], joiner_headers)

    assert joined.status_code == 200
    assert joined.json()["role"] == "member"
    assert joined.json()["user_id"] == joiner["id"]

    repeated = join_room(client, room["id"], joiner_headers)
    assert repeated.status_code == 200
    assert (
        db.query(models.RoomMember)
        .filter_by(room_id=room["id"], user_id=joiner["id"])
        .count()
        == 1
    )
    assert client.get("/rooms", headers=joiner_headers).json()[0]["id"] == room["id"]


def test_join_unknown_room_returns_404(client):
    register_user(client)

    response = join_room(client, 999, auth_header(client))

    assert response.status_code == 404
    assert response.json()["detail"] == "Room not found"


def test_messages_forbidden_for_non_member(client, db):
    owner = register_user(client)
    room = create_room(client, auth_header(client))
    seed_messages(db, room["id"], owner["id"], 1)

    register_user(client, OTHER_USER)
    non_member = client.get(
        f"/rooms/{room['id']}/messages", headers=auth_header(client, OTHER_USER)
    )
    anonymous = client.get(f"/rooms/{room['id']}/messages")

    assert non_member.status_code == 403
    assert non_member.json()["detail"] == "You are not a member of this room"
    assert anonymous.status_code == 401


def test_messages_newest_first_with_cursor_pagination(client, db):
    owner = register_user(client)
    headers = auth_header(client)
    room = create_room(client, headers)
    messages = seed_messages(db, room["id"], owner["id"], 120)
    all_ids = [message.id for message in messages]

    first_page = client.get(f"/rooms/{room['id']}/messages?limit=50", headers=headers)
    second_page = client.get(
        f"/rooms/{room['id']}/messages?before={all_ids[70]}&limit=50", headers=headers
    )
    third_page = client.get(
        f"/rooms/{room['id']}/messages?before={all_ids[20]}&limit=50", headers=headers
    )

    assert first_page.status_code == 200
    assert [message["id"] for message in first_page.json()] == all_ids[70:][::-1]
    assert [message["content"] for message in first_page.json()][:2] == [
        "message 119",
        "message 118",
    ]

    # The cursor is exclusive: every page returns messages older than it.
    assert [message["id"] for message in second_page.json()] == all_ids[20:70][::-1]
    assert [message["id"] for message in third_page.json()] == all_ids[:20][::-1]

    pages = [
        [message["id"] for message in page.json()]
        for page in (first_page, second_page, third_page)
    ]
    assert not set(pages[0]) & set(pages[1])
    assert not set(pages[1]) & set(pages[2])
    assert sorted(pages[0] + pages[1] + pages[2]) == all_ids


def test_messages_default_limit_and_validation(client, db):
    owner = register_user(client)
    headers = auth_header(client)
    room = create_room(client, headers)
    seed_messages(db, room["id"], owner["id"], 60)

    default_page = client.get(f"/rooms/{room['id']}/messages", headers=headers)
    too_small = client.get(f"/rooms/{room['id']}/messages?limit=0", headers=headers)
    too_large = client.get(f"/rooms/{room['id']}/messages?limit=101", headers=headers)
    bad_cursor = client.get(
        f"/rooms/{room['id']}/messages?before=99999", headers=headers
    )

    assert len(default_page.json()) == 50
    assert too_small.status_code == 422
    assert too_large.status_code == 422
    assert bad_cursor.status_code == 400