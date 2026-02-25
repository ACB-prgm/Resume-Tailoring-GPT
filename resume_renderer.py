from reportlab.platypus import (
	SimpleDocTemplate,
	Paragraph,
	Spacer,
	HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from dataclasses import fields
from io import BytesIO
import re

from resume_theme import ResumeTheme, ParagraphConfig


class ResumeRenderer:

	def __init__(self, theme: ResumeTheme):
		self.theme = theme
		self.styles = self._build_styles()

	def _config_kwargs(self, config_obj, skip_none: bool = True):
		kwargs = {}
		for field in fields(config_obj):
			value = getattr(config_obj, field.name)
			if skip_none and value is None:
				continue
			kwargs[field.name] = value
		return kwargs

	def _build_styles(self):
		styles = {}

		styles["normal"] = ParagraphStyle(
			"Normal",
			**self._config_kwargs(self.theme.normal)
		)

		# Auto-register any additional ParagraphConfig fields on the theme.
		for name, config in vars(self.theme).items():
			if name == "normal" or not isinstance(config, ParagraphConfig):
				continue
			styles[name] = ParagraphStyle(
				name.upper(),
				parent=styles["normal"],
				**self._config_kwargs(config)
			)

		if "bullet" not in styles:
			styles["bullet"] = styles["normal"]

		return styles

	def _convert_links(self, text: str) -> str:
		pattern = r"\[(.*?)\]\((.*?)\)"
		return re.sub(
			pattern,
			lambda m: self.theme.inline.link_tag_template.format(
				url=m.group(2),
				text=m.group(1)
			),
			text
		)

	def _convert_bold(self, text: str) -> str:
		return re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

	def _parse_line(self, line: str):
		line = line.strip()

		if not line:
			return None

		# Heading (##..######) maps to style keys h2..h6.
		heading_match = re.match(r"^(#{2,6})\s+(.*)$", line)
		if heading_match:
			level = len(heading_match.group(1))
			return (f"h{level}", heading_match.group(2).strip())

		# Horizontal rule
		if line == "---":
			return ("hr", None)

		# Bullet
		if line.startswith("- ") or line.startswith("* "):
			return ("bullet", line[2:].strip())

		# Normal paragraph
		return ("normal", line)

	def _build_story(self, markdown_text: str):
		story = []
		lines = markdown_text.split("\n")
		bullet_buffer = []

		for raw_line in lines:
			parsed = self._parse_line(raw_line)

			if parsed is None:
				continue

			type_, content = parsed

			# Flush bullet buffer if switching types
			if type_ != "bullet" and bullet_buffer:
				for item in bullet_buffer:
					story.append(Paragraph(item, self.styles["bullet"], bulletText="\u2022"))
				# If the next block is a section heading (h2), let heading spacing handle it.
				if type_ != "h2":
					story.append(Spacer(1, self.theme.section_spacer.height))
				bullet_buffer = []

			if type_.startswith("h") and type_[1:].isdigit():
				style_name = type_ if type_ in self.styles else "normal"
				story.append(Paragraph(content, self.styles[style_name]))

				# Keep current behavior: only h2 headings get divider lines.
				if type_ == "h2":
					story.append(
						HRFlowable(
							**self._config_kwargs(self.theme.section_rule)
						)
					)

			elif type_ == "hr":
				hr_kwargs = self._config_kwargs(self.theme.section_rule)
				hr_kwargs.pop("spaceBefore", None)
				hr_kwargs.pop("spaceAfter", None)
				story.append(
					HRFlowable(
						**hr_kwargs
					)
				)

			elif type_ == "bullet":
				formatted = self._convert_links(self._convert_bold(content))
				bullet_buffer.append(formatted)

			elif type_ == "normal":
				formatted = self._convert_links(self._convert_bold(content))
				story.append(Paragraph(formatted, self.styles["normal"]))

		# Flush remaining bullets
		if bullet_buffer:
			for item in bullet_buffer:
				story.append(Paragraph(item, self.styles["bullet"], bulletText="\u2022"))

		return story

	def exceeds_one_page(self, markdown_text: str) -> bool:
		"""Return True when this markdown would render to more than one page."""
		doc_kwargs = self._config_kwargs(self.theme.doc)
		buffer = BytesIO()
		doc = SimpleDocTemplate(buffer, **doc_kwargs)
		doc.build(self._build_story(markdown_text))
		return getattr(doc, "page", 1) > 1

	def render(self, markdown_text: str, output_path: str):
		doc_kwargs = self._config_kwargs(self.theme.doc)
		doc = SimpleDocTemplate(
			output_path,
			**doc_kwargs
		)
		story = self._build_story(markdown_text)
		doc.build(story)
