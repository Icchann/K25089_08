from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class UranaiAppTestCase(unittest.TestCase):
    """占いアプリの計算アルゴリズム・バリデーション・HTTPエンドポイントを検証するテスト。"""

    def setUp(self):
        main.app.config["TESTING"] = True
        self.client = main.app.test_client()

    def test_handout_calculation_example(self):
        """講義資料の具体例（現在日付 20261116、生年月日 2005-04-01、名前『愛工太郎』）で結果が 5 になることを確認する。"""
        result = main.evaluate_uranai(
            name_raw="愛工太郎",
            birthday_raw="2005-04-01",
            today_int=20261116,
        )
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["rank"], 5)
        self.assertEqual(result["message"], main.URANAI_MESSAGES_BY_RANK[5])

    def test_all_five_ranks_are_reachable_by_changing_inputs(self):
        """生年月日または名前が変わると mod 5 の全インデックス（0〜4）に対応して 5, 1, 3, 2, 4 が返ることを確認する。"""
        # today_int = 20261127, name = "A" (1文字) のとき diff = 20261127 - birth_int
        expected_by_birth = {
            "2026-11-27": 5,  # diff=0 -> 0%5=0 -> 5
            "2026-11-26": 1,  # diff=1 -> 1%5=1 -> 1
            "2026-11-25": 3,  # diff=2 -> 2%5=2 -> 3
            "2026-11-24": 2,  # diff=3 -> 3%5=3 -> 2
            "2026-11-23": 4,  # diff=4 -> 4%5=4 -> 4
        }
        for birthday_str, expected_rank in expected_by_birth.items():
            result = main.evaluate_uranai(
                name_raw="A",
                birthday_raw=birthday_str,
                today_int=20261127,
            )
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["rank"], expected_rank)
            self.assertEqual(result["message"], main.URANAI_MESSAGES_BY_RANK[expected_rank])

    def test_invalid_inputs_return_rank_1_and_error_message(self):
        """生年月日未入力・日付変換不可・名前未入力（空白のみ含む）のとき結果1と指定エラーメッセージになることを確認する。"""
        invalid_cases = [
            {"name": "愛工太郎", "birthday": ""},
            {"name": "愛工太郎", "birthday": None},
            {"name": "愛工太郎", "birthday": "invalid-date"},
            {"name": "愛工太郎", "birthday": "2026-02-30"},
            {"name": "愛工太郎", "birthday": "2026/04/01"},
            {"name": "愛工太郎", "birthday": "205-4-1"},
            {"name": "", "birthday": "2005-04-01"},
            {"name": "   ", "birthday": "2005-04-01"},
            {"name": None, "birthday": "2005-04-01"},
            {"name": "", "birthday": ""},
        ]
        for case in invalid_cases:
            with self.subTest(case=case):
                result = main.evaluate_uranai(
                    name_raw=case["name"],
                    birthday_raw=case["birthday"],
                    today_int=20261116,
                )
                self.assertFalse(result["is_valid"])
                self.assertEqual(result["rank"], 1)
                self.assertEqual(result["message"], "入力不備で占えませんでした")

    def test_uranai_http_endpoints(self):
        """GET /uranai および POST /uranai/play が正常に応答することを確認する。"""
        form_res = self.client.get("/uranai")
        self.assertEqual(form_res.status_code, 200)
        form_html = form_res.get_data(as_text=True)
        self.assertIn('action="/uranai/play"', form_html)
        self.assertIn("占う", form_html)

        valid_res = self.client.post(
            "/uranai/play",
            data={"name": "愛工太郎", "birthday": "2005-04-01"},
        )
        self.assertEqual(valid_res.status_code, 200)
        valid_html = valid_res.get_data(as_text=True)
        self.assertIn("愛工太郎", valid_html)
        self.assertIn("2005-04-01", valid_html)

        invalid_res = self.client.post(
            "/uranai/play",
            data={"name": "", "birthday": "not-a-date"},
        )
        self.assertEqual(invalid_res.status_code, 200)
        invalid_html = invalid_res.get_data(as_text=True)
        self.assertIn("入力不備で占えませんでした", invalid_html)
        self.assertIn('<strong class="rank_number">1</strong>', invalid_html)


if __name__ == "__main__":
    unittest.main()
