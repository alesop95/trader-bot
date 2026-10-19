#!/usr/bin/env python3
"""Lossless storage for derived caches; never recompress original documents."""
import argparse
import bz2
import ctypes
import gzip
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time

TEXT_EXTENSIONS = {'.txt', '.json', '.jsonl', '.md', '.csv', '.tsv', '.xml', '.html', '.log'}
CODEC_SUFFIXES = ('', '.gz', '.bz2', '.xz')
WOF_TAG = 0x80000017


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def open_text(path):
    path = Path(path)
    opener = {'.gz': gzip.open, '.bz2': bz2.open, '.xz': lzma.open}.get(path.suffix, open)
    return opener(path, 'rt', encoding='utf-8', newline='')


def smallest_bytes(data, compression='auto'):
    """Choose the smallest verified encoding, including the uncompressed input."""
    if compression not in {'plain', 'auto', 'gzip', 'bzip2', 'xz'}:
        raise ValueError('Unsupported compression')
    best = ('', data)
    if compression == 'plain':
        return best
    choices = [('gzip', '.gz', lambda: gzip.compress(data, compresslevel=9, mtime=0), gzip.decompress),
               ('bzip2', '.bz2', lambda: bz2.compress(data, compresslevel=9), bz2.decompress),
               ('xz', '.xz', lambda: lzma.compress(data, preset=9 | lzma.PRESET_EXTREME), lzma.decompress)]
    for name, suffix, encode, decode in choices:
        if compression not in {'auto', name}:
            continue
        encoded = encode()
        if decode(encoded) != data:
            raise ValueError('Compression round trip failed')
        if len(encoded) < len(best[1]):
            best = (suffix, encoded)
    return best


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Named temporary lives beside the destination, on the same filesystem.
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.part', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def cache_variant(base):
    candidates = [Path(str(base) + suffix) for suffix in CODEC_SUFFIXES]
    present = [p for p in candidates if p.is_file()]
    if len(present) > 1:
        # An interrupted migration can leave identical variants; conflicting data is an error.
        contents = []
        for path in present:
            with open_text(path) as stream:
                contents.append(stream.read())
        if len(set(contents)) != 1:
            raise ValueError('Conflicting cache variants: ' + str(base))
    return min(present, key=lambda p: (p.stat().st_size, str(p))) if present else None


def write_cached_text(base, text, compression='auto'):
    base = Path(base)
    suffix, data = smallest_bytes(text.encode('utf-8'), compression)
    destination = Path(str(base) + suffix)
    atomic_write(destination, data)
    with open_text(destination) as stream:
        if stream.read() != text:
            raise ValueError('Stored cache verification failed')
    # The caller explicitly selects a derived mirror. Retire only its alternate encodings.
    for old_suffix in CODEC_SUFFIXES:
        old = Path(str(base) + old_suffix)
        if old != destination:
            old.unlink(missing_ok=True)
    return destination


def save_smallest_lossless(image, base):
    """Save a newly generated RGB/L/RGBA raster; preserve every decoded RGBA pixel."""
    from PIL import Image
    if image.mode not in {'L', 'RGB', 'RGBA'} or image.info:
        raise ValueError('Only generated rasters without source metadata are supported')
    original = image.convert('RGBA')
    expected = original.tobytes()
    choices = []
    representations = [image]
    gray = image.convert('L')
    if gray.convert('RGBA').tobytes() == expected:
        representations.append(gray)
    for representation in representations:
        encoded = io.BytesIO()
        representation.save(encoded, format='PNG', optimize=True)
        choices.append(('.png', encoded.getvalue()))
    try:
        encoded = io.BytesIO()
        image.save(encoded, format='WEBP', lossless=True, quality=100, method=6, exact=True)
        choices.append(('.webp', encoded.getvalue()))
    except (OSError, KeyError):
        pass  # A Pillow build without WebP retains lossless PNG.
    suffix, data = min(choices, key=lambda item: len(item[1]))
    with Image.open(io.BytesIO(data)) as decoded:
        if decoded.size != image.size or decoded.convert('RGBA').tobytes() != expected:
            raise ValueError('Image pixels changed during lossless encoding')
    destination = Path(str(base) + suffix)
    atomic_write(destination, data)
    with Image.open(destination) as decoded:
        if decoded.convert('RGBA').tobytes() != expected:
            raise ValueError('Stored image verification failed')
    return destination, {'bytes': len(data), 'pixel_sha256': hashlib.sha256(expected).hexdigest(),
                         'width': image.width, 'height': image.height, 'format': suffix[1:],
                         'pixels_unchanged': True}


def confined_cache(project, cache):
    project, cache = Path(project).resolve(), Path(cache).absolute()
    if not cache.is_relative_to(project) or cache == project:
        raise ValueError('Cache must be inside the project')
    relative = cache.relative_to(project)
    if not any('cache' in part.lower() for part in relative.parts):
        raise ValueError('Explicit derived cache directory required')
    for current in [cache, *cache.parents]:
        if current == project:
            break
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError('Cache path traverses a link or junction')
    if cache.resolve() != cache:
        raise ValueError('Cache path is not canonical')
    return project, cache


def stored_bytes(path):
    if os.name != 'nt':
        return path.stat().st_size
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    function = kernel.GetCompressedFileSizeW
    function.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    function.restype = ctypes.c_ulong
    high = ctypes.c_ulong()
    ctypes.set_last_error(0)
    low = function(str(path), ctypes.byref(high))
    if low == 0xFFFFFFFF and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    return (high.value << 32) | low


def text_cache_files(cache):
    for directory, children, names in os.walk(cache, followlinks=False):
        children[:] = [name for name in children if name.lower() not in {'backup', 'originali', 'originals'}
                      and not (Path(directory) / name).is_symlink()
                      and not (hasattr(Path, 'is_junction') and (Path(directory) / name).is_junction())]
        for name in names:
            path = Path(directory) / name
            info = path.lstat()
            tag = getattr(info, 'st_reparse_tag', 0)
            if path.suffix.lower() in TEXT_EXTENSIONS and info.st_size >= 4096 and not path.is_symlink():
                if tag and tag != WOF_TAG:
                    continue
                yield path


def compact_ntfs(project, cache, report_path, apply=False):
    project, cache = confined_cache(project, cache)
    report_path = Path(report_path).absolute()
    if not report_path.resolve().is_relative_to(project):
        raise ValueError('Report must stay inside the project')
    if apply and os.name != 'nt':
        raise ValueError('Transparent LZX compression requires Windows and an NTFS target')
    rows, errors = [], []
    start = time.perf_counter()
    files = sorted(text_cache_files(cache))
    for offset in range(0, len(files), 32):
        batch = files[offset:offset + 32]
        before = [(p, p.stat().st_size, stored_bytes(p), sha256(p)) for p in batch]
        if apply:
            result = subprocess.run(['compact.exe', '/C', '/EXE:LZX', *map(str, batch)],
                                    capture_output=True, text=True)
            if result.returncode:
                errors.append({'batch': offset, 'exit_code': result.returncode,
                               'output': result.stdout + result.stderr})
        for path, logical, stored, digest in before:
            after_hash = sha256(path)
            if after_hash != digest:
                raise ValueError('File changed during compression: ' + str(path))
            rows.append({'path': path.relative_to(project).as_posix(), 'logical_bytes': logical,
                         'before_stored_bytes': stored, 'after_stored_bytes': stored_bytes(path),
                         'sha256': digest, 'byte_identity_verified': True})
        if apply and offset % 320 == 0:
            print(json.dumps({'verified':len(rows),'total':len(files)}), flush=True)
    report = {'scope': str(cache.relative_to(project)), 'apply': apply, 'method': 'NTFS LZX',
              'files': rows, 'errors': errors, 'seconds': time.perf_counter() - start,
              'logical_bytes': sum(r['logical_bytes'] for r in rows),
              'before_stored_bytes': sum(r['before_stored_bytes'] for r in rows),
              'after_stored_bytes': sum(r['after_stored_bytes'] for r in rows)}
    # Reports may be large; use the same verified portable storage as other derived data.
    destination = write_cached_text(report_path, json.dumps(report, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'files'}, ensure_ascii=False))
    print('REPORT: ' + str(destination))
    return report


def optimize_png(path, apply=False):
    """Re-encode derived PNGs in place only when pixels and supported metadata match."""
    from PIL import Image
    path = Path(path)
    original_bytes = path.read_bytes()
    with Image.open(io.BytesIO(original_bytes)) as opened:
        if opened.mode not in {'RGB', 'RGBA', 'L'} or getattr(opened, 'n_frames', 1) != 1:
            return None
        if set(opened.info) - {'dpi'}:
            return None
        image, metadata = opened.copy(), dict(opened.info)
    expected = image.convert('RGBA').tobytes()
    gray = image.convert('L')
    if gray.convert('RGBA').tobytes() != expected:
        return None
    buffer = io.BytesIO()
    gray.save(buffer, format='PNG', optimize=True, **metadata)
    encoded = buffer.getvalue()
    if len(encoded) >= len(original_bytes):
        return None
    with Image.open(io.BytesIO(encoded)) as decoded:
        if decoded.convert('RGBA').tobytes() != expected or decoded.info != metadata:
            raise ValueError('PNG pixels or metadata changed: ' + str(path))
    old_hash = hashlib.sha256(original_bytes).hexdigest()
    if apply:
        if sha256(path) != old_hash:
            raise ValueError('PNG changed concurrently: ' + str(path))
        atomic_write(path, encoded)
        if sha256(path) != hashlib.sha256(encoded).hexdigest():
            raise ValueError('Stored PNG verification failed')
    return {'before_bytes':len(original_bytes),'after_bytes':len(encoded),
            'before_sha256':old_hash,'after_sha256':hashlib.sha256(encoded).hexdigest(),
            'pixel_sha256':hashlib.sha256(expected).hexdigest(),'pixels_and_metadata_unchanged':True}


def png_cache(project, cache, report_path, apply=False):
    project, cache = confined_cache(project, cache)
    if not Path(report_path).resolve().is_relative_to(project):
        raise ValueError('Report must stay inside the project')
    paths = []
    for directory, children, files in os.walk(cache, followlinks=False):
        children[:] = [n for n in children if not (Path(directory) / n).is_symlink()
                      and not getattr((Path(directory) / n).stat(), 'st_file_attributes', 0) & 1024]
        paths.extend(Path(directory) / n for n in files if n.lower().endswith('.png')
                     and not (Path(directory) / n).is_symlink())
    rows = []
    before = sum(p.stat().st_size for p in paths)
    start = time.perf_counter()
    for number, path in enumerate(sorted(paths), 1):
        result = optimize_png(path, apply)
        if result:
            rows.append({'path':path.relative_to(project).as_posix(),**result})
        if number % 100 == 0:
            print(json.dumps({'png_checked':number,'png_total':len(paths),'optimized':len(rows)}), flush=True)
    saved = sum(r['before_bytes'] - r['after_bytes'] for r in rows)
    report = {'method':'Lossless grayscale PNG with identical RGBA pixels and metadata',
              'scope':cache.relative_to(project).as_posix(),'apply':apply,'checked':len(paths),
              'optimized':len(rows),'before_bytes':before,'after_bytes':before-saved,
              'saved_bytes':saved,'seconds':time.perf_counter()-start,'files':rows}
    destination = write_cached_text(report_path, json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'files'},ensure_ascii=False))
    print('REPORT: ' + str(destination))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    read = sub.add_parser('read', help='Read plain/gzip/bzip2/xz text without a persistent extracted copy')
    read.add_argument('path', type=Path)
    read.add_argument('--first', type=int, default=1)
    read.add_argument('--last', type=int)
    compact = sub.add_parser('ntfs', help='Measure or apply transparent LZX to derived text caches only')
    compact.add_argument('--project-root', type=Path, required=True)
    compact.add_argument('--cache', type=Path, required=True)
    compact.add_argument('--report', type=Path, required=True)
    compact.add_argument('--apply', action='store_true')
    png = sub.add_parser('png', help='Optimize derived grayscale PNGs without changing names, pixels or metadata')
    png.add_argument('--project-root', type=Path, required=True)
    png.add_argument('--cache', type=Path, required=True)
    png.add_argument('--report', type=Path, required=True)
    png.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.command == 'read':
        if args.first < 1 or (args.last is not None and args.last < args.first):
            parser.error('Invalid line range')
        with open_text(args.path) as stream:
            for number, line in enumerate(stream, 1):
                if args.last is not None and number > args.last:
                    break
                if number >= args.first:
                    print(line, end='')
    elif args.command == 'ntfs':
        report = compact_ntfs(args.project_root, args.cache, args.report, args.apply)
        return 1 if report['errors'] else 0
    else:
        png_cache(args.project_root, args.cache, args.report, args.apply)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
