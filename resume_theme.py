from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

# -------------------------
# Document Defaults
# -------------------------

@dataclass
class DocumentDefaults:
	"""Page-level PDF layout settings (margins and paper size), not markdown-specific."""
	pagesize: tuple = A4
	leftMargin: float = 30
	rightMargin: float = 30
	topMargin: float = 30
	bottomMargin: float = 30


# -------------------------
# Inline Markup Defaults
# -------------------------

@dataclass
class InlineMarkupDefaults:
	"""Inline markdown styling defaults, mainly for links like [text](url)."""
	link_color: str = "#0000EE"
	link_underline: bool = True
	link_tag_template: str = '<a href="{url}" color="#0000EE">{text}</a>'


# -------------------------
# Paragraph Style Config
# -------------------------

@dataclass
class ParagraphConfig:
	"""Generic paragraph style used by markdown block types (section, paragraph, bullet text)."""
	fontName: str  # Typeface used for this markdown block (e.g., paragraph, h2, bullet text).
	fontSize: float = 10.0 # Text size for the block content.
	leading: float = 12.0  # Line spacing within the same markdown block.
	spaceBefore: float = 2.0  # Vertical space inserted before this block.
	spaceAfter: float = 2.0  # Vertical space inserted after this block.
	leftIndent: float = 0.0  # Left indentation for the whole block.
	rightIndent: float = 0.0  # Right indentation for the whole block.
	firstLineIndent: float = 0.0  # Extra indent only on the first line of the block.
	alignment: int = TA_LEFT  # Text alignment (left/center/right/justify) for the block.
	keepWithNext: bool = False  # Keeps this block on the same page as the next block (useful for headings).
	bulletIndent: Optional[float] = None  # Bullet marker offset for markdown list items.
	bulletFontName: Optional[str] = None  # Font used for bullet marker glyphs.
	bulletFontSize: Optional[float] = None  # Size used for bullet marker glyphs.


# -------------------------
# Non-Paragraph Flowables
# -------------------------

@dataclass
class HRConfig:
	"""Horizontal rule style for markdown `hr` lines and section divider lines."""
	thickness: float = 1.0
	width: str = "100%"
	color: str = "#969696"
	spaceBefore: float = 0.0
	spaceAfter: float = 4.5


@dataclass
class SpacerConfig:
	"""Vertical gap inserted between rendered markdown blocks."""
	height: float = 6.2


# -------------------------
# Master Theme
# -------------------------

@dataclass
class ResumeTheme:
	"""Top-level theme object that maps markdown blocks to PDF styles."""
	doc: DocumentDefaults = field(default_factory=DocumentDefaults)
	inline: InlineMarkupDefaults = field(default_factory=InlineMarkupDefaults)

	# Markdown `paragraph` blocks.
	normal: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		fontName="Helvetica",
		fontSize=10
	))

	# Markdown `section` heading text.
	h2: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		fontName="Helvetica-Bold",
		fontSize=12,
		leading=12,
		spaceBefore=12,
		keepWithNext=True
	))

	# Markdown `###` heading text (same style as `section`, but no divider line).
	h3: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		fontName="Helvetica-Bold",
		fontSize=12,
		spaceBefore=0,
		spaceAfter=3,
		keepWithNext=True
	))

	# Markdown `bullet` list item text.
	bullet: ParagraphConfig = field(default_factory=lambda: ParagraphConfig(
		fontName="Helvetica",
		fontSize=10,
		spaceBefore=2.5,
		spaceAfter=0,
		leftIndent=6,
		bulletIndent=4,
		bulletFontName="Helvetica",
		bulletFontSize=12
	))

	# Markdown `hr` style, also used as divider after `section` headings.
	section_rule: HRConfig = field(default_factory=HRConfig)
	# Extra spacing between grouped markdown blocks (for example after bullet lists).
	section_spacer: SpacerConfig = field(default_factory=SpacerConfig)
