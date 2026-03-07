"""HTML template loader for documentation pages"""

from pathlib import Path


class TemplateLoader:
    """
    Loads HTML templates from the templates directory

    Single Responsibility:
    - Only loads and returns HTML template content
    - Does NOT serve routes or handle HTTP
    """

    _TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

    @classmethod
    def load(cls, template_name: str) -> str:
        """
        Load HTML template from file

        Args:
            template_name: Name of template file (e.g., 'swagger_ui.html')

        Returns:
            HTML content as string

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = cls._TEMPLATES_DIR / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
