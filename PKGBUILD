# Contributor: Danny (https://github.com/carrolldant-glitch) <carrolldant@gmail.com>
# Former Maintainer: Mariusz Libera <mariusz.libera@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only WITH Qt-GPL-exception-1.0
# LOCAL REVIEW ONLY: clean-chroot verification and release approval remain.
pkgname=rccextended
pkgver=1.0.6
pkgrel=2
_license_commit=eea2824a1a602a89d9270fc64020a735584958ce
pkgdesc='Qt resource compiler and decompiler with bounded offline extraction'
arch=('x86_64')
url='https://github.com/zedxxx/rccextended'
license=('GPL-3.0-only WITH Qt-GPL-exception-1.0')
depends=('glibc' 'libgcc' 'libstdc++' 'qt5-base' 'zlib' 'zstd')
checkdepends=('python' 'shellcheck')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz"
        "$pkgname-$_license_commit-license.patch::$url/commit/$_license_commit.patch"
        'resource-safety.patch'
        'check.py'
        'README.arch'
        'LICENSE-STATUS.txt')
sha256sums=('0949d2b0a47e56624f5bc2c57e90ad8115298ce69012bb4235dfd8f7ab00b599'
            'c707fd23813599bad85444465c509796f0aa0f7bfcf70d36b163a4c00f59f2d6'
            'e6d5f272d010dc512d2aa4819f7e2e3d265ad55b19b6a6bdcd5b9d0ca74fe2e8'
            '628bfef5e8e2cd3c1d50c8f51d14462da2bbca4464e3cef41c998082f67cf7a6'
            '6bb1226aaa8858d5450ddcbcf5f3b1a7bb8790ea96a14d204509bd0ba1daf2a8'
            'c2662ca405a951edfa2bbc61b08aa464ed00cbe76fa7833ef0ce1f636c0c9c08')

prepare() {
  cd "$pkgname-$pkgver" || return
  patch --batch --forward --fuzz=0 -Np1 -i "$srcdir/$pkgname-$_license_commit-license.patch" || return
  patch --batch --forward --fuzz=0 -Np1 -i "$srcdir/resource-safety.patch"
}

build() {
  mkdir -p build
  cd build || return
  qmake-qt5 "../$pkgname-$pkgver/src/rcc.pro" \
    "QMAKE_CFLAGS=$CFLAGS" "QMAKE_CXXFLAGS=$CXXFLAGS" "QMAKE_LFLAGS=$LDFLAGS" \
    QMAKE_CFLAGS_RELEASE= QMAKE_CXXFLAGS_RELEASE= QMAKE_LFLAGS_RELEASE=
  make
}

check() {
  local filename
  for filename in logger.cpp logger.h rccreverse.cpp rccreverse.h resinfo.cpp resinfo.h; do
    grep -Fxq '// SPDX-License-Identifier: GPL-3.0-only WITH Qt-GPL-exception-1.0' \
      "$srcdir/$pkgname-$pkgver/src/$filename" || return
  done
  grep -Fxq 'GNU GENERAL PUBLIC LICENSE' "$srcdir/$pkgname-$pkgver/LICENSE" || return
  grep -Fxq 'The Qt Company GPL Exception 1.0' "$srcdir/$pkgname-$pkgver/LICENSE.GPL3-EXCEPT" || return
  python "$srcdir/check.py" "$srcdir/build/rcc"
}

package() {
  install -Dm755 build/rcc "$pkgdir/usr/bin/rccextended"
  install -Dm644 "$srcdir/README.arch" "$pkgdir/usr/share/doc/$pkgname/README.arch"
  install -Dm644 "$pkgname-$pkgver/readme.md" "$pkgdir/usr/share/doc/$pkgname/README.upstream.md"
  install -Dm644 "$pkgname-$pkgver/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
  install -Dm644 "$pkgname-$pkgver/LICENSE.GPL3-EXCEPT" "$pkgdir/usr/share/licenses/$pkgname/LICENSE.GPL3-EXCEPT"
  install -Dm644 "$srcdir/LICENSE-STATUS.txt" "$pkgdir/usr/share/licenses/$pkgname/LICENSE-STATUS.txt"
}
