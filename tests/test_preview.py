from mlb_digest.preview import load_sample_digest


def test_load_sample_digest_contains_all_template_elements():
    sample = load_sample_digest()

    assert "\n## " in sample
    assert "\n### " in sample
    assert "**" in sample
    assert "](http" in sample
    assert "| Team |" in sample
    assert "\n- " in sample
    assert "\n---\n" in sample
