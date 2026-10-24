"""
utils/validator.py
==================
金额逻辑校验工具 —— 双校验策略：
  校验 1: 不含税金额合计 + 税额合计 ≈ 价税合计（0.02 元容差）
  校验 2: 明细表行金额求和 ≈ 不含税合计（补充交叉验证）

异常提示必须带定位引导：
  "疑似价税合计行定位错误，请核对票面最下方「价税合计」栏金额"

注意：由于 OCR 识别可能存在小数精度问题，使用 0.02 容差做近似比较。
"""

from dataclasses import dataclass
from typing import Optional, List


TOLERANCE = 0.02  # 允许的误差范围（元）


@dataclass
class ValidationResult:
    passed: bool
    message: str


# 异常定位引导语 —— 必须出现在所有 false 分支的 message 里
_LOCATION_HINT = "疑似价税合计行定位错误，请核对票面最下方「价税合计」栏金额"


def validate_amount(
    amount: float,
    tax: float,
    total_amount: float,
    detail_amounts: Optional[List[float]] = None,
) -> ValidationResult:
    """
    双校验金额逻辑。

    参数:
        amount:         不含税金额（合计）
        tax:            税额（合计）
        total_amount:    价税合计（含税总额）
        detail_amounts:  可选 —— 明细各行不含税金额列表（用于校验 2）
    返回:
        ValidationResult(passed=True/False, message="...")
    """
    # ===== 空值/全零 =====
    if total_amount == 0 and amount == 0 and tax == 0:
        return ValidationResult(
            passed=True,
            message="识别结果均为 0，可能是识别失败，建议人工核对"
        )

    # ===== 校验 1: amount + tax ≈ total_amount =====
    expected_total = round(amount + tax, 2)
    actual_total = round(total_amount, 2)
    diff = abs(expected_total - actual_total)

    if diff > TOLERANCE:
        # 主校验失败 —— 拼定位引导
        lines = [
            f"金额逻辑异常！",
            f"不含税金额 {amount:.2f} + 税额 {tax:.2f} = {expected_total:.2f}，",
            f"但识别的价税合计为 {actual_total:.2f}（差异 {diff:.2f} 元）。",
            _LOCATION_HINT,
        ]
        # 如果明细表校验能帮上忙，追加提示
        if detail_amounts:
            detail_sum = round(sum(detail_amounts), 2)
            if abs(detail_sum - amount) > TOLERANCE:
                lines.append(f"另：明细行金额合计 {detail_sum:.2f} 与不含税合计 {amount:.2f} 也存在差异，请核对明细表格底部「合计」行。")
        return ValidationResult(passed=False, message="\n".join(lines))

    # 主校验通过
    message = f"金额逻辑正确：{amount:.2f} + {tax:.2f} = {expected_total:.2f}（价税合计 {actual_total:.2f}）"

    # ===== 校验 2（可选）: 明细表行求和 ≈ amount =====
    if detail_amounts:
        detail_sum = round(sum(detail_amounts), 2)
        diff2 = abs(detail_sum - round(amount, 2))
        if diff2 > TOLERANCE:
            return ValidationResult(
                passed=False,
                message=(
                    f"价税合计校验通过（{amount:.2f} + {tax:.2f} = {expected_total:.2f}），"
                    f"但明细行金额合计 {detail_sum:.2f} 与不含税合计 {amount:.2f} 不符（差异 {diff2:.2f} 元），"
                    f"请核对明细表格底部「合计」行金额是否为不含税金额合计。"
                ),
            )

    return ValidationResult(passed=True, message=message)
