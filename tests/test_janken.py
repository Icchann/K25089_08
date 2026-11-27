from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class JankenAppTestCase(unittest.TestCase):
    """じゃんけんアプリのルーティング・通常モード・接待モードを検証するテスト。"""

    def setUp(self):
        main.app.config["TESTING"] = True
        self.client = main.app.test_client()

    def test_index_and_janken_form_pages(self):
        """トップページとじゃんけん入力画面に接待モードチェックボックスが存在することを確認する。"""
        index_res = self.client.get("/")
        self.assertEqual(index_res.status_code, 200)
        self.assertIn("/janken", index_res.get_data(as_text=True))

        form_res = self.client.get("/janken")
        self.assertEqual(form_res.status_code, 200)
        form_html = form_res.get_data(as_text=True)
        self.assertIn('id="is_settai"', form_html)
        self.assertIn('name="is_settai"', form_html)

    def test_normal_mode_late_hand_and_default_name(self):
        """通常モードで手未選択・名前空白のみの場合、『名無しさん』かつ『後出しはダメです。』になることを確認する。"""
        res = self.client.post("/janken/play", data={"name": "   "})
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("名無しさん", html)
        self.assertIn("後出しはダメです。", html)
        self.assertIn("mark_batsu.png", html)

    def test_normal_mode_win_lose_draw(self):
        """通常モードで乱数を固定し、勝ち・負け・あいこの判定が正しいことを確認する。"""
        with patch("main.random.choice", return_value="scissor"):
            win_res = self.client.post("/janken/play", data={"name": "太郎", "hand": "rock"})
            self.assertIn("太郎の勝ち", win_res.get_data(as_text=True))

            draw_res = self.client.post("/janken/play", data={"name": "太郎", "hand": "scissor"})
            self.assertIn("あいこ", draw_res.get_data(as_text=True))

            lose_res = self.client.post("/janken/play", data={"name": "太郎", "hand": "paper"})
            self.assertIn("太郎の負け", lose_res.get_data(as_text=True))

    def test_settai_mode_always_wins_for_each_hand(self):
        """接待モードONのとき、グー・チョキ・パーいずれを出してもCPUが負ける手を出しプレイヤーが勝つことを確認する。"""
        expected_cpu_img = {
            "rock": "janken_choki.png",
            "scissor": "janken_pa.png",
            "paper": "janken_gu.png",
        }
        for hand, cpu_img in expected_cpu_img.items():
            res = self.client.post(
                "/janken/play",
                data={"name": "花子", "hand": hand, "is_settai": "on"},
            )
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("花子の勝ち", html)
            self.assertIn(cpu_img, html)

    def test_settai_mode_late_hand_defaults_to_rock_and_wins(self):
        """接待モードONかつ手未選択（後出し）のとき、グーが出た扱いになりCPUがチョキを出して勝つことを確認する。"""
        res = self.client.post(
            "/janken/play",
            data={"name": "社長", "is_settai": "on"},
        )
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("社長の勝ち", html)
        self.assertIn("janken_gu.png", html)
        self.assertIn("janken_choki.png", html)
        self.assertNotIn("mark_batsu.png", html)

    def test_win_message_is_red_only_when_player_wins(self):
        """プレイヤーが勝った場合のみ結果メッセージの h2 タグが赤文字になり、それ以外では赤文字にならないことを確認する。"""
        with patch("main.random.choice", return_value="scissor"):
            win_html = self.client.post("/janken/play", data={"name": "太郎", "hand": "rock"}).get_data(as_text=True)
            self.assertIn('<h2 style="color: red;">太郎の勝ち</h2>', win_html)

            draw_html = self.client.post("/janken/play", data={"name": "太郎", "hand": "scissor"}).get_data(as_text=True)
            self.assertIn("<h2>あいこ</h2>", draw_html)
            self.assertNotIn('style="color: red;"', draw_html)

            lose_html = self.client.post("/janken/play", data={"name": "太郎", "hand": "paper"}).get_data(as_text=True)
            self.assertIn("<h2>太郎の負け</h2>", lose_html)
            self.assertNotIn('style="color: red;"', lose_html)

        late_html = self.client.post("/janken/play", data={"name": "太郎"}).get_data(as_text=True)
        self.assertIn("<h2>後出しはダメです。</h2>", late_html)
        self.assertNotIn('style="color: red;"', late_html)


if __name__ == "__main__":
    unittest.main()
