#!/bin/sh
# Build every theme from the upstream tinted-theming schemes plus the
# [[schemes.extras]] in tinty.toml (e.g. tinted-colortemplate's solarized8).
#
# The update workflow runs this same script with the same tinty version, so
# local and CI builds produce the same files. It uses its own tinty config and
# data dir (.cache/tinty), never the user's.
set -eu
cd "$(dirname "$0")"

# --- repo-specific ---------------------------------------------------------
OUT="delta"
EXT="gitconfig"
pre_build() { :; }
post_build() { :; }
# ---------------------------------------------------------------------------

data=.cache/tinty
schemes="$data/scheme-repos/schemes"

# Fetch or update the scheme repos; fall back to the cache when offline.
if ! tinty sync --quiet -c tinty.toml -d "$data"; then
  [ -d "$schemes" ] || exit 1
  echo "build.sh: tinty sync failed; building from cached schemes" >&2
fi

# tinty build reads only scheme-repos/schemes, so merge the extras into a
# second data dir. Upstream first, so an extra with the same name wins.
link_schemes() {
  for f in "$1"/*.yaml "$1"/*.yml; do
    if [ -e "$f" ]; then ln -sf "$PWD/$f" "$2/"; fi
  done
}
merged="$data/merged"
rm -rf "$merged"
for system in base16 base24 tinted8; do
  dest="$merged/scheme-repos/schemes/$system"
  mkdir -p "$dest"
  link_schemes "$schemes/$system" "$dest"
  for repo in "$data"/scheme-repos/*; do
    if [ "$repo" != "$schemes" ] && [ -d "$repo/$system" ]; then
      link_schemes "$repo/$system" "$dest"
    fi
  done
done

pre_build
# Rebuild from scratch so removed or renamed schemes don't linger.
rm -f "$OUT"/*."$EXT"
tinty build --quiet -c tinty.toml -d "$merged" .
post_build
echo "build.sh: $(find "$OUT" -name "*.$EXT" | wc -l) $OUT/*.$EXT"
