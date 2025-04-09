from setuptools import setup, find_packages

setup(
    name="dados-abertos-setor-eletrico",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Copia daqui do seu requirements.txt
    ],
    author="Diego Neri",
    author_email="seu-email@example.com",  # Troque para seu email real
    description="Coleta e tratamento de dados públicos do setor elétrico brasileiro (ONS e ANEEL).",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/diegonerii/Dados-Abertos-Setor-Eletrico-Brasileiro",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
