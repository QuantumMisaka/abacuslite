"""Resolve one engine/harness tuple per workflow and verify curated assets."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request


SHA = re.compile(r"[0-9a-f]{40}\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def resolve_ref(repository: str, ref: str) -> str:
    if not REPOSITORY.fullmatch(repository) or not ref or "\n" in ref:
        raise ValueError("Invalid GitHub repository or ref")
    if SHA.fullmatch(ref):
        return ref
    url = f"https://api.github.com/repos/{repository}/commits/{urllib.parse.quote(ref, safe='')}"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        sha = json.load(response)["sha"]
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError(f"GitHub returned an invalid commit for {repository}:{ref}")
    return sha


def resolve_matrix(manifest, event, overrides, resolver=resolve_ref):
    if manifest.get("schema") != "abacus-engine-compatibility-refs-v1":
        raise ValueError("Unsupported engine reference schema")
    repository = manifest["engine_repository"]
    lanes = []
    for variant, branch in (("develop", "develop"), ("lts", "LTS")):
        selected = manifest["engines"][variant]
        requested = overrides.get(variant) or (
            branch if event == "schedule" else selected["ref"]
        )
        lanes.append({"variant": variant, "ref": resolver(repository, requested),
                      "format": selected["expected_format"]})
    harness = manifest["harness"]
    assets = manifest["assets"]
    return {
        "matrix": {"include": lanes},
        "engine_repository": repository,
        "harness_repository": harness["repository"],
        "harness_ref": resolver(harness["repository"], overrides.get("harness") or harness["ref"]),
        "assets_repository": assets["repository"],
        "assets_ref": resolver(assets["repository"], assets["ref"]),
        "assets_directory": assets["directory"],
    }


def verify_assets(manifest, directory):
    required = manifest["assets"]["required_sha256"]
    if not required:
        raise ValueError("Curated asset manifest must not be empty")
    for name, expected in required.items():
        path = directory / name
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f"Asset escapes its directory: {name}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Asset SHA256 mismatch: {name}")
    return required


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--event", default="push")
    parser.add_argument("--develop-ref", default="")
    parser.add_argument("--lts-ref", default="")
    parser.add_argument("--harness-ref", default="")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--assets-dir", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if args.assets_dir is not None:
        print(json.dumps(verify_assets(manifest, args.assets_dir), indent=2))
        return
    result = resolve_matrix(manifest, args.event, {
        "develop": args.develop_ref, "lts": args.lts_ref, "harness": args.harness_ref,
    })
    print(json.dumps(result, indent=2))
    if args.github_output:
        with args.github_output.open("a") as stream:
            for key, value in result.items():
                rendered = json.dumps(value, separators=(",", ":")) if isinstance(value, dict) else value
                if "\n" in rendered or "\r" in rendered:
                    raise ValueError("Workflow output contains a newline")
                stream.write(f"{key}={rendered}\n")


if __name__ == "__main__":
    main()
