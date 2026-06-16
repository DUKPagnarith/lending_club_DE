# Bitnami deprecated its public Docker Hub catalog in 2025; the old public tags
# (bitnami/spark:3.5.0) were removed and archived under the `bitnamilegacy` org.
# This image keeps the SPARK_MODE master/worker entrypoint the compose file uses.
FROM bitnamilegacy/spark:3.5.0
USER root
RUN pip install --no-cache-dir \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    scikit-learn>=1.3.0 \
    statsmodels>=0.14.0 \
    pyarrow>=12.0.0 \
    boto3>=1.34.0 \
    psycopg2-binary>=2.9.0
