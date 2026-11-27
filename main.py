from datetime import datetime
import random  # ランダムデータ作成のためのライブラリ
from flask import Flask, request, render_template

app = Flask(__name__)

# じゃんけんの有効な手と、接待モード時にCPUが出す負け手の対応表
JANKEN_HANDS = ("rock", "scissor", "paper")
LOSING_CPU_HAND_BY_PLAYER_HAND = {
    "rock": "scissor",
    "scissor": "paper",
    "paper": "rock",
}
DEFAULT_PORT = 8888

# 占いアプリの定数定義
URANAI_RESULTS_TABLE = (5, 1, 3, 2, 4)
URANAI_MAX_RANK = 5
INVALID_INPUT_RANK = 1
INVALID_INPUT_MESSAGE = "入力不備で占えませんでした"
ISO_DATE_LENGTH = 10
PERCENT_MULTIPLIER = 100

URANAI_LABELS_BY_RANK = {
    5: "大吉（レベル 5 / 5）",
    4: "吉（レベル 4 / 5）",
    3: "中吉（レベル 3 / 5）",
    2: "小吉（レベル 2 / 5）",
    1: "末吉（レベル 1 / 5）",
}

URANAI_MESSAGES_BY_RANK = {
    5: "最高の一日になります！直感を信じて新しいことに挑戦すると、大きな成果につながるでしょう。",
    4: "好調な運気です。周囲とのコミュニケーションを大切にすると、思わぬ幸運が舞い込みます。",
    3: "安定した平穏な一日です。いつも通りのペースを守り、着実に目の前の課題を進めましょう。",
    2: "少し注意が必要な日です。焦らず確認を丁寧に行い、忘れ物や連絡ミスに気をつけましょう。",
    1: "今日は無理をせずエネルギーを蓄える日です。早めに休息をとり、心身をリフレッシュしましょう。",
}


def parse_birthday_to_int(birthday_raw: str | None) -> int | None:
    """YYYY-MM-DD 形式の生年月日文字列を検証し、yyyyMMdd 形式の整数に変換する。不正時は None を返す。"""
    if not birthday_raw:
        return None
    cleaned = birthday_raw.strip()
    if len(cleaned) != ISO_DATE_LENGTH:
        return None
    try:
        birth_date = datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError:
        return None
    return int(birth_date.strftime("%Y%m%d"))


def evaluate_uranai(
    name_raw: str | None,
    birthday_raw: str | None,
    today_int: int | None = None,
) -> dict:
    """入力された名前と生年月日から5段階の占い結果とメッセージを含む辞書を返す。"""
    cleaned_name = (name_raw or "").strip()
    birth_int = parse_birthday_to_int(birthday_raw)

    if not cleaned_name or birth_int is None:
        meter_percent = (INVALID_INPUT_RANK * PERCENT_MULTIPLIER) // URANAI_MAX_RANK
        return {
            "is_valid": False,
            "name": cleaned_name or "未入力",
            "birthday": (birthday_raw or "").strip() or "未入力",
            "rank": INVALID_INPUT_RANK,
            "rank_label": "判定不可（レベル 1 / 5）",
            "message": INVALID_INPUT_MESSAGE,
            "meter_percent": meter_percent,
        }

    if today_int is None:
        today_int = int(datetime.now().strftime("%Y%m%d"))

    diff = abs(today_int - birth_int)
    table_index = (diff * len(cleaned_name)) % len(URANAI_RESULTS_TABLE)
    rank = URANAI_RESULTS_TABLE[table_index]
    meter_percent = (rank * PERCENT_MULTIPLIER) // URANAI_MAX_RANK

    return {
        "is_valid": True,
        "name": cleaned_name,
        "birthday": birthday_raw.strip(),
        "rank": rank,
        "rank_label": URANAI_LABELS_BY_RANK[rank],
        "message": URANAI_MESSAGES_BY_RANK[rank],
        "meter_percent": meter_percent,
    }


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
    is_win = False
    if hand == cpu:
        result_message = "あいこ"
    else:
        if hand == "rock":
            if cpu == "scissor":
                result_message = "{}の勝ち".format(name)
                is_win = True
            else:
                result_message = "{}の負け".format(name)
        elif hand == "scissor":
            if cpu == "paper":
                result_message = "{}の勝ち".format(name)
                is_win = True
            else:
                result_message = "{}の負け".format(name)
        elif hand == "paper":
            if cpu == "rock":
                result_message = "{}の勝ち".format(name)
                is_win = True
            else:
                result_message = "{}の負け".format(name)
        else:
            result_message = "後出しはダメです。"

    # 渡したいデータを先に定義しておいてもいいし、テンプレートを先に作っておいても良い
    return render_template('janken_play.html',
                           result_message=result_message,
                           name=name,
                           hand=hand,
                           cpu=cpu,
                           is_win=is_win)


# 4. 占いアプリの入力フォーム
@app.route('/uranai')
def uranai():
    return render_template('uranai_form.html')


# 5. 占いデータ送信先と占い結果表示画面
@app.route('/uranai/play', methods=["POST"])
def uranai_play():
    result = evaluate_uranai(
        name_raw=request.form.get("name"),
        birthday_raw=request.form.get("birthday"),
    )
    return render_template('uranai_play.html', **result)


if __name__ == '__main__':
    # portは適宜書き換えてください
    app.run(host="0.0.0.0", port=DEFAULT_PORT, debug=True)
