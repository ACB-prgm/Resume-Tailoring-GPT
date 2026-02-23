from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT

# -------------------------
# Document Defaults
# -------------------------

@dataclass
class DocumentDefaults:
	page_size: tuple = A4
	left_margin: float = 33.3
	right_margin: float = 35.1
	top_margin: float = 28.8
	bottom_margin: float = 28.8


# -------------------------
# Inline Markup Defaults
# -------------------------

@dataclass
class InlineMarkupDefaults:
	link_color: str = "#0000EE"
	link_underline: bool = True
	link_tag_template: str = '<a href="{url}" color="#0000EE">{text}</a>'


# -------------------------
# Paragraph Style Config
# -------------------------

@dataclass
class ParagraphConfig:
	font_name: str
	font_size: float
	leading: float
	space_before: float = 0
	space_after: float = 0
	left_indent: float = 0
	right_indent: float = 0
	first_line_indent: float = 0
	alignment: int = TA_LEFT
	keep_with_next: bool = False
	bullet_indent: Optional[float] = None
	bullet_font_name: Optional[str] = None
	bullet_font_size: Optional[float] = None


# -------------------------
# Non-Paragraph Flowables
# -------------------------

@dataclass
class HRConfig:
	thickness: float = 1.0
	width: str = "100%"
	space_before: float = 0
	space_after: float = 15.45


@dataclass
class SpacerConfig:
	height: float = 7.76


# -------------------------
# Master Theme
# -------------------------

@dataclass
class ResumeTheme:
	doc: DocumentDefaults = field(default_factory=DocumentDefaults)
	inline: InlineMarkupDefaults = field(default_factory=InlineMarkupDefaults)

	normal: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		font_name="Helvetica",
		font_size=7.2,
		leading=9.0
	))

	h2: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		font_name="Helvetica-Bold",
		font_size=12.6,
		leading=15.45,
		space_after=3.0,
		keep_with_next=True
	))

	bullet: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		font_name="Helvetica",
		font_size=7.2,
		leading=9.0,
		left_indent=24.01,
		bullet_indent=12.0,
		bullet_font_name="Helvetica",
		bullet_font_size=7.2
	))

	section_rule: HRConfig = field(default_factory=HRConfig)
	section_spacer: SpacerConfig = field(default_factory=SpacerConfig)