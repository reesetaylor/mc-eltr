import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mc-eltr-vpcuitis", # Replace with your own username
    version="0.0.1",
    author="Vincentas Prancuitis",
    author_email="vincentasprancuitis@gmail.com",
    description="Enhanced loot table randomizer for Minecraft based on SethBling/Fasguy's original script",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vpcuitis/mc-eltr",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)