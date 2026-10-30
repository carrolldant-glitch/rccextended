# RccExtended rescue — 2026-10-29

Local candidate: **1.0.6-2**. Upstream licensing is clarified and the notices are
backported. Rootless diagnostics and **three independent clean-chroot builds
(3/3)** are verified. Danny reviewed the recipe and earlier changelog; this
documentation update records the completed builds. Final human release review
and explicit publication approval remain. Nothing was installed on the host;
no package, source or patch was published.

## Baseline and intent

- Danny selected this repair after the Necromancer shortlist.
- AUR baseline `b2751c10b8e54c1289d42c5ae2cb95dde537918f`, version `1.0.5-1`;
  official AUR metadata reported it orphaned on October 29.
- Upstream `v1.0.6`: `0160038dd0b2d1e0b501dbeea46ec1dfcd09ae6e`.
  Source archive SHA-256:
  `0949d2b0a47e56624f5bc2c57e90ad8115298ce69012bb4235dfd8f7ab00b599`.
- The unpatched **1.0.6** source compiled with the installed toolchain. Its
  missing-input and invalid-input commands returned success, reproduced in
  isolation. The earlier audit reproduced its broken shell assignment. This
  work repairs functional/safety defects; it does not claim that the old AUR
  1.0.5 build was reproduced as a compiler failure.

## Source repair

`resource-safety.patch` changes the shared reverse-mode path, not one caller at
a time. The parser/extractor implementation and headers shrink from 679 to 387
lines (excluding the newly preserved three-line notices on four files) by
removing global resource registration, default-locale mutation,
recursive filename-collision machinery and hand-built XML.

- Parse one bounded byte snapshot. Validate section order/ranges, record sizes,
  child indexes, cycles/shared nodes, depth, names, flags, locales, payload
  ranges and duplicate aliases before using them. Reject unsupported input;
  never fall through to Qt's resource loader after validation fails.
- Decode data using the existing zlib/Zstandard libraries with fixed output
  capacities. Verify stream completion and size rather than trusting a declared
  decompressed length or letting decompression grow an unlimited buffer.
- Extract into a private temporary directory. Use exclusive file creation,
  checked writes/flushes and a final directory rename. Refuse an existing
  `qresource`, including dangling symlinks. A failed batch discards only its own
  staging directory and never replaces an earlier extraction.
- Use Qt's XML writer for aliases, language attributes and paths. Separate
  locale payload directories so a localized filename cannot collide with an
  ordinary resource path. Include hidden and empty resources.
- Generate a POSIX rebuild script with literal shell quoting, `set -eu`, and
  paths relative to the script location. Never execute it automatically. Its
  ShellCheck SC2016 annotation documents intentional literal dollar signs.
- Parse reverse-mode arguments through `QCommandLineParser`, supporting
  multiple inputs, wildcard paths, `--`, and options after filenames. Propagate
  failure to the process exit status; reject duplicate input basenames.
- Check compiler output writes/flushes and validate the format number before
  narrowing it to the library's byte-sized field. Fix the logger's failed-open
  allocation leak. Retain upstream copyright notices.

Limits and changed output layout are explicit in `README.arch`: 64 MiB input
and per-file output, 256 MiB total output, 10,000 nodes per batch, depth 64,
255-byte components and 4096-byte resource paths. These are deliberate ceilings,
not general archive support. This is a Linux-focused downstream repair; Windows
and arbitrary nonstandard RCC layouts are not validated. Do not treat this tool
as a sandbox or the tests as proof of safety against every malformed input.

## Packaging

- Update to 1.0.6 with SHA-256 pins, a collision-resistant source filename and
  a reviewed `prepare()` patch. Regenerate `.SRCINFO` from the final recipe.
- Declare direct runtime dependencies: glibc, libgcc, libstdc++, Qt 5 Base,
  zlib and Zstandard. Remove Qt Declarative; the packaged executable does not
  link it. Add Python/ShellCheck only for checks.
- Use an out-of-source qmake build and pass makepkg's hardening flags. Remove
  upstream's static-build switches. The final executable is PIE, has a
  non-executable stack, GNU RELRO and immediate symbol binding.
- Install only `/usr/bin/rccextended`, documentation and licensing material.
  Do not replace `/usr/bin/rcc`, add services or change system configuration.
- Credit Danny as Contributor while preserving the previous maintainer's
  attribution; no AUR ownership claim has been made.

## Licensing-only refresh — 1.0.6-2

- With Danny's approval, opened [upstream issue #6](https://github.com/zedxxx/rccextended/issues/6)
  without sharing code or security findings. The author replied and closed it,
  confirming `GPL-3.0-only WITH Qt-GPL-exception-1.0` for the combined work.
- Backport the exact license-only commit
  `eea2824a1a602a89d9270fc64020a735584958ce` onto the unchanged v1.0.6 source.
  Its patch SHA-256 is
  `c707fd23813599bad85444465c509796f0aa0f7bfcf70d36b163a4c00f59f2d6`.
  This adds GPL/exception texts, six SPDX notices and both README license
  sections without importing the intervening compilation-instructions change.
- Install upstream's separate `LICENSE` and `LICENSE.GPL3-EXCEPT`; stop fetching
  Qt's combined text as a substitute. Remove `LicenseRef-Upstream-Unspecified`,
  regenerate `.SRCINFO`, and document the same license for original downstream
  additions without taking ownership of upstream code or its commercial rights.
- Apply the license patch first. Rebase the repair's context to preserve the
  notices; both patches apply with `--fuzz=0`, without offsets. The built C++
  and qmake file bodies exactly match the previous candidate after removing
  only those six new three-line headers. `check.py` changes only its SPDX line.
- Keep runnable notice guards in `check()`: six SPDX headers and two license
  headings. An isolated probe accepts the valid tree and rejects all eight
  cases where a required notice is removed. The original 78 CLI cases remain.
- Bump `pkgrel` to 2 to distinguish the refreshed artifacts from 1.0.6-1.
  Create and inspect a complete local `makepkg --allsource` archive; it contains
  the recipe, upstream archive, both patches, checks and packaged documentation.
  These artifacts remain local, unsigned and ignored, pending release approval.

## Earlier rootless verification

The following pre-chroot checks ran as the ordinary user in Bubblewrap
namespaces: network and other namespaces isolated, capabilities dropped,
`/usr` read-only, no home or
credential directories mounted, and writable work confined to this project's
verification directory plus disposable sandbox `/tmp`.

1. Original source built; two false-success behaviors reproduced in the earlier
   baseline investigation. This was not rerun as a new baseline this time.
2. Standard-library `check.py`: **78 offline cases pass** in the final makepkg
   build and again against the extracted, stripped package executable.
3. Clang **AddressSanitizer + LeakSanitizer + UndefinedBehaviorSanitizer** build:
   all 78 cases pass, including with Qt logging forced to stderr. Sanitizers
   instrument our executable; system libraries were not rebuilt with sanitizers.
4. Tests cover formats 1/2/3, uncompressed/zlib/Zstandard payloads, default and
   localized aliases, Unicode/hidden/empty files, shell/XML-special names, moving
   and rebuilding output, multi-file CLI behavior, malformed/truncated data,
   depth/decompression limits, failed writes and existing-directory/symlink
   preservation. Inputs are synthetic; no third-party application was executed.
5. Final offline `makepkg` checks declared dependencies using a read-only host
   Pacman database. Source checksums, patch application, build, `check()`, main
   and debug archive creation pass. `.BUILDINFO` matches the final PKGBUILD.
   The patched source equals the source reconstructed by that recipe.
6. `bash -n` passes. Recipe ShellCheck passes with only its standard makepkg
   supplied-variable/metadata exclusions (`SC2034`, `SC2154`). Generated scripts
   are checked by ShellCheck in every format round-trip case.
7. Main archive namcap output is empty. Recipe namcap warns only about the
   intentionally absent Maintainer tag. Debug-only namcap reports an empty
   source-build directory and a link to the main executable, absent from that
   separate archive. Extracting both packages together resolves both build-ID
   links; executable/debug Build IDs match
   `415430049178ccf2852feea89c79722d6bac9009`.
   **Do not describe the isolated debug namcap report as error-free.**
8. Installed license files match upstream's pinned files byte-for-byte. The
   archive metadata has exactly one license expression and no unresolved
   placeholder. The source archive matches all frozen inputs; its `.SRCINFO`
   adds only makepkg's two generated comment lines. The eight negative notice
   probes pass. No host installation is needed for these checks.

Those diagnostics are **not** clean chroots: the sandbox uses installed host
tools/libraries and their package database. At that stage the count was **0/3**;
the subsequently completed builds are recorded below. No bit-for-bit
reproducibility claim. The first exploratory makepkg run skipped dependencies
and lacked Pacman's inventory for `.BUILDINFO`; it is superseded by the final
build above, not silently counted as equivalent verification.

Rootless-stage evidence is ignored under `verification/license-refresh.n2seHu/`:
`build.log`, `package-review.log`, `sanitizers-final.log`, `license-guards.log`,
`namcap-final-main.log`, `namcap-final-debug.log` and
`source-and-debug-review.log`. Frozen inputs and archives are in `package/`;
combined archive readback is in `readback/`. The refreshed ledger is
`verification/evidence.sha256`; the run adds about 18 MiB.

Retained diagnostic attempts are not passing evidence: `preflight.log` caught
the two full-file hunks needing new license context; `rebased.log` confirms the
correction. `sanitizers.log` used GCC's release/LTO settings with Clang and failed
at linking; the final run uses the earlier working sanitizer configuration with
LTO disabled. Initial `namcap-main.log` lacked the read-only loader cache;
the final run supplies it and reports no main-package findings. The package
build's GDB index-cache warning reflects the absent sandbox home/cache path,
not a failed build. GNU readelf also complains about an interpreter in the
debug-only file; direct build-ID section comparison and both link checks pass.

The previous candidate's inputs, review notes and ledger are retained in
`before/`; its build artifacts remain in `verification/final-reviewed/` and
its earlier logs remain at the verification root. The old ledger describes
those old inputs, not the updated working files. Earlier 72/77-case attempts
are historical only. No bit-identical rebuild claim is made.

Rootless main archive SHA-256:
`fbf5f00aa02f40e036e797eff4ccd4ea2ed3e39b1f10029be49eff3d902afba2`

Rootless debug archive SHA-256:
`f8bd2b2e99a359790ea17bf177f4ac31b416b5442ca9db90cc3b1c4d69095c47`

Complete source archive SHA-256:
`0b2cdfe61abb10764cd4f4d860a9d200b303e7804d12716f7b4c9816d2a99e61`

## Three clean-chroot builds — verified 2026-10-29

Danny separately approved each exact privileged job. All three used new base
and build roots under `verification/clean-chroots.Gu6HGN/pass-1/`, `pass-2/` and
`pass-3/`, with native Arch devtools and compilation as the non-root build user.
Pinned sources and the normal signed-package download cache were reused;
installed chroots were not. These environments still share the host kernel.

- Each build exited **0**, passed all **78 offline cases** and the six SPDX/
  two license-heading checks, and applied both patches without offsets/fuzz.
- Each installed executable passed all **78 cases again** in a rootless,
  network-isolated check using that chroot's own libraries, not host libraries.
- Main archive namcap reports are empty. Each debug package has only the empty
  build-directory warning, with no errors in the installed chroot context.
  The earlier isolated debug-archive link finding is retained above, not hidden.
  Recipe namcap still warns about the intentional Contributor-only attribution.
- `checkpkg` skipped comparison because `rccextended` is not in the official
  repositories. That comparison was **not** a passing test.
- `pacman -Qkk` against each chroot reports main: 13 files, zero altered;
  debug: 25 files, zero altered. Archives, installed/extracted binary identity,
  licensing texts, debug links/build IDs and ELF hardening checks pass.
- All three main executables are byte-identical, SHA-256
  `5144c8b16b1e7aa267c1914c7d3cd381126c8ce2336da602f77989acb142e3b3`.
  Complete package archives differ in build metadata/timestamps; this is not
  a claim of bit-identical archive reproducibility or universal input safety.
- Host package inventories are unchanged. No host installation, configuration,
  VM/kernel modification, signing or package publication occurred. About
  **27.31 GiB** remained free after the final review; no further cleanup ran.

The tested PKGBUILD remains
`f2d2304a0d1aeb7825db86bbe3d0752a85f9476a08d0539954aeffa89272e668`.
Recipe, `.SRCINFO`, patches, checks and packaged documentation did not change.
Only verification reporting changed afterward. The earlier reviewed changelog
is preserved in every pass's frozen `recipe/changes.md`; the rootless ledger
now references that preserved copy. Its original ledger is retained as
`verification/clean-chroots.Gu6HGN/rootless-ledger-before-final-docs.sha256`.

Each pass retains `RESULTS.txt`, input/evidence checksums, build and installed-
command logs, main/debug archives and archive readback. The combined summary
and current documentation ledger are `verification/clean-chroots.Gu6HGN/RESULTS.txt`
and `verification/clean-chroots.Gu6HGN/evidence.sha256`. Evidence stays local and
ignored; no logs or artifacts were uploaded.

Final (pass 3) main archive SHA-256:
`22bddd8556f90556082959a5d3fc9f4cd83085f3c6fc85df9b14405bc2357806`

Final (pass 3) debug archive SHA-256:
`755cb1609790f5c289c672170ffc3cfd445770434894177a6c1da7c7f7538ac8`

## Release hold and next decision

The upstream licensing question now has an author response and source notices;
both are incorporated in this candidate. Details and primary-source links are
in `LICENSE-STATUS.txt`. This does not replace license/source obligations when
distributing binaries, verify arbitrary extracted resources' rights, or grant
release approval.

Danny's recipe review stands; the recipe is unchanged. Review these new
verification notes and complete any remaining review of the patch/checks before
the release decision. Three clean-chroot passes are complete; their approvals
do not authorize retries, cleanup or publication. Host installation, further
upstream messages, a fork/PR and any GitHub/AUR package publication remain
unauthorized. Only the non-sensitive ELIAS continuity note may sync under the
existing standing exception.
