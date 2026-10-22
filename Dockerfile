# Always-on hosting (Hugging Face Spaces, Railway, Render, Fly.io, any VPS).
FROM python:3.13-slim

# lightgbm needs the OpenMP runtime
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Run as a normal user (uid 1000, required by Hugging Face) that owns the app
# folder: the app writes users.db and .ml_cache next to its code.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user . .

# Hugging Face routes to 8501 (README app_port); other hosts may set $PORT.
ENV PORT=8501
EXPOSE 8501
CMD streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true
