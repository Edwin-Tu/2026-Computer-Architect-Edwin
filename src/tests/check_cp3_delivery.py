"""Check CP3 layout, local links and preserved-evidence integrity (v1.1).

This checks files, not personal understanding, GitHub ownership or submission.
"""

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def anchors(text):
    seen = {}
    result = set()
    for line in text.splitlines():
        if not re.match(r"^#{1,6} ", line):
            continue
        title = line.lstrip("#").strip().replace("`", "").lower()
        slug = "".join(c for c in title if c.isalnum() or c in "_- ").replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def main():
    instructions = ROOT / "instructions"
    check((instructions / "README.md").is_file(), "Missing instruction index")
    check([p.name for p in (instructions / "MIN").iterdir()] == ["README.md"],
          "Instruction directory must contain only README.md")
    check([p.relative_to(ROOT).as_posix() for p in ROOT.rglob("CP3.md")] == ["report/CP3.md"],
          "Expected one canonical CP3 report")
    required = ["README.md", "CONTRIBUTIONS.md", "report/README.md", "report/CP1.md",
                "report/CP2.md", "report/CP3.md", "report/figures/README.md"]
    for relative in required:
        check((ROOT / relative).is_file(), f"Missing required file: {relative}")
    min_roots = [instructions / "MIN", ROOT / "src", ROOT / "report"]
    min_folders = [folder for scope in min_roots for folder in [scope, *scope.rglob("*")]]
    for folder in min_folders:
        if folder.is_dir() and ".git" not in folder.parts and "__pycache__" not in folder.parts:
            check((folder / "README.md").is_file(), f"Missing directory README: {folder}")
    print("Flat MIN directory, report placement and directory READMEs: PASS")

    links = 0
    documents = [ROOT / "README.md", ROOT / "CONTRIBUTIONS.md", instructions / "README.md"]
    documents += [path for scope in min_roots for path in scope.rglob("*.md")]
    for path in documents:
        if ".git" in path.parts:
            continue
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8-sig")):
            if link.startswith(("https:", "http:", "mailto:")):
                continue
            filename, _, fragment = link.partition("#")
            target = path.parent / filename if filename else path
            check(target.is_file(), f"Missing link target: {path}: {link}")
            if fragment:
                check(fragment in anchors(target.read_text(encoding="utf-8-sig")),
                      f"Missing section: {path}: {link}")
            links += 1
    print(f"MIN delivery Markdown file/section links: {links} PASS")

    evidence = ROOT / "src/references/validation/2026-10-23-gcc15"
    manifest = json.loads((evidence / "package_sha256.json").read_text(encoding="utf-8-sig"))
    actual_files = {p.relative_to(evidence).as_posix() for p in evidence.rglob("*")
                    if p.is_file() and p.name != "package_sha256.json"}
    check(actual_files == set(manifest["files"]), "Evidence file list is incomplete")
    for relative, metadata in manifest["files"].items():
        data = (evidence / relative).read_bytes()
        check(len(data) == metadata["bytes"] and hashlib.sha256(data).hexdigest() == metadata["sha256"],
              f"Evidence hash mismatch: {relative}")
    provenance = json.loads((evidence / "provenance_manifest.json").read_text(encoding="utf-8-sig"))
    for entry in provenance["entries"]:
        check(hashlib.sha256((evidence / entry["path"]).read_bytes()).hexdigest() == entry["sha256"],
              f"Preserved provenance mismatch: {entry['path']}")
    repair = json.loads((evidence / "integrity_update.json").read_text(encoding="utf-8-sig"))
    check(repair["original_manifest_readme"]["sha256"] != repair["actual_input_zip_readme"]["sha256"],
          "Expected disclosed original README mismatch")
    print(f"Current evidence hashes: {len(manifest['files'])}/{len(manifest['files'])} PASS")
    print(f"Preserved provenance entries: {len(provenance['entries'])} PASS; original mismatch disclosed")

    report = (ROOT / "report/CP3.md").read_text(encoding="utf-8")
    for number in range(1, 7):
        check(re.search(r"^## " + str(number) + r"\.", report, re.M), "Missing report section")
    plain = re.search(r"^## 5\.[^\n]*\n(.*?)^## 6\.", report, re.M | re.S).group(1).strip()
    check(len(plain) <= 200, "Plain-language section exceeds 200 characters")
    print(f"Report section structure and plain-language length ({len(plain)}): PASS")

    print("Git branch name: not constrained by MIN delivery validation")
    print("Scope: work 2 files only; group-wide content, personal understanding and GitHub identity are not certified.")


if __name__ == "__main__":
    main()
