FROM mambaorg/micromamba:latest

# Set up the environment
COPY --chown=$MAMBA_USER:$MAMBA_USER conda_env.yml /tmp/conda_env.yml
RUN micromamba install -y -n base -f /tmp/conda_env.yml && \
    micromamba clean --all --yes

# Copy the application code
COPY --chown=$MAMBA_USER:$MAMBA_USER . /app
WORKDIR /app

# Run unit tests during build
# If tests fail, the build fails and Render won't deploy
# Run unit tests during build
# If tests fail, the build fails and Render won't deploy
RUN micromamba run -n base python -m pytest

# Expose the port (Render uses $PORT)
ENV PORT=8000
EXPOSE $PORT

# Start the application using uvicorn
# We use a shell to expand the $PORT variable
CMD ["sh", "-c", "micromamba run -n base uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
