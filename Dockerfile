FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY documents/ ./documents/

RUN pip install --no-cache-dir --no-deps -e .

ENV MCP_TRANSPORT=http
EXPOSE 8080

CMD ["python", "-m", "lismore_da_mcp.server"]
