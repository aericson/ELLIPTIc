# Authors:
# Guilherme Caminha <gpkc@cin.ufpe.br>

FROM gpkc/pymoab-pytrilinos
MAINTAINER Guilherme Caminha <gpkc@cin.ufpe.br>

RUN easy_install pytest
RUN git clone https://github.com/gpkc/ELLIPTIc.git
WORKDIR $HOME/ELLIPTIc

RUN python setup.py build
