FROM jupyter/base-notebook:dc9744740e12
EXPOSE 8888
ENV SETUPTOOLS_SCM_PRETEND_VERSION dev
ENV NODE_ENV production

COPY binder/environment.yml environment.yml
RUN conda update -n base conda && \
    conda env update --file environment.yml && \
    python -m ipykernel install --user && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda clean -afy

COPY mpcontribs-io/requirements.txt requirements-io.txt
COPY mpcontribs-client/requirements.txt requirements-client.txt
RUN cat requirements-*.txt > requirements.txt && pip install --no-cache-dir -r requirements.txt

USER root
COPY mpcontribs-io src/mpcontribs-io
COPY mpcontribs-client src/mpcontribs-client
COPY mpcontribs-api/kernel_imports.ipynb .
RUN chown -R $NB_USER:users src/mpcontribs-io && \
    chown -R $NB_USER:users src/mpcontribs-client && \
    chown $NB_USER:users kernel_imports.ipynb

USER $NB_USER

RUN cd src/mpcontribs-io && pip install --no-cache-dir -e . && \
    cd ../mpcontribs-client && pip install --no-cache-dir -e .

ENV GATEWAY_HOST=localhost:8888
ENV KG_ENV_PROCESS_WHITELIST=GATEWAY_HOST,MPCONTRIBS_API_HOST
CMD ["jupyter", "enterprisegateway", "--ip=0.0.0.0", "--port_retries=0", "--KernelGatewayApp.seed_uri='kernel_imports.ipynb'"]