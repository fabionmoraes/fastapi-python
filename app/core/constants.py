# Alinhar com modelos de embedding (ex.: all-MiniLM-L6-v2 → 384 dimensões)
DEFAULT_EMBEDDING_DIMENSIONS: int = 384

_GEMINI_DESCRIPTION_SYSTEM = """Você é redator de e-commerce. Gere somente o texto da descrição do \
produto em português, sem título, sem markdown, em 2 a 4 parágrafos curtos, destacando benefícios \
e público-alvo quando fizer sentido."""