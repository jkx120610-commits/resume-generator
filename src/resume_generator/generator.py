from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

from .models import EducationEntry, GeneratedFiles, ResumeData, SkillEntry


class ResumeLayoutError(RuntimeError):
    """Raised when resume content cannot fit on one A4 page."""


class FontResolver:
    def __init__(self) -> None:
        windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        candidates = (
            (windows_fonts / "msyh.ttc", windows_fonts / "msyhbd.ttc"),
            (windows_fonts / "simhei.ttf", windows_fonts / "simhei.ttf"),
            (
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            ),
            (
                Path("/System/Library/Fonts/PingFang.ttc"),
                Path("/System/Library/Fonts/PingFang.ttc"),
            ),
        )

        for regular, bold in candidates:
            if regular.is_file():
                self.regular_path = regular
                self.bold_path = bold if bold.is_file() else regular
                return

        raise ResumeLayoutError("未找到可用的中文字体，请安装微软雅黑、黑体或思源黑体。")

    def regular(self, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(self.regular_path), size=size)

    def bold(self, size: int) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(self.bold_path), size=size)


class ResumeRenderer:
    WIDTH = 1240
    HEIGHT = 1754
    SCALE = 2
    MARGIN = 76
    CONTENT_X = 300
    CONTENT_WIDTH = 864

    BLUE = "#246BDE"
    BLUE_DEEP = "#174DA8"
    BLUE_SOFT = "#EDF4FF"
    INK = "#172033"
    INK_SOFT = "#526078"
    MUTED = "#7B879B"
    LINE = "#DFE6F1"
    LINE_STRONG = "#B9C9E2"
    WHITE = "#FFFFFF"
    PAGE_BG = "#FFFFFF"

    def __init__(self, data: ResumeData) -> None:
        self.data = data
        self.fonts = FontResolver()
        self.image = Image.new(
            "RGB",
            (self.WIDTH * self.SCALE, self.HEIGHT * self.SCALE),
            self.PAGE_BG,
        )
        self.draw = ImageDraw.Draw(self.image)

    def _s(self, value: float) -> int:
        return round(value * self.SCALE)

    def _font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        return self.fonts.bold(self._s(size)) if bold else self.fonts.regular(self._s(size))

    def _text(
        self,
        xy: tuple[float, float],
        text: str,
        size: int,
        fill: str,
        *,
        bold: bool = False,
        anchor: str = "la",
        stroke_width: int = 0,
    ) -> None:
        self.draw.text(
            (self._s(xy[0]), self._s(xy[1])),
            text,
            font=self._font(size, bold),
            fill=fill,
            anchor=anchor,
            stroke_width=stroke_width,
        )

    def _line(
        self,
        points: Iterable[tuple[float, float]],
        fill: str,
        width: int = 1,
    ) -> None:
        scaled = [(self._s(x), self._s(y)) for x, y in points]
        self.draw.line(scaled, fill=fill, width=self._s(width), joint="curve")

    def _rounded_rect(
        self,
        box: tuple[float, float, float, float],
        radius: float,
        fill: str | None = None,
        outline: str | None = None,
        width: int = 1,
    ) -> None:
        scaled = tuple(self._s(value) for value in box)
        self.draw.rounded_rectangle(
            scaled,
            radius=self._s(radius),
            fill=fill,
            outline=outline,
            width=self._s(width),
        )

    def _ellipse(
        self,
        box: tuple[float, float, float, float],
        fill: str | None = None,
        outline: str | None = None,
        width: int = 1,
    ) -> None:
        scaled = tuple(self._s(value) for value in box)
        self.draw.ellipse(scaled, fill=fill, outline=outline, width=self._s(width))

    def _wrap(self, text: str, font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
        clean = " ".join(text.replace("\r", "").split())
        if not clean:
            return []

        lines: list[str] = []
        current = ""
        max_width_px = self._s(max_width)

        for character in clean:
            candidate = current + character
            width = self.draw.textlength(candidate, font=font)
            if current and width > max_width_px:
                lines.append(current.rstrip())
                current = character.lstrip()
            else:
                current = candidate

        if current:
            lines.append(current.rstrip())
        return lines

    def _draw_wrapped_text(
        self,
        x: float,
        y: float,
        text: str,
        size: int,
        fill: str,
        max_width: float,
        *,
        bold: bool = False,
        line_height: float | None = None,
        max_lines: int | None = None,
    ) -> float:
        font = self._font(size, bold)
        lines = self._wrap(text, font, max_width)
        if not lines:
            return y

        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            last = lines[-1]
            while last and self.draw.textlength(last + "…", font=font) > self._s(max_width):
                last = last[:-1]
            lines[-1] = last + "…"

        spacing = line_height or size * 1.55
        for index, line in enumerate(lines):
            self._text((x, y + index * spacing), line, size, fill, bold=bold)
        return y + len(lines) * spacing

    def _draw_divider(self, y: float, *, strong: bool = False) -> None:
        self._line(
            [(self.MARGIN, y), (self.WIDTH - self.MARGIN, y)],
            self.LINE_STRONG if strong else self.LINE,
            width=1,
        )

    def _draw_header(self) -> None:
        avatar_x, avatar_y, avatar_size = self.MARGIN, 70, 156
        self._draw_avatar(avatar_x, avatar_y, avatar_size)

        name_x = 270
        self._text((name_x, 72), "CURRICULUM VITAE", 13, self.BLUE, bold=True)
        self._text((name_x, 102), self.data.name[:24], 42, self.INK, bold=True)
        self._text((name_x, 168), "求职意向：", 17, self.INK_SOFT, bold=True)
        target_width = self.WIDTH - self.MARGIN - (name_x + 98)
        target_font = self._font(17, True)
        target_text = self.data.job_target[:40]
        if self.draw.textlength(target_text, font=target_font) > self._s(target_width):
            target_text = self._truncate(target_text, target_font, target_width)
        self._text((name_x + 98, 168), target_text, 17, self.BLUE_DEEP, bold=True)

        tags = [
            self.data.city.strip() or "所在城市",
            self.data.work_years.strip() or "工作年限",
            self.data.availability.strip() or "到岗时间",
        ]
        tag_x = name_x
        tag_y = 207
        for value in tags:
            font = self._font(12, True)
            width = self.draw.textlength(value, font=font) / self.SCALE + 24
            if tag_x + width > self.WIDTH - self.MARGIN:
                break
            self._rounded_rect(
                (tag_x, tag_y, tag_x + width, tag_y + 32),
                16,
                fill="#FBFCFE",
                outline=self.LINE,
                width=1,
            )
            self._text(
                (tag_x + width / 2, tag_y + 8),
                value,
                12,
                self.INK_SOFT,
                bold=True,
                anchor="ma",
            )
            tag_x += width + 10

        self._draw_divider(286, strong=True)

    def _truncate(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: float,
    ) -> str:
        current = text
        while current and self.draw.textlength(current + "…", font=font) > self._s(max_width):
            current = current[:-1]
        return current + "…"

    def _draw_avatar(self, x: float, y: float, size: float) -> None:
        center_x = x + size / 2
        center_y = y + size / 2
        radius = size / 2
        self._ellipse(
            (x, y, x + size, y + size),
            fill=self.BLUE_SOFT,
            outline="#BDD2F3",
            width=2,
        )

        if self.data.photo_path and Path(self.data.photo_path).is_file():
            photo = Image.open(self.data.photo_path).convert("RGB")
            photo = ImageOps.fit(
                photo,
                (self._s(size), self._s(size)),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            mask = Image.new("L", (self._s(size), self._s(size)), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, self._s(size), self._s(size)), fill=255)
            self.image.paste(photo, (self._s(x), self._s(y)), mask)
        else:
            self._ellipse(
                (center_x - 22, center_y - 43, center_x + 22, center_y + 1),
                outline=self.BLUE,
                width=4,
            )
            self.draw.arc(
                (
                    self._s(center_x - 46),
                    self._s(center_y + 3),
                    self._s(center_x + 46),
                    self._s(center_y + 75),
                ),
                200,
                340,
                fill=self.BLUE,
                width=self._s(4),
            )

        self._ellipse(
            (x + size - 31, y + size - 33, x + size - 9, y + size - 11),
            fill=self.BLUE,
            outline=self.WHITE,
            width=5,
        )

    def _draw_section_heading(
        self,
        y: float,
        index: str,
        title: str,
        subtitle: str,
    ) -> None:
        self._rounded_rect(
            (self.MARGIN, y, self.MARGIN + 31, y + 31),
            8,
            fill=self.BLUE,
        )
        self._text(
            (self.MARGIN + 15.5, y + 5),
            index,
            11,
            self.WHITE,
            bold=True,
            anchor="ma",
        )
        self._text((self.MARGIN + 43, y - 1), title, 18, self.INK, bold=True)
        self._text((self.MARGIN + 43, y + 30), subtitle, 11.5, self.MUTED)

    def _draw_basic_info(self) -> float:
        y = 325
        self._draw_section_heading(y, "01", "基本信息", "个人概况")
        items = [
            ("出生年月", self.data.birth_date or "请填写"),
            ("政治面貌", self.data.political_status or "请填写"),
            ("最高学历", self.data.highest_education or "请填写"),
            ("现居地址", self.data.current_address or "请填写"),
        ]
        start_y = y + 4
        row_gap = 58
        column_width = self.CONTENT_WIDTH / 2
        for index, (label, value) in enumerate(items):
            column = index % 2
            row = index // 2
            x = self.CONTENT_X + column * column_width
            item_y = start_y + row * row_gap
            self._text((x, item_y), label, 11.5, self.MUTED, bold=True)
            self._text((x, item_y + 21), value, 14.5, self.INK, bold=True)
        self._draw_divider(y + 135)
        return y + 174

    def _draw_education(self, y: float) -> float:
        self._draw_section_heading(y, "02", "教育背景", "学历与经历")
        entries = [entry for entry in self.data.educations[:2] if entry.school.strip()]
        entry_y = y - 1
        for index, education in enumerate(entries):
            bullet_x = self.CONTENT_X
            self._ellipse(
                (bullet_x, entry_y + 6, bullet_x + 11, entry_y + 17),
                fill=self.WHITE,
                outline=self.BLUE,
                width=2,
            )
            if index < len(entries) - 1:
                self._line(
                    [(bullet_x + 5.5, entry_y + 24), (bullet_x + 5.5, entry_y + 110)],
                    "#CFDBED",
                    width=1,
                )

            content_x = self.CONTENT_X + 27
            self._text(
                (content_x, entry_y),
                education.school[:50],
                16,
                self.INK,
                bold=True,
            )
            date_text = education.date_range[:40]
            date_font = self._font(11.5, True)
            self._text(
                (self.WIDTH - self.MARGIN, entry_y + 3),
                date_text,
                11.5,
                self.BLUE_DEEP,
                bold=True,
                anchor="ra",
            )
            major = education.major or "专业 / 学历"
            self._text((content_x, entry_y + 29), major[:50], 13, self.INK_SOFT, bold=True)
            details = education.details or "课程、荣誉奖项或校园经历"
            self._draw_wrapped_text(
                content_x,
                entry_y + 53,
                details,
                12,
                self.MUTED,
                self.CONTENT_WIDTH - 27,
                line_height=18,
                max_lines=2,
            )
            entry_y += 105

        section_height = max(128, len(entries) * 105 + 20)
        divider_y = y + section_height
        self._draw_divider(divider_y)
        return divider_y + 39

    def _draw_skills(self, y: float) -> float:
        self._draw_section_heading(y, "03", "技能特长", "能力与工具")
        skills = [skill for skill in self.data.skills[:4] if skill.name.strip()]
        cell_width = self.CONTENT_WIDTH / 2
        row_height = 48
        for index, skill in enumerate(skills):
            column = index % 2
            row = index // 2
            x = self.CONTENT_X + column * cell_width
            item_y = y + row * row_height
            self._text((x, item_y), skill.name[:24], 14, self.INK, bold=True)
            level_text = skill.level or "熟练"
            self._text(
                (x + cell_width - 24, item_y + 2),
                level_text[:12],
                10.5,
                self.MUTED,
                bold=True,
                anchor="ra",
            )
            track_y = item_y + 27
            track_width = cell_width - 46
            self._rounded_rect(
                (x, track_y, x + track_width, track_y + 5),
                3,
                fill="#E8EEF7",
            )
            fill_width = track_width * max(0, min(100, skill.score)) / 100
            if fill_width > 0:
                self._rounded_rect(
                    (x, track_y, x + fill_width, track_y + 5),
                    3,
                    fill=self.BLUE,
                )

        tags_y = y + max(2, math.ceil(len(skills) / 2)) * row_height + 12
        self._line(
            [(self.CONTENT_X, tags_y - 10), (self.WIDTH - self.MARGIN, tags_y - 10)],
            "#EDF1F7",
            width=1,
        )
        self._draw_tags(self.data.skill_tags, self.CONTENT_X, tags_y)

        divider_y = tags_y + 58
        self._draw_divider(divider_y)
        return divider_y + 39

    def _draw_tags(self, tags: list[str], x: float, y: float) -> None:
        current_x = x
        for index, tag in enumerate(tags[:8]):
            label = tag.strip()
            if not label:
                continue
            font = self._font(11.5, True)
            width = self.draw.textlength(label[:24], font=font) / self.SCALE + 22
            if current_x + width > self.WIDTH - self.MARGIN:
                break
            self._rounded_rect(
                (current_x, y, current_x + width, y + 31),
                7,
                fill=self.BLUE_SOFT,
                outline="#CFE0FA",
                width=1,
            )
            self._text(
                (current_x + width / 2, y + 7),
                label[:24],
                11.5,
                self.BLUE_DEEP,
                bold=True,
                anchor="ma",
            )
            current_x += width + 9
            if index == len(tags) - 1:
                break

    def _draw_contact(self, y: float) -> None:
        self._draw_section_heading(y, "04", "联系方式", "联系与评价")
        items = [
            ("phone", "手机号码", self.data.phone or "请填写手机号码"),
            ("mail", "电子邮箱", self.data.email or "请填写电子邮箱"),
            ("globe", "个人网站 / 作品集", self.data.portfolio or "请填写作品集链接"),
            ("pin", "通讯地址", self.data.contact_address or "请填写通讯地址"),
        ]
        column_width = self.CONTENT_WIDTH / 2
        for index, (icon, label, value) in enumerate(items):
            column = index % 2
            row = index // 2
            x = self.CONTENT_X + column * column_width
            item_y = y + row * 59
            self._rounded_rect(
                (x, item_y, x + 37, item_y + 37),
                9,
                fill="#F6F9FF",
                outline="#D8E5F8",
                width=1,
            )
            self._draw_contact_icon(icon, x + 10, item_y + 10)
            self._text((x + 50, item_y - 1), label, 10.5, self.MUTED, bold=True)
            max_value_width = column_width - 64
            font = self._font(13, True)
            shown_value = value[:80]
            if self.draw.textlength(shown_value, font=font) > self._s(max_value_width):
                shown_value = self._truncate(shown_value, font, max_value_width)
            self._text((x + 50, item_y + 17), shown_value, 13, self.INK, bold=True)

        evaluation_y = y + 132
        self.draw.rounded_rectangle(
            (
                self._s(self.CONTENT_X),
                self._s(evaluation_y),
                self._s(self.WIDTH - self.MARGIN),
                self._s(evaluation_y + 118),
            ),
            radius=self._s(2),
            fill="#F7FAFF",
        )
        self.draw.rectangle(
            (
                self._s(self.CONTENT_X),
                self._s(evaluation_y),
                self._s(self.CONTENT_X + 4),
                self._s(evaluation_y + 118),
            ),
            fill=self.BLUE,
        )
        self._text(
            (self.CONTENT_X + 24, evaluation_y + 17),
            "他人评价 / 自荐语",
            11.5,
            self.BLUE_DEEP,
            bold=True,
        )
        self._draw_wrapped_text(
            self.CONTENT_X + 24,
            evaluation_y + 43,
            self.data.evaluation or "请填写评价内容。",
            12.5,
            self.INK_SOFT,
            self.CONTENT_WIDTH - 48,
            line_height=19,
            max_lines=3,
        )

        self._draw_divider(evaluation_y + 150, strong=True)
        self._draw_footer(evaluation_y + 176)

    def _draw_contact_icon(self, icon: str, x: float, y: float) -> None:
        if icon == "phone":
            self._line(
                [
                    (x + 3, y + 3),
                    (x + 7, y + 3),
                    (x + 9, y + 7),
                    (x + 6, y + 11),
                    (x + 12, y + 17),
                    (x + 16, y + 14),
                    (x + 20, y + 16),
                    (x + 20, y + 20),
                    (x + 15, y + 21),
                    (x + 4, y + 10),
                    (x + 3, y + 3),
                ],
                self.BLUE,
                width=2,
            )
        elif icon == "mail":
            self._rounded_rect((x + 1, y + 4, x + 21, y + 19), 2, outline=self.BLUE, width=2)
            self._line([(x + 2, y + 5), (x + 11, y + 13), (x + 20, y + 5)], self.BLUE, width=2)
        elif icon == "globe":
            self._ellipse((x + 1, y + 1, x + 21, y + 21), outline=self.BLUE, width=2)
            self._line([(x + 1, y + 11), (x + 21, y + 11)], self.BLUE, width=2)
            self._line([(x + 11, y + 1), (x + 7, y + 11), (x + 11, y + 21)], self.BLUE, width=2)
            self._line([(x + 11, y + 1), (x + 15, y + 11), (x + 11, y + 21)], self.BLUE, width=2)
        else:
            self._ellipse((x + 3, y + 1, x + 19, y + 17), outline=self.BLUE, width=2)
            self._ellipse((x + 9, y + 7, x + 13, y + 11), fill=self.BLUE)
            self._line([(x + 6, y + 15), (x + 11, y + 21), (x + 16, y + 15)], self.BLUE, width=2)

    def _draw_footer(self, y: float) -> None:
        year = self.data.copyright_year.strip() or "2026"
        name = self.data.name.strip() or "你的姓名"
        self._text(
            (self.MARGIN, y),
            f"© {year} {name}. All rights reserved.",
            10.5,
            self.MUTED,
        )
        self._text(
            (self.WIDTH - self.MARGIN, y),
            "保持真诚，持续成长。",
            10.5,
            self.INK_SOFT,
            bold=True,
            anchor="ra",
        )

    def render(self) -> Image.Image:
        self._draw_header()
        next_y = self._draw_basic_info()
        next_y = self._draw_education(next_y)
        next_y = self._draw_skills(next_y)
        self._draw_contact(next_y)
        return self.image


def _safe_stem(value: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip().rstrip(".")
    return stem or "resume"


def generate_resume(
    data: ResumeData,
    output_dir: str | Path,
    filename: str | None = None,
) -> GeneratedFiles:
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(filename or f"{data.name or 'resume'}-个人简历")
    image_path = output_path / f"{stem}.png"
    pdf_path = output_path / f"{stem}.pdf"

    renderer = ResumeRenderer(data)
    image = renderer.render()
    image.save(image_path, "PNG", optimize=True, dpi=(300, 300))

    pdf = pdf_canvas.Canvas(str(pdf_path), pagesize=A4, pageCompression=1)
    page_width, page_height = A4
    pdf.drawImage(
        ImageReader(image),
        0,
        0,
        width=page_width,
        height=page_height,
        preserveAspectRatio=False,
        mask="auto",
    )
    pdf.showPage()
    pdf.save()

    return GeneratedFiles(image_path=image_path, pdf_path=pdf_path)
