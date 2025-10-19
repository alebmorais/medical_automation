from medical_automation import config as cfg


def admin_headers():
    return {cfg.Config.SNIPPET_ADMIN_HEADER: cfg.Config.SNIPPET_ADMIN_TOKEN}


def test_get_all_and_one(app_client):
    r = app_client.get("/snippets/")
    assert r.status_code == 200
    all_snips = r.get_json()
    assert any(s["abbreviation"] == "addr" for s in all_snips)

    r = app_client.get("/snippets/addr")
    assert r.status_code == 200
    assert r.get_json()["full_text"].startswith("123 Main")


def test_add_update_delete_snippet(app_client):
    # Add
    r = app_client.post("/snippets/", json={"abbreviation": "sig", "full_text": "Signature"}, headers=admin_headers())
    assert r.status_code == 201

    # Update
    r = app_client.put("/snippets/1", json={"abbreviation": "addr", "full_text": "Updated Street"}, headers=admin_headers())
    # May be 200 or 404 depending on id, so ensure add/update path works by updating the newly added one:
    if r.status_code == 404:
        # Find the inserted snippet id by listing all
        li = app_client.get("/snippets/").get_json()
        new_id = next(s["id"] for s in li if s["abbreviation"] == "sig")
        r = app_client.put(f"/snippets/{new_id}", json={"abbreviation": "sig", "full_text": "Signature Updated"}, headers=admin_headers())
    assert r.status_code == 200

    # Delete
    li = app_client.get("/snippets/").get_json()
    to_delete = next(s["id"] for s in li if s["abbreviation"] in ("sig", "addr") and s["full_text"].startswith(("Signature", "Updated")))
    r = app_client.delete(f"/snippets/{to_delete}", headers=admin_headers())
    assert r.status_code == 200