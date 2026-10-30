<!-- SPDX-License-Identifier: GPL-3.0-only WITH Qt-GPL-exception-1.0 -->
# RccExtended — Arch packaging and downstream repair

Source-only Arch Linux packaging for **RccExtended 1.0.6-2**, contributed by
[Danny](https://github.com/carrolldant-glitch), with implementation assistance
from Elias (Codex). The original AUR history and upstream attribution are
preserved. This is a downstream packaging repository, not the upstream project
and not an AUR adoption or submission.

RccExtended inspects and extracts binary Qt resource bundles without launching
their application. This repair adds bounded parsing/decompression, safer output
handling, accurate failures, and portable, quoted rebuild scripts. It installs
as `rccextended`, leaving Qt's `rcc` untouched. It is not a general executable
decompiler or a security sandbox.

## Verification

Verified locally on Arch x86_64 on 2026-10-29:

- **Three independent clean-chroot builds passed.** Each passed the same
  **78 offline cases** plus license-notice checks.
- Each installed executable passed those 78 cases again in a rootless,
  network-isolated check using its own chroot's libraries.
- Main-package namcap reports were empty. Debug packages had one empty-directory
  warning; the recipe's missing Maintainer warning is intentional Contributor
  attribution. `checkpkg` skipped its unavailable official-repository comparison.
- All three main executables were byte-identical. Complete package archives
  differ in build metadata/timestamps; no bit-identical archive or universal
  safety guarantee is claimed. Clean chroots share the host kernel.

See [changes.md](changes.md) for the detailed repair and verification record,
[check.py](check.py) for the runnable tests, and [README.arch](README.arch) for
usage, supported formats, resource limits and changed output layout.

## Build from reviewed source

On Arch Linux with Git and Arch devtools already available, inspect `PKGBUILD`,
the patch and checker before building. Run as an ordinary user, never root:

```bash
git clone https://github.com/carrolldant-glitch/rccextended.git
cd rccextended
# Review PKGBUILD, resource-safety.patch and check.py before continuing.
mkdir -p verification
rcc_chroot=$(mktemp -d "$PWD/verification/chroot.XXXXXX")
extra-x86_64-build -r "$rcc_chroot" -- -U "$(id -un)"
```

Devtools requests sudo for chroot setup and installs packages inside that
chroot; compilation runs as its unprivileged build user. It uses the normal
package download cache and requires several GiB of disk space. Repeat with a
new `mktemp` directory for each independent pass. No host installation command
or automatic cleanup is provided here. The recipe downloads pinned upstream
source and the licensing patch, then verifies their SHA-256 values.

## Publication scope

Danny approved this GitHub **source-only** publication after reviewing the
completed results. No binary release, AUR action, host installation or upstream
submission is included. Build directories, downloaded source archives, package
binaries, raw logs, private inventories and credentials are not in this repo.
The local evidence paths mentioned in `changes.md` are not included in a clone;
the test code and verification summary are included so others can repeat it.

To preserve the exact tested inputs, the recipe and packaged documentation keep
their earlier local-review notices. Publication-pending statements in the
reviewed changelog record the stage before this GitHub approval; this README
states the current source-publication scope. These notices do not imply AUR
ownership or authorization for future releases.

## Upstream, credit and license

- Upstream: [zedxxx/rccextended](https://github.com/zedxxx/rccextended).
- Original AUR packaging: Mariusz Libera; attribution remains in `PKGBUILD`.
- Downstream packaging/review: Danny, `carrolldant@gmail.com`.
- License: **GPL-3.0-only WITH Qt-GPL-exception-1.0**. See [LICENSE](LICENSE),
  [LICENSE.GPL3-EXCEPT](LICENSE.GPL3-EXCEPT) and
  [LICENSE-STATUS.txt](LICENSE-STATUS.txt) for the pinned upstream clarification.

The two license texts are unchanged copies of the reviewed upstream texts.
Original upstream notices remain in force; this repository does not claim
ownership of upstream work or rights to third-party resources you may extract.
