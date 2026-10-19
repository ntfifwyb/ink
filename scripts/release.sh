#!/usr/bin/env bash
# Publish the version in src/anki_dashboard/manifest.json as a GitHub Release.
# Run from an up-to-date main after the release PR merged: tags v<version>, builds
# dist/anki-dashboard.ankiaddon and uploads it, with the CHANGELOG section as notes.
set -euo pipefail
cd "$(dirname "$0")/.."

version=$(python3 -c 'import json; print(json.load(open("src/anki_dashboard/manifest.json"))["human_version"])')
tag="v$version"

[ "$(git branch --show-current)" = main ] || { echo "release: check out main first" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "release: working tree has changes" >&2; exit 1; }
git fetch -q origin
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "release: main is not origin/main; pull first" >&2; exit 1; }
if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
	echo "release: $tag already exists" >&2
	exit 1
fi

# The "## [x.y.z]" section of CHANGELOG.md, without its heading.
notes=$(awk -v v="$version" '
	$0 ~ "^## \\[" v "\\]" { on = 1; next }
	on && /^## \[/ { exit }
	on { print }
' CHANGELOG.md)
[ -n "$notes" ] || { echo "release: CHANGELOG.md has no section for $version" >&2; exit 1; }

python3 scripts/build.py
git tag -a "$tag" -m "$tag"
git push origin "$tag"
gh release create "$tag" dist/anki-dashboard.ankiaddon --title "$tag" --notes "$notes"
