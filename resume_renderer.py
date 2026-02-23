from reportlab.platypus import (
	SimpleDocTemplate,
	Paragraph,
	Spacer,
	HRFlowable,
	ListFlowable,
	ListItem
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
import re

from resume_theme import ResumeTheme


class ResumeRenderer:

	def __init__(self, theme: ResumeTheme):
		self.theme = theme
		self.styles = self._build_styles()

	def _build_styles(self):
		styles = {}

		styles["normal"] = ParagraphStyle(
			"Normal",
			fontName=self.theme.normal.font_name,
			fontSize=self.theme.normal.font_size,
			leading=self.theme.normal.leading,
			spaceBefore=self.theme.normal.space_before,
			spaceAfter=self.theme.normal.space_after,
			leftIndent=self.theme.normal.left_indent,
			rightIndent=self.theme.normal.right_indent,
			firstLineIndent=self.theme.normal.first_line_indent,
			alignment=self.theme.normal.alignment
		)

		styles["h2"] = ParagraphStyle(
			"H2",
			parent=styles["normal"],
			fontName=self.theme.h2.font_name,
			fontSize=self.theme.h2.font_size,
			leading=self.theme.h2.leading,
			spaceAfter=self.theme.h2.space_after,
			keepWithNext=self.theme.h2.keep_with_next
		)

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

		# Section Heading
		if line.startswith("## "):
			return ("section", line[3:].strip())

		# Horizontal rule
		if line == "---":
			return ("hr", None)

		# Bullet
		if line.startswith("- "):
			return ("bullet", line[2:].strip())

		# Normal paragraph
		return ("paragraph", line)

	def render(self, markdown_text: str, output_path: str):
		doc = SimpleDocTemplate(
			output_path,
			pagesize=self.theme.doc.page_size,
			leftMargin=self.theme.doc.left_margin,
			rightMargin=self.theme.doc.right_margin,
			topMargin=self.theme.doc.top_margin,
			bottomMargin=self.theme.doc.bottom_margin
		)

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
				story.append(
					ListFlowable(
						[ListItem(Paragraph(item, self.styles["normal"])) for item in bullet_buffer],
						bulletType='bullet'
					)
				)
				story.append(Spacer(1, self.theme.section_spacer.height))
				bullet_buffer = []

			if type_ == "section":
				story.append(Paragraph(content, self.styles["h2"]))
				story.append(
					HRFlowable(
						thickness=self.theme.section_rule.thickness,
						width=self.theme.section_rule.width,
						spaceBefore=self.theme.section_rule.space_before,
						spaceAfter=self.theme.section_rule.space_after
					)
				)

			elif type_ == "hr":
				story.append(
					HRFlowable(
						thickness=self.theme.section_rule.thickness,
						width=self.theme.section_rule.width
					)
				)

			elif type_ == "bullet":
				formatted = self._convert_links(self._convert_bold(content))
				bullet_buffer.append(formatted)

			elif type_ == "paragraph":
				formatted = self._convert_links(self._convert_bold(content))
				story.append(Paragraph(formatted, self.styles["normal"]))

		# Flush remaining bullets
		if bullet_buffer:
			story.append(
				ListFlowable(
					[ListItem(Paragraph(item, self.styles["normal"])) for item in bullet_buffer],
					bulletType='bullet'
				)
			)

		doc.build(story)