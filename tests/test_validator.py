from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from resume_generator.models import EducationEntry, ResumeData, SkillEntry
from resume_generator.validator import validate_resume


def valid_data() -> ResumeData:
    return ResumeData(
        name="张三",
        job_target="产品经理",
        educations=[
            EducationEntry(
                school="示例大学",
                date_range="2018.09 - 2022.06",
                major="信息管理 / 本科",
                details="校级奖学金，负责学生会活动策划。",
            )
        ],
        skills=[SkillEntry(name="需求分析", level="熟练", score=90)],
        phone="13812345678",
        email="zhangsan@example.com",
        evaluation="工作认真，沟通清晰，具备良好的团队协作能力。",
    )


class ValidatorTests(unittest.TestCase):
    def test_valid_data_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_resume(valid_data(), Path(directory) / "output")
        self.assertTrue(result.is_valid, result.errors)

    def test_required_fields_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_resume(ResumeData(), directory)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("姓名" in error for error in result.errors))
        self.assertTrue(any("求职意向" in error for error in result.errors))
        self.assertTrue(any("教育经历" in error for error in result.errors))

    def test_invalid_email_and_phone_are_reported(self) -> None:
        data = valid_data()
        data.email = "invalid-email"
        data.phone = "abc"
        with tempfile.TemporaryDirectory() as directory:
            result = validate_resume(data, directory)
        self.assertTrue(any("邮箱格式" in error for error in result.errors))
        self.assertTrue(any("手机号码格式" in error for error in result.errors))

    def test_invalid_skill_score_is_reported(self) -> None:
        data = valid_data()
        data.skills[0].score = 101
        with tempfile.TemporaryDirectory() as directory:
            result = validate_resume(data, directory)
        self.assertTrue(any("0 到 100" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
