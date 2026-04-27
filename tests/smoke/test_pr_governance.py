from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_pull_request_template.py"


def _valid_pr_body() -> str:
    return textwrap.dedent(
        """
        ## Summary

        - 收口 PR 治理门禁

        ## Applicable Rules

        - 当前执行入口: `docs/roadmap.md`
        - 架构护栏 / canonical owner: `docs/ARCHITECTURE_GUARDRAILS.md` + `.github/workflows/ci.yml`
        - 模块不变量: PR 描述必须显式列出适用规则、验证结果和残留风险
        - 兼容性约束: 不改变 CLI 或项目协议，只增加治理门禁
        - 额外 ADR / plan / 测试基线: `tests.smoke.test_pr_governance`

        ## Review Checklist

        - [x] 已按适用规则自审，而不是只按抽象风格偏好评价
        - [x] 未越过 canonical owner 或禁止的依赖方向
        - [x] 未引入未说明的 breaking change / behavior change
        - [x] 未新增重复规则定义、平行配置或平行真相源
        - [x] 测试结果已记录
        - [x] 文档已同步，或已明确说明无需同步

        ## Validation

        - 运行命令: `python -m unittest tests.smoke.test_pr_governance`
        - 结果: 通过
        - 未验证区域: 未在 GitHub 远端实际跑 CI

        ## Risks

        - 残留风险: 无
        - 需要 reviewer 重点关注: 规则是否过严
        """
    ).strip()


class PullRequestGovernanceScriptTests(unittest.TestCase):
    def _run_script(self, body: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
            handle.write(body)
            temp_path = Path(handle.name)
        try:
            return subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--body-file", str(temp_path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    def test_accepts_complete_pull_request_body(self) -> None:
        result = self._run_script(_valid_pr_body())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("passed", result.stdout.lower())

    def test_rejects_empty_applicable_rule_field(self) -> None:
        body = _valid_pr_body().replace(
            "- 当前执行入口: `docs/roadmap.md`",
            "- 当前执行入口:",
        )
        result = self._run_script(body)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Applicable Rules: field `当前执行入口` is empty or placeholder", result.stderr)

    def test_rejects_unchecked_checklist_item(self) -> None:
        body = _valid_pr_body().replace(
            "- [x] 测试结果已记录",
            "- [ ] 测试结果已记录",
        )
        result = self._run_script(body)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Review Checklist: contains unchecked items", result.stderr)
