from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
FONTS_DIR = ROOT / "public" / "fonts"
RAW_DIR = ROOT / "scripts" / ".font-cache"
SUBSET_DIR = FONTS_DIR / "subset"

STATIC_EXTENSIONS = {".astro", ".css", ".ts", ".tsx"}

COMMON_CHINESE_URL = (
    "https://raw.githubusercontent.com/"
    "shengdoushi/common-standard-chinese-characters-table/master/level-1.txt"
)

FONT_SOURCES = {
    "bagel": (
        "BagelFatOne-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bagelfatone/"
        "BagelFatOne-Regular.ttf",
    ),
    "fraunces": (
        "Fraunces.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/"
        "Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf",
    ),
    "fraunces_italic": (
        "Fraunces-Italic.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/"
        "Fraunces-Italic%5BSOFT,WONK,opsz,wght%5D.ttf",
    ),
    "ma_shan": (
        "MaShanZheng-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/mashanzheng/"
        "MaShanZheng-Regular.ttf",
    ),
    "space_mono_regular": (
        "SpaceMono-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/spacemono/"
        "SpaceMono-Regular.ttf",
    ),
    "space_mono_bold": (
        "SpaceMono-Bold.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/spacemono/"
        "SpaceMono-Bold.ttf",
    ),
    "zcool": (
        "ZCOOLKuaiLe-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/zcoolkuaile/"
        "ZCOOLKuaiLe-Regular.ttf",
    ),
}

LATIN_TEXT = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    " !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
)
COMMON_PUNCTUATION = "，。！？、；：“”‘’（）《》【】—…·￥％℃№～"
PROJECT_TERMS = (
    "摸鱼热榜公开榜单链接聚合器首页热榜美股大盘平台微博知乎百度抖音"
    "哔哩哔哩虎扑贴吧豆瓣少数派华尔街见闻财联社金十数据雪球牛客"
    "老板键刷新免责声明仅供信息展示不构成投资建议沿用趣味风格设计规范"
)


def unique_chars(text: str) -> str:
    return "".join(dict.fromkeys(text))


def collect_static_chars() -> str:
    text_parts: list[str] = [LATIN_TEXT, COMMON_PUNCTUATION, PROJECT_TERMS]
    for path in SRC_DIR.rglob("*"):
        if path.suffix not in STATIC_EXTENSIONS or path.is_dir():
            continue
        text_parts.append(path.read_text(encoding="utf-8"))

    text = "\n".join(text_parts)
    chars = re.findall(r"[\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]|[ -~]", text)
    return unique_chars("".join(chars))


def download_sources() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SUBSET_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in FONT_SOURCES.values():
        target = RAW_DIR / filename
        if not target.exists():
            urlretrieve(url, target)

    common_target = RAW_DIR / "common-standard-chinese-level-1.txt"
    if not common_target.exists():
        urlretrieve(COMMON_CHINESE_URL, common_target)


def load_common_chinese() -> str:
    chars = (RAW_DIR / "common-standard-chinese-level-1.txt").read_text(encoding="utf-8")
    return unique_chars("".join(chars.split()))


def write_charset_files(static_chars: str, common_chars: str) -> tuple[Path, Path]:
    static_file = RAW_DIR / "static-ui-chars.txt"
    common_file = RAW_DIR / "common-cn-3500-chars.txt"
    static_file.write_text(static_chars, encoding="utf-8")
    common_file.write_text(unique_chars(static_chars + common_chars), encoding="utf-8")
    return static_file, common_file


def run_subset(source: Path, output: Path, text_file: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "fontTools.subset",
        str(source),
        f"--text-file={text_file}",
        "--flavor=woff2",
        "--layout-features=*",
        "--desubroutinize",
        "--no-hinting",
        f"--output-file={output}",
    ]
    subprocess.run(command, check=True)


def write_css() -> None:
    css = """@font-face {
  font-family: 'Bagel Fat One';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('/fonts/subset/bagel-fat-one-ui.woff2') format('woff2');
}

@font-face {
  font-family: 'Fraunces';
  font-style: normal;
  font-weight: 400 800;
  font-display: swap;
  src: url('/fonts/subset/fraunces-ui.woff2') format('woff2');
}

@font-face {
  font-family: 'Fraunces';
  font-style: italic;
  font-weight: 400 800;
  font-display: swap;
  src: url('/fonts/subset/fraunces-italic-ui.woff2') format('woff2');
}

@font-face {
  font-family: 'Ma Shan Zheng';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('/fonts/subset/ma-shan-zheng-common-cn.woff2') format('woff2');
}

@font-face {
  font-family: 'Space Mono';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('/fonts/subset/space-mono-regular-ui.woff2') format('woff2');
}

@font-face {
  font-family: 'Space Mono';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url('/fonts/subset/space-mono-bold-ui.woff2') format('woff2');
}

@font-face {
  font-family: 'ZCOOL KuaiLe';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('/fonts/subset/zcool-kuaile-ui.woff2') format('woff2');
}
"""
    (FONTS_DIR / "fonts-subset.css").write_text(css, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    if not args.skip_download:
        download_sources()

    static_chars = collect_static_chars()
    common_chars = load_common_chinese()
    static_file, common_file = write_charset_files(static_chars, common_chars)

    raw = {name: RAW_DIR / filename for name, (filename, _) in FONT_SOURCES.items()}
    run_subset(raw["bagel"], SUBSET_DIR / "bagel-fat-one-ui.woff2", static_file)
    run_subset(raw["fraunces"], SUBSET_DIR / "fraunces-ui.woff2", static_file)
    run_subset(raw["fraunces_italic"], SUBSET_DIR / "fraunces-italic-ui.woff2", static_file)
    run_subset(raw["ma_shan"], SUBSET_DIR / "ma-shan-zheng-common-cn.woff2", common_file)
    run_subset(raw["space_mono_regular"], SUBSET_DIR / "space-mono-regular-ui.woff2", static_file)
    run_subset(raw["space_mono_bold"], SUBSET_DIR / "space-mono-bold-ui.woff2", static_file)
    run_subset(raw["zcool"], SUBSET_DIR / "zcool-kuaile-ui.woff2", static_file)
    write_css()

    total = sum(path.stat().st_size for path in SUBSET_DIR.glob("*.woff2"))
    print(f"static chars: {len(static_chars)}")
    print(f"common chars: {len(common_chars)}")
    print(f"subset fonts: {total / 1024:.1f} KiB")


if __name__ == "__main__":
    main()
