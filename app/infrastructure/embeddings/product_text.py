"""Monta o texto enviado ao modelo de embedding a partir dos dados do produto."""


def build_index_text(
    *,
    name: str,
    description: str | None,
    sku: str,
    category: str | None,
) -> str:
    parts: list[str] = [name.strip()]
    if description and description.strip():
        parts.append(description.strip())
    parts.append(f"SKU {sku.strip()}")
    if category and category.strip():
        parts.append(f"Categoria {category.strip()}")
    return " | ".join(parts)
