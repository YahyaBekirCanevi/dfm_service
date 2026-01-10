FROM mambaorg/micromamba:latest

# Set up the environment
COPY --chown=$MAMBA_USER:$MAMBA_USER conda_env.yml /tmp/conda_env.yml
RUN micromamba install -y -n base -f /tmp/conda_env.yml && \
    micromamba clean --all --yes

# Copy the application code
COPY --chown=$MAMBA_USER:$MAMBA_USER . /app
WORKDIR /app

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the application using uvicorn
# Note: Render provides a $PORT environment variable
CMD ["micromamba", "run", "-n", "base", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
