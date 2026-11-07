# tinted-delta

Remote tinty template that themes [delta](https://github.com/dandavison/delta)
(the git pager) from the current tinty scheme (base16, base24, tinted8). It
works with delta on Linux, WSL, and Windows.

Each built file sets:

- `dark`/`light` from the scheme variant, so delta does not have to guess the
  terminal background.
- `syntax-theme = ansi`: syntax colors come from the terminal's ANSI palette,
  which tinted-shell / tinted-windows-terminal set from the same scheme, and
  plain text uses the terminal's default foreground. (The `base16` theme draws
  plain text in ANSI 7, which is unreadable on light schemes whose ANSI 7 is a
  true white, e.g. tinted8.)
- `true-color = always`, so the hex colors are not rounded to the
  xterm-256 palette. (`COLORTERM` is often unset in WSL.)
- Added and removed lines get backgrounds blended from the scheme background and
  red/green. Line numbers, file headers, and hunk headers use scheme colors.

## Layout

- `templates/`: one gitconfig fragment per system.
- `delta/`: built output, one file per scheme (committed; tinty reads it
  directly). Each file works by itself with simple red/green styles.
- `apply-delta.py`: the tinty hook. It reads the `tinted-delta-vars` comment in
  the built file and rewrites the plus/minus styles to `syntax` on a background
  20% (line) / 40% (changed words) of the way from the scheme background to
  red/green. The blend is reduced when needed to keep the scheme foreground
  readable. Then it writes the result to each destination.
  Standard library only.

## Tinted Configuration

Append to `~/.config/tinted-theming/tinty/config.toml`:

```toml
[[items]]
name = "tinted-delta"
path = "https://github.com/jfishe/tinted-delta"
themes-dir = "delta"
hook = "python3 -I ~/.local/share/tinted-theming/tinty/repos/tinted-delta/apply-delta.py %f ~/.config/delta/tinty.gitconfig ${USERPROFILE:+\"$USERPROFILE/.config/delta/tinty.gitconfig\"}"
supported-systems = ["base16", "base24", "tinted8"]
```

Then include the result from your git config (one time):

```ini
[include]
	path = ~/.config/delta/tinty.gitconfig
```

Put the include **before** any `[delta]` settings of your own, so your own
settings take precedence.

### WSL + Windows

When `$USERPROFILE` is set, the hook also writes
`$USERPROFILE/.config/delta/tinty.gitconfig` for Git for Windows and Windows
delta. Elsewhere it writes only `~/.config/delta/tinty.gitconfig`.
On WSL, the hook reads `$USERPROFILE` from the shell that runs `tinty`; see
[tinted-dircolors](https://github.com/jfishe/tinted-dircolors#tinted-configuration)
for passing it through `WSLENV`.

Both gits expand `~` to their own home, so a single
`path = ~/.config/delta/tinty.gitconfig` include works in a `.gitconfig` that
both of them read.

## Development

Edit `templates/` or `apply-delta.py`, then preview locally:

```bash
tinty build .
python3 -I apply-delta.py delta/base16-solarized-dark.gitconfig /tmp/t.gitconfig
```

Commit and push `templates/` and `delta/`. The
[update workflow](.github/workflows/update.yml) also rebuilds `delta/` on every
push touching `templates/` and weekly against the latest upstream schemes.
Users pick up changes with `tinty update`.

## Credits

- [Tinted Theming schemes](https://github.com/tinted-theming/schemes): the
  base16, base24, and tinted8 color schemes.
- [tinted-builder-rust](https://github.com/tinted-theming/tinted-builder-rust)
  builds `delta/`; [tinty](https://github.com/tinted-theming/tinty) applies it.
- [delta](https://github.com/dandavison/delta).

## License

[MIT](LICENSE.txt). Files in `delta/` contain color values from the
Tinted Theming schemes, © 2022 Tinted Theming, used under the MIT License;
see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
