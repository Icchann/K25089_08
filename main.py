from flask import Flask, request, render_template
import random  # ランダムデータ作成のためのライブラリ

app = Flask(__name__)

# じゃんけんの有効な手と、接待モード時にCPUが出す負け手の対応表
JANKEN_HANDS = ("rock", "scissor", "paper")
LOSING_CPU_HAND_BY_PLAYER_HAND = {
    "rock": "scissor",
    "scissor": "paper",
    "paper": "rock",
}
DEFAULT_PORT = 8888


# 1. プロジェクトのトップ（じゃんけんアプリや、課題のアプリへのリンクを配置するだけ）
@app.route('/')
def index():
    return render_template('index.html')


# 2. じゃんけんアプリの入力フォーム
@app.route('/janken')
def janken():
    # じゃんけんの入力画面のテンプレートを呼び出し
    return render_template('janken_form.html')


# 3. じゃんけんデータ送信先とじゃんけん結果表示画面
@app.route('/janken/play', methods=["POST"])
def janken_play():

    # <input type="text" id="your_name" name="name">
    name = (request.form.get("name") or "").strip()
    if not name:
        name = "名無しさん"

    # <input type="radio" id="hand_rock" value="rock" name="hand">
    # <input type="radio" id="hand_scissor" value="scissor" name="hand">
    # <input type="radio" id="hand_paper" value="paper" name="hand">
    hand = request.form.get("hand", None)

    # <input type="checkbox" id="is_settai" name="is_settai" value="on">
    is_settai = bool(request.form.get("is_settai"))

    if is_settai:
        # 接待モード時は後出し（未選択）であってもグーが出ていることにしてCPUが必ず負ける
        if hand not in LOSING_CPU_HAND_BY_PLAYER_HAND:
            hand = "rock"
        cpu = LOSING_CPU_HAND_BY_PLAYER_HAND[hand]
    else:
        # リストの中からランダムに選ぶ
        cpu = random.choice(list(JANKEN_HANDS))

    # じゃんけん処理
    if hand == cpu:
        result_message = "あいこ"
    else:
        if hand == "rock":
            if cpu == "scissor":
                result_message = "{}の勝ち".format(name)
            else:
                result_message = "{}の負け".format(name)
        elif hand == "scissor":
            if cpu == "paper":
                result_message = "{}の勝ち".format(name)
            else:
                result_message = "{}の負け".format(name)
        elif hand == "paper":
            if cpu == "rock":
                result_message = "{}の勝ち".format(name)
            else:
                result_message = "{}の負け".format(name)
        else:
            result_message = "後出しはダメです。"

    # 渡したいデータを先に定義しておいてもいいし、テンプレートを先に作っておいても良い
    return render_template('janken_play.html',
                           result_message=result_message,
                           name=name,
                           hand=hand,
                           cpu=cpu)


if __name__ == '__main__':
    # portは適宜書き換えてください
    app.run(host="0.0.0.0", port=DEFAULT_PORT, debug=True)
