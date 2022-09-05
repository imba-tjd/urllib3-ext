import subprocess
import sys
import glob
import os

if not os.path.exists('urllib3_ext_vendor.py'):
    subprocess.run([sys.executable, '-m', 'pip', 'wheel',
                   'https://github.com/urllib3/urllib3/archive/refs/heads/main.zip']).check_returncode()
    whl = glob.glob('urllib3-2*.whl')
    if len(whl) != 1:
        raise RuntimeError('Failed to build urllib3 wheel')
    os.rename(whl[0], 'urllib3_ext_vendor.py')


import setuptools
setuptools.setup(
    name='urllib3-ext',
    version='2.0b4',
    py_modules=['urllib3_ext', 'urllib3_ext_vendor'],
)
