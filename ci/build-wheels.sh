#!/bin/bash
set -e -x


# Compile wheels
for PYBIN in /opt/python/*/bin; do
    if [[ "${PYBIN}" == *"cp27"* ]]; then
        continue
    fi
    if [[ "${PYBIN}" == *"cp34"* ]]; then
        continue
    fi
    "${PYBIN}/pip" install -r /io/requirements.txt
    "${PYBIN}/pip" wheel /io/ -w /io/wheels/
done

# Bundle external shared libraries into the wheels
for whl in /io/wheels/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheels/
    # Delete the original wheel. They are unusable as they contain no valid platform tag.
    rm "$whl"
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    if [[ "${PYBIN}" == *"cp27"* ]]; then
        continue
    fi
    if [[ "${PYBIN}" == *"cp34"* ]]; then
        continue
    fi
    "${PYBIN}/pip" install littlefs-python --no-index -f /io/wheels
    "${PYBIN}/py.test" /io/test
done
