from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from resume_generator.generator import generate_resume
from resume_generator.models import EducationEntry, ResumeData, SkillEntry


class GeneratorTests(unittest.TestCase):
    def test_generates_png_and_single_page_a4_pdf(self) -> None:
        data = ResumeData(
            name="张三",
            job_target="产品经理 / UI 设计师",
            city="上海",
            work_years="5 年",
            availability="一周内",
            birth_date="1998.06",
            political_status="群众",
            highest_education="本科",
            current_address="上海市浦东新区",
            educations=[
                EducationEntry(
                    school="示例大学",
                    date_range="2018.09 - 2022.06",
                    major="信息管理 / 本科",
                    details="主修数据分析、产品设计、项目管理。",
                ),
                EducationEntry(
                    school="开放大学",
                    date_range="2024.03 - 2026.06",
                    major="数字媒体 / 硕士",
                    details="研究方向为交互体验与可用性测试。",
                ),
            ],
            skills=[
                SkillEntry(name="需求分析", level="熟练", score=92),
                SkillEntry(name="产品设计", level="熟练", score=85),
                SkillEntry(name="数据分析", level="掌握", score=78),
                SkillEntry(name="项目管理", level="了解", score=68),
            ],
            skill_tags=["Axure", "Figma", "SQL", "英语 CET-6"],
            phone="13812345678",
            email="zhangsan@example.com",
            portfolio="https://example.com",
            contact_address="上海市浦东新区",
            evaluation="工作认真严谨，沟通表达清晰，具备良好的团队协作意识与持续学习能力。",
            copyright_year="2026",
        )

        with tempfile.TemporaryDirectory() as directory:
            generated = generate_resume(data, directory, "张三-个人简历")

            self.assertTrue(generated.image_path.is_file())
            self.assertTrue(generated.pdf_path.is_file())
            self.assertGreater(generated.image_path.stat().st_size, 100_000)
            self.assertGreater(generated.pdf_path.stat().st_size, 50_000)

            with Image.open(generated.image_path) as image:
                self.assertEqual(image.size, (2480, 3508))
                dpi = image.info.get("dpi")
                self.assertIsNotNone(dpi)
                self.assertAlmostEqual(dpi[0], 300, places=2)
                self.assertAlmostEqual(dpi[1], 300, places=2)

            reader = PdfReader(str(generated.pdf_path))
            self.assertEqual(len(reader.pages), 1)
            page_width = float(reader.pages[0].mediabox.width)
            page_height = float(reader.pages[0].mediabox.height)
            self.assertAlmostEqual(page_width, 595.2756, places=2)
            self.assertAlmostEqual(page_height, 841.8898, places=2)


if __name__ == "__main__":
    unittest.main()
