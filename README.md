# 信長真戦シミュレーター Ver3.9 All Adjusted

## 内容
- Ver3.7更新データ反映版をベース
- 合戦開始ログへ整理
- 1ターン〜8ターン表記へ変更
- 指揮/受動/兵種戦法は合戦開始に発動
- 能動戦法は行動時に発動判定
- 兵種戦法は兵種一致時のみ発動
- 大太刀/三河弓/赤備え/甲斐弓系を開戦時付与へ整理
- 罵詈雑言のような非ダメージ突撃をダメージ扱いしない補助
- 古今独歩系の多重判定確認用
- DEBUG：所持戦法確認を追加

## URLを変えずに更新する場合
今Streamlitで指定している `shinsen_sim_github_ver35/app.py` の中身を、
このZIP内の `app.py` / `data` / `requirements.txt` で上書きしてください。

## GitHub新規で使う場合
Main file path:
```text
shinsen_sim_github_ver39_all_adjusted/app.py
```
