import setuptools

with open('README.md', 'r') as file:
    long_description = file.read()

setuptools.setup(
    name='example-pkg-your-username',
    version='0.0.1',
    author='Sam Henry',
    author_email='samuel.e.henry97@gmail.com',
    description='A utility package for editing grammars (CFG, PDA, etc)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/pypa/sampleproject',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)