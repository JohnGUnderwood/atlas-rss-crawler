. venv/bin/activate && \
cd frontend && \
npm run build && \
cd .. && \
supervisord -c supervisord.conf