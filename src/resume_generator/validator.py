from __future__ import annotations

import re
from pathlib import Path

from .models import ResumeData, ValidationResult


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_length(
    result: ValidationResult,
    label: str,
    value: str,
    maximum: int,
    required: bool = False,
) -> None:
    cleaned = value.strip()
    if required and not cleaned:
        result.errors.append(f"请填写{label}。")
    elif cleaned and len(cleaned) > maximum:
        result.errors.append(f"{label}不能超过 {maximum} 个字符。")


def validate_resume(data: ResumeData, output_dir: str | Path) -> ValidationResult:
    result = ValidationResult()

    _check_length(result, "姓名", data.name, 24, required=True)
    _check_length(result, "求职意向", data.job_target, 40, required=True)
    _check_length(result, "所在城市", data.city, 24)
    _check_length(result, "工作年限", data.work_years, 16)
    _check_length(result, "到岗时间", data.availability, 16)
    _check_length(result, "出生年月", data.birth_date, 24)
    _check_length(result, "政治面貌", data.political_status, 24)
    _check_length(result, "最高学历", data.highest_education, 24)
    _check_length(result, "现居地址", data.current_address, 40)

    populated_education = False
    for index, education in enumerate(data.educations[:2], start=1):
        if any(
            (
                education.school.strip(),
                education.date_range.strip(),
                education.major.strip(),
                education.details.strip(),
            )
        ):
            populated_education = True
        _check_length(result, f"教育经历 {index} 的学校名称", education.school, 50)
        _check_length(result, f"教育经历 {index} 的起止时间", education.date_range, 40)
        _check_length(result, f"教育经历 {index} 的专业学历", education.major, 50)
        _check_length(result, f"教育经历 {index} 的补充说明", education.details, 90)

    if not populated_education:
        result.errors.append("请至少填写一段教育经历。")

    if not data.skills:
        result.errors.append("请至少填写一项技能。")

    for index, skill in enumerate(data.skills[:4], start=1):
        _check_length(result, f"技能 {index} 名称", skill.name, 24)
        _check_length(result, f"技能 {index} 熟练度", skill.level, 12)
        if not 0 <= skill.score <= 100:
            result.errors.append(f"技能 {index} 的评分必须在 0 到 100 之间。")

    if len("，".join(data.skill_tags)) > 100:
        result.errors.append("技能标签总长度不能超过 100 个字符。")

    _check_length(result, "手机号码", data.phone, 30)
    _check_length(result, "电子邮箱", data.email, 80)
    _check_length(result, "作品集链接", data.portfolio, 120)
    _check_length(result, "通讯地址", data.contact_address, 80)
    _check_length(result, "评价内容", data.evaluation, 180)

    if data.email.strip() and not EMAIL_PATTERN.match(data.email.strip()):
        result.errors.append("电子邮箱格式不正确。")

    if data.phone.strip():
        normalized_phone = re.sub(r"[\s\-()+]", "", data.phone)
        if not normalized_phone.isdigit() or len(normalized_phone) < 7:
            result.errors.append("手机号码格式不正确。")

    if data.photo_path.strip():
        photo_path = Path(data.photo_path)
        if not photo_path.is_file():
            result.errors.append("所选头像文件不存在。")
        elif photo_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            result.errors.append("头像仅支持 JPG、PNG、WEBP 或 BMP 格式。")

    output_path = Path(output_dir).expanduser()
    if not str(output_path).strip():
        result.errors.append("请选择输出目录。")
    else:
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except OSError:
            result.errors.append("输出目录无法创建，请重新选择。")

    if not data.phone.strip():
        result.warnings.append("手机号码为空。")
    if not data.email.strip():
        result.warnings.append("电子邮箱为空。")
    if not data.evaluation.strip():
        result.warnings.append("评价内容为空。")

    return result
