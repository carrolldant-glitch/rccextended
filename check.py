#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only WITH Qt-GPL-exception-1.0
"""Offline CLI regressions; all inputs/outputs live in our temporary directory."""

import argparse
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zlib


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    checks = 0
    with tempfile.TemporaryDirectory(prefix="rccextended-check-", dir=".") as temporary:
        root = Path(temporary).resolve()
        (root / "bin").mkdir()
        (root / "bin/rccextended").symlink_to(binary)
        env = dict(os.environ, PATH=f"{root}/bin:/usr/bin")

        def run(command, cwd, success=True):
            result = subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=30)
            assert result.returncode == 0 if success else result.returncode > 0, (
                command, result.returncode, result.stdout, result.stderr)
            assert "AddressSanitizer" not in result.stderr, result.stderr
            assert "runtime error:" not in result.stderr, result.stderr
            return result

        def case(name):
            nonlocal checks
            checks += 1
            path = root / f"{checks:03d}-{name}"
            path.mkdir()
            return path

        if args.baseline:
            for name, content in (("missing", None), ("invalid", b"not a resource")):
                work = case(name)
                if content is not None:
                    (work / "input.rcc").write_bytes(content)
                run([binary, "--reverse", "input.rcc"], work)
                print(f"CONFIRMED upstream defect: {name} input reports success (0)")
            return

        run([binary, "--version"], root)
        run([binary, "--reverse", "missing.rcc"], case("missing"), False)
        run([binary, "--reverse"], case("empty-glob"), False)

        rows = [("nested/a & <b> 'quote' \"name\".txt", "", b"plain\0bytes"),
                (".hidden", "", b"hidden"), ("empty", "", b""),
                ("unicode/日本語-😀.txt", "", b"unicode"),
                ("message.txt", "", b"default"),
                ("message.txt", "en", b"English" * 1000),
                ("message.txt", "en_GB", b"British" * 1000),
                ("message.txt", "de_DE", b"Deutsch" * 1000)]

        def compile_bundle(work, filename, version=3, compression="none", entries=None):
            entries = rows if entries is None else entries
            document = ET.Element("RCC")
            for index, (alias, language, content) in enumerate(entries):
                source = f"source-{index}.dat"
                (work / source).write_bytes(content)
                resource = ET.SubElement(document, "qresource",
                                         {"lang": language} if language else {})
                ET.SubElement(resource, "file", {"alias": alias}).text = source
            qrc = work / "source.qrc"
            ET.ElementTree(document).write(qrc, encoding="utf-8", xml_declaration=True)
            run(["/usr/bin/rcc", "--binary", "--format-version", version,
                 "--compress-algo", compression, qrc, "-o", work / filename], work)
            return work / filename

        def contents(qrc):
            found = {}
            for resource in ET.parse(qrc).getroot():
                for item in resource:
                    path = (qrc.parent / item.text).resolve()
                    assert path.is_relative_to(qrc.parent.parent / "res"), path
                    key = (item.attrib["alias"], resource.attrib.get("lang", ""))
                    assert key not in found, key
                    found[key] = path.read_bytes()
            return found

        expected = {(alias, language): data for alias, language, data in rows}
        for version in (1, 2, 3):
            for compression in ("none", "zlib", "zstd"):
                if compression == "zstd" and version != 3:
                    continue
                work = case(f"roundtrip-{version}-{compression}")
                filename = "bundle 'quote' $literal; [1].rcc"
                compile_bundle(work, filename, version, compression)
                run([binary, "--reverse", "--", filename], work)
                output = work / "qresource"
                assert contents(output / "qrc" / f"{filename}.qrc") == expected
                assert output.stat().st_mode & 0o077 == 0
                # Rebuild after moving the result, from an unrelated directory.
                moved = work / "moved result"
                output.rename(moved)
                script = moved / "rcc/rcc-make.sh"
                run(["/bin/sh", "-n", script], root)
                run(["shellcheck", "--shell=sh", script], root)
                run(["/bin/sh", script], root)
                second = work / "second"
                second.mkdir()
                run([binary, "--reverse", moved / "rcc" / filename], second)
                assert contents(second / "qresource/qrc" / f"{filename}.qrc") == expected

        for mode in ("explicit", "glob", "default", "options-after-file"):
            work = case(f"inputs-{mode}")
            compile_bundle(work, "first.rcc", entries=[("one", "", b"1")])
            compile_bundle(work, "second.rcc", entries=[("two", "", b"2")])
            options = {"explicit": ["-r", "first.rcc", "second.rcc"],
                       "glob": ["-r", "*.rcc"], "default": ["-r"],
                       "options-after-file": ["first.rcc", "second.rcc", "-r"]}[mode]
            run([binary, *options], work)
            assert len(list((work / "qresource/qrc").glob("*.qrc"))) == 2

        work = case("seed")
        seed = compile_bundle(work, "seed.rcc", entries=[("ok.txt", "", b"hello")]).read_bytes()
        tree, payload, names = struct.unpack_from(">III", seed, 8)
        file_node = tree + 22
        name_record = names + struct.unpack_from(">I", seed, file_node)[0]

        def rejects(name, data):
            work = case(name)
            (work / "bad.rcc").write_bytes(data)
            run([binary, "--reverse", "bad.rcc"], work, False)
            assert not (work / "qresource").exists()
            assert not list(work.glob(".rccextended-*"))

        for size in range(24):
            rejects(f"header-truncated-{size}", seed[:size])
        for name, offset, fmt, value in (
            ("version", 4, ">I", 99), ("tree-offset", 8, ">I", 0xffffffff),
            ("payload-offset", 12, ">I", 0), ("names-offset", 16, ">I", len(seed)),
            ("header-flags", 20, ">I", 8), ("root-is-file", tree + 4, ">H", 0),
            ("child-count", tree + 6, ">I", 0x7fffffff),
            ("cycle", tree + 10, ">I", 0),
            ("name-offset", file_node, ">I", 0x7fffffff),
            ("node-flags", file_node + 4, ">H", 5),
            ("locale", file_node + 8, ">H", 65535),
            ("file-data-offset", file_node + 10, ">I", 0xffffffff),
            ("payload-size", payload, ">I", 0xffffffff),
            ("name-length", name_record, ">H", 65535),
            ("path-separator", name_record + 6, ">H", ord('/')),
            ("path-backslash", name_record + 6, ">H", ord('\\')),
            ("xml-control", name_record + 6, ">H", 0),
            ("invalid-surrogate", name_record + 6, ">H", 0xd800),
        ):
            data = bytearray(seed)
            struct.pack_into(fmt, data, offset, value)
            rejects(name, data)
        rejects("truncated-tree", seed[:-1])
        rejects("unreachable-node", seed + bytes(22))
        data = bytearray(seed)
        struct.pack_into(">H", data, name_record, 2)
        data[name_record + 6:name_record + 10] = "..".encode("utf-16-be")
        rejects("parent-traversal", data)

        work = case("invalid-format-number")
        compile_bundle(work, "valid.rcc", entries=[("f", "", b"x")])
        run([binary, "--binary", "--format-version", "257", "source.qrc",
             "-o", "should-not-exist.rcc"], work, False)
        assert not (work / "should-not-exist.rcc").exists()
        work = case("duplicate-alias")
        duplicate = compile_bundle(work, "duplicate.rcc",
                                   entries=[("same", "", b"one"), ("same", "", b"two")])
        rejects("duplicate-alias-reject", duplicate.read_bytes())
        work = case("empty-resource")
        compile_bundle(work, "empty.rcc", entries=[])
        run([binary, "-r", "empty.rcc"], work)
        assert contents(work / "qresource/qrc/empty.rcc.qrc") == {}
        work = case("second-input-invalid")
        (work / "valid.rcc").write_bytes(seed)
        (work / "bad.rcc").write_bytes(b"broken")
        run([binary, "-r", "valid.rcc", "bad.rcc"], work, False)
        assert not (work / "qresource").exists()
        assert not list(work.glob(".rccextended-*"))

        for kind in ("directory", "file", "symlink", "dangling-symlink"):
            work = case(f"existing-{kind}")
            (work / "input.rcc").write_bytes(seed)
            target = work / "qresource"
            if kind == "directory":
                target.mkdir()
                (target / "sentinel").write_text("keep")
            elif kind == "file":
                target.write_text("keep")
            else:
                (work / "outside").mkdir()
                (work / "outside/sentinel").write_text("keep")
                target.symlink_to("outside" if kind == "symlink" else "absent")
            run([binary, "--reverse", "input.rcc"], work, False)
            if kind == "directory":
                assert (target / "sentinel").read_text() == "keep"
            elif kind == "file":
                assert target.read_text() == "keep"
            else:
                assert target.is_symlink() and (work / "outside/sentinel").read_text() == "keep"

        work = case("duplicate-basename")
        (work / "a").mkdir()
        (work / "b").mkdir()
        for folder in ("a", "b"):
            (work / folder / "same.rcc").write_bytes(seed)
        run([binary, "-r", "a/same.rcc", "b/same.rcc"], work, False)
        assert not (work / "qresource").exists()
        work = case("read-only-output")
        (work / "input.rcc").write_bytes(seed)
        work.chmod(0o500)
        try:
            run([binary, "-r", "input.rcc"], work, False)
        finally:
            work.chmod(0o700)

        work = case("depth-limit")
        deep = compile_bundle(work, "deep.rcc", entries=[("d/" * 65 + "f", "", b"x")])
        rejects("excess-depth", deep.read_bytes())

        # Small synthetic compressed archives exercise expansion bounds without
        # storing enormous source fixtures in Git. Failed output is discarded.
        def compressed_archive(claimed, compressed, count=1):
            block = struct.pack(">I", claimed) + compressed
            data = struct.pack(">I", len(block)) + block
            name_data = b""
            nodes = struct.pack(">IHIIQ", 0, 2, count, 1, 0)
            for index in range(count):
                name = f"file{index}".encode("utf-16-be")
                nodes += struct.pack(">IHHHIQ", len(name_data), 1, 0, 1, 0, 0)
                name_data += struct.pack(">HI", len(name) // 2, 0) + name
            header = struct.pack(">4s5I", b"qres", 3, 24 + len(data) + len(name_data),
                                 24, 24 + len(data), 1)
            return header + data + name_data + nodes

        rejects("oversize-declaration", compressed_archive(64 * 1024 * 1024 + 1, b""))
        rejects("corrupt-zlib", compressed_archive(8, b"broken"))
        rejects("false-zlib-size", compressed_archive(1, zlib.compress(b"x" * 1000)))
        rejects("trailing-zlib-data", compressed_archive(1, zlib.compress(b"x") + b"extra"))
        compressed = zlib.compress(b"x" * (64 * 1024 * 1024))
        rejects("total-output-limit", compressed_archive(64 * 1024 * 1024, compressed, 5))
        work = case("batch-node-limit")
        # A valid 10,000-node tree of empty directories needs no large payload.
        name_data = b""
        nodes = struct.pack(">IHIIQ", 0, 2, 9999, 1, 0)
        for index in range(9999):
            name = f"d{index}".encode("utf-16-be")
            nodes += struct.pack(">IHIIQ", len(name_data), 2, 0, 0, 0)
            name_data += struct.pack(">HI", len(name) // 2, 0) + name
        large_tree = struct.pack(">4s5I", b"qres", 3, 24 + len(name_data), 24, 24, 0)
        (work / "many.rcc").write_bytes(large_tree + name_data + nodes)
        (work / "one.rcc").write_bytes(seed)
        run([binary, "-r", "many.rcc", "one.rcc"], work, False)
        assert not (work / "qresource").exists()
        assert not list(work.glob(".rccextended-*"))
        print(f"PASS: {checks} offline cases (round trips, CLI, malformed inputs and output safety)")


if __name__ == "__main__":
    main()
