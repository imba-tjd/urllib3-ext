import setuptools
setuptools.setup(
    name='urllib3-ext',
    version='1.0',
    py_modules=['urllib3_ext'],
    # install_requires=['urllib3>=2']
)

assert __import__('urllib3').__version__[0] == '2'
