def test_get_categories(app_client):
    resp = app_client.get("/medical/categories")
    assert resp.status_code == 200
    cats = resp.get_json()
    assert "Cardiology" in cats
    assert "Neurology" in cats


def test_get_phrases(app_client):
    resp = app_client.get("/medical/phrases/Cardiology")
    assert resp.status_code == 200
    phrases = resp.get_json()
    assert "Normal sinus rhythm" in phrases


def test_add_phrase_and_search_then_delete(app_client):
    # Add
    r = app_client.post("/medical/phrases", json={"categoria": "Cardiology", "frase": "No murmurs"})
    assert r.status_code == 201

    # Search
    r = app_client.get("/medical/search?q=murmurs")
    assert r.status_code == 200
    results = r.get_json()
    assert any("No murmurs" == x["frase"] for x in results)

    # Find id of the inserted phrase
    pid = next(x["id"] for x in results if x["frase"] == "No murmurs")

    # Delete
    r = app_client.delete(f"/medical/phrases/{pid}")
    assert r.status_code == 200