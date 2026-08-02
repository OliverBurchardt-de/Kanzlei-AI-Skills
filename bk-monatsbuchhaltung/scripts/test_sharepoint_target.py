from sharepoint_target import build_targets


def main() -> None:
    targets = build_targets("12371")
    assert targets["hostname"] == "burchardtkollegen.sharepoint.com"
    assert targets["site_path"] == "/sites/Wissen"
    assert targets["library"] == "Mandantenbesonderheiten"
    assert targets["profile_url"] == (
        "https://burchardtkollegen.sharepoint.com/sites/Wissen/"
        "Mandantenbesonderheiten/Mandantenprofile/12371.md"
    )
    assert targets["accrual_url"] == (
        "https://burchardtkollegen.sharepoint.com/sites/Wissen/"
        "Mandantenbesonderheiten/Abgrenzungsregister/12371.md"
    )
    assert targets["fetch_raw_file"] is True
    assert "Kanzlei/Mandanten" in targets["forbidden_path_fragments"]
    print("SharePoint target contract: OK")


if __name__ == "__main__":
    main()
