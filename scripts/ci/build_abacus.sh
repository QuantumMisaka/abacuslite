#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: build_abacus.sh --variant develop|lts --source-dir ABSOLUTE_PATH \
  --build-dir ABSOLUTE_PATH --report-dir ABSOLUTE_PATH --expected-sha FULL_40_HEX

Build a clean CPU/LCAO ABACUS checkout with two compile workers. The report
directory receives configure.log, build.log, version.log, ldd.log, and
build-provenance.json. A nonempty build directory is rejected (cold-build gate).
EOF
  exit 2
}

variant= source_dir= build_dir= report_dir= expected_sha=
while [[ $# -gt 0 ]]; do
  [[ $# -ge 2 ]] || usage
  case "$1" in
    --variant) variant=$2 ;;
    --source-dir) source_dir=$2 ;;
    --build-dir) build_dir=$2 ;;
    --report-dir) report_dir=$2 ;;
    --expected-sha) expected_sha=$2 ;;
    *) usage ;;
  esac
  shift 2
done
[[ "$variant" == develop || "$variant" == lts ]] || usage
[[ "$expected_sha" =~ ^[0-9a-f]{40}$ ]] || usage
for value in "$source_dir" "$build_dir" "$report_dir"; do
  [[ "$value" == /* ]] || usage
done

source_dir=$(realpath -e -- "$source_dir")
build_dir=$(realpath -m -- "$build_dir")
report_dir=$(realpath -m -- "$report_dir")
[[ -f "$source_dir/CMakeLists.txt" ]] || {
  echo "No CMakeLists.txt in source checkout: $source_dir" >&2
  exit 2
}
for value in "$build_dir" "$report_dir"; do
  case "$value/" in
    "$source_dir/"*)
      echo "Build and report directories must be outside the source checkout: $value" >&2
      exit 2 ;;
  esac
done
[[ "$build_dir" != "$report_dir" ]] || {
  echo 'Build and report directories must differ' >&2
  exit 2
}
source_root=$(git -C "$source_dir" rev-parse --show-toplevel)
[[ "$(realpath -e -- "$source_root")" == "$source_dir" ]] || {
  echo 'Source directory must be the Git checkout root' >&2
  exit 2
}
source_sha=$(git -C "$source_dir" rev-parse --verify 'HEAD^{commit}')
[[ "$source_sha" == "$expected_sha" ]] || {
  echo "Engine source SHA mismatch: expected $expected_sha, got $source_sha" >&2
  exit 2
}
[[ -z "$(git -C "$source_dir" status --porcelain --untracked-files=all)" ]] || {
  echo 'Engine source checkout is dirty' >&2
  exit 2
}
mkdir -p -- "$build_dir" "$report_dir"
[[ -z "$(find "$build_dir" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
  echo "Build directory must be empty for a cold build: $build_dir" >&2
  exit 2
}
[[ ! -e "$report_dir/build-provenance.json" ]] || {
  echo "Refusing to overwrite build provenance: $report_dir/build-provenance.json" >&2
  exit 2
}

options=(
  -DCMAKE_BUILD_TYPE=Release
  -DCMAKE_CXX_COMPILER="$(command -v g++)"
  -DENABLE_MPI=ON
  -DENABLE_LCAO=ON
  -DENABLE_LIBRI=OFF
  -DBUILD_TESTING=OFF
  -DGIT_SUBMODULE=OFF
  -DENABLE_NATIVE_OPTIMIZATION=OFF
  -DUSE_CUDA=OFF
  -DUSE_ROCM=OFF
)
if [[ "$variant" == develop ]]; then
  options+=(-DENABLE_OPENMP=ON -DENABLE_ELPA=OFF)
  binary_name=abacus_basic_para
else
  options+=(-DUSE_OPENMP=ON -DUSE_ELPA=OFF)
  binary_name=abacus
fi

start_epoch=$(date +%s)
echo "Configuring $variant $source_sha; log: $report_dir/configure.log"
cmake -S "$source_dir" -B "$build_dir" "${options[@]}" \
  >"$report_dir/configure.log" 2>&1

if grep -Eq 'Manually-specified variables were not used by the project|Ignoring extra path from command line' \
    "$report_dir/configure.log"; then
  echo 'CMake ignored an explicit build option; see configure.log' >&2
  exit 1
fi

# CMake can silently replace a deprecated or dependency-disabled option.
# Check every explicit switch against the resulting cache before compiling.
python3 - "$build_dir/CMakeCache.txt" "${options[@]}" <<'PY'
import pathlib
import sys

cache = {}
for line in pathlib.Path(sys.argv[1]).read_text().splitlines():
    if line.startswith(('#', '//')) or ':' not in line or '=' not in line:
        continue
    key, raw = line.split(':', 1)
    _kind, value = raw.split('=', 1)
    cache[key] = value
for option in sys.argv[2:]:
    key, wanted = option.removeprefix('-D').split('=', 1)
    actual = cache.get(key)
    if actual != wanted:
        raise SystemExit(f'CMake option {key} requested {wanted!r}, cached {actual!r}')
for key, needle in (
    ('BLAS_openblas_LIBRARY', 'openblas'),
    ('FFTW3_LIBRARY', 'fftw3'),
    ('ScaLAPACK_LIBRARY', 'scalapack'),
    ('MPI_CXX_COMPILER', 'mpi'),
):
    value = cache.get(key, '')
    if not value or needle not in value.lower() or not pathlib.Path(value).exists():
        raise SystemExit(f'Missing expected CPU dependency in CMake cache: {key}={value!r}')
PY
configured_epoch=$(date +%s)

echo "Building with two workers; log: $report_dir/build.log"
cmake --build "$build_dir" --parallel 2 >"$report_dir/build.log" 2>&1
built_epoch=$(date +%s)

binary=$(realpath -e -- "$build_dir/$binary_name")
[[ -x "$binary" ]] || {
  echo "Expected branch binary is not executable: $binary" >&2
  exit 1
}
"$binary" --version >"$report_dir/version.log" 2>&1
grep -Eq '^ABACUS version v[0-9]' "$report_dir/version.log" || {
  echo "Unexpected ABACUS --version output; see version.log" >&2
  exit 1
}
ldd "$binary" >"$report_dir/ldd.log" 2>&1
if grep -q 'not found' "$report_dir/ldd.log"; then
  echo 'Built engine has unresolved shared libraries; see ldd.log' >&2
  exit 1
fi

python3 - "$variant" "$source_dir" "$build_dir" "$report_dir" "$binary" \
  "$source_sha" "$start_epoch" "$configured_epoch" "$built_epoch" "${options[@]}" <<'PY'
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

(variant, source_dir, build_dir, report_dir, binary, source_sha,
 start, configured, built, *options) = sys.argv[1:]
source_dir = pathlib.Path(source_dir)
report_dir = pathlib.Path(report_dir)
binary = pathlib.Path(binary)

def output(*command):
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()

def version_line(*command):
    return output(*command).splitlines()[0]

packages = ('build-essential', 'cmake', 'git', 'libopenmpi-dev', 'openmpi-bin',
            'libfftw3-dev', 'libopenblas-dev', 'libscalapack-openmpi-dev',
            'libcereal-dev', 'pkg-config', 'python3')
dependencies = {}
for name in packages:
    dependencies[name] = output('dpkg-query', '-W', '-f=${Version}', name)
os_release = {}
for line in pathlib.Path('/etc/os-release').read_text().splitlines():
    if '=' in line:
        key, value = line.split('=', 1)
        os_release[key] = value.strip('"')
report = {
    'schema': 'abacus-cold-cpu-build-v1',
    'variant': variant,
    'source': {
        'directory': str(source_dir),
        'sha': source_sha,
        'tree_sha': output('git', '-C', str(source_dir), 'rev-parse', 'HEAD^{tree}'),
        'remote_origin': output('git', '-C', str(source_dir), 'config', '--get', 'remote.origin.url'),
        'clean': True,
    },
    'host': {'os': {key: os_release.get(key) for key in ('ID', 'VERSION_ID', 'PRETTY_NAME')},
             'kernel': platform.platform(), 'architecture': platform.machine()},
    'toolchain': {'cxx': version_line('g++', '--version'),
                  'cmake': version_line('cmake', '--version'),
                  'mpi': version_line('mpirun', '--version')},
    'dependencies': dependencies,
    'cmake_options': options,
    'compile_workers': 2,
    'build_directory': build_dir,
    'binary': {'path': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
               'version': (report_dir / 'version.log').read_text().strip()},
    'elapsed_seconds': {'configure': int(configured) - int(start),
                        'build': int(built) - int(configured),
                        'total': int(built) - int(start)},
    'logs': {name: str(report_dir / name) for name in
             ('configure.log', 'build.log', 'version.log', 'ldd.log')},
}
(report_dir / 'build-provenance.json').write_text(json.dumps(report, indent=2) + '\n')
print(f"Built {variant} {binary} sha256={report['binary']['sha256']} "
      f"in {report['elapsed_seconds']['total']}s")
PY
