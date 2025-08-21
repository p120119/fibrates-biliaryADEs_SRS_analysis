# data/README

このフォルダには**生データ**（配布不可）と、解析のための**中間生成物**の配置規約をまとめます。  
本リポジトリはデータを同梱しません（FAERS/JADER は各規約に従って取得してください）。

## 目的と対象
- **対象データセット**：FAERS、JADER（自発報告データ）
- **目的**：フィブラート（ペマ／フェノ／ベザ）と**胆道系有害事象**（PT14）に関する不均衡解析・層別解析・TTO・EBGM の再現

## ディレクトリ構成
```
data/
├─ raw/        # 取得直後のファイル（無加工・非追跡）
└─ parsed/     # 文字コード変換・列名統一・CSV化など前処理後のファイル（追跡可）
```
- 追跡可否は `.gitignore` に従います。`raw/` は**Gitに含めません**。

## 取得方法（概要）
- **FAERS**：FDAサイトから四半期ごとの DEMO/DRUG/REAC/OUTC/INDI/THER 等を入手（原典はTSV/固定長/ZIP）。
- **JADER**：PMDAサイトから CSV を入手。

> 本プロジェクトでは**UTF-8（BOMなし）・カンマ区切りCSV**に正規化して `parsed/` に配置します。

## 形式・文字コードの正規化
- 文字コードは **UTF-8** に統一（JADERはShift_JIS系のことがあるため変換推奨）。
- 改行は LF（\n）。
- 区切りはカンマ、ヘッダ行を1行目に持つ**ワイド型CSV**。
- 日付は `YYYY-MM-DD` に統一（未知は空欄）。

## ファイル命名規約（推奨）
```
data/parsed/
  faers_DEMO.csv
  faers_DRUG.csv
  faers_REAC.csv
  faers_OUTC.csv      # 任意
  faers_INDI.csv      # 任意
  jader_DEMO.csv
  jader_DRUG.csv
  jader_REAC.csv
  jader_HIST.csv      # 任意
```
- 任意テーブルは解析に直接必須ではありませんが、PLID作成や補助に用いることがあります。

## 最低限必要なカラム（本パイプラインで参照する項目）

### JADER
- **DEMO**：`識別番号`, `年齢`, `体重`, `身長`, `性別`（性別は '男性'/'女性' など）
- **DRUG**：`識別番号`, `医薬品（一般名）`, `医薬品連番`, `投与開始日`
- **REAC**：`識別番号`, `有害事象`, `有害事象発現日`

### FAERS
- **DEMO**：`caseid`, `caseversion`, `primaryid`, `age`, `age_cod`, `sex`, `wt`, `wt_cod`
- **DRUG**：`primaryid`, `drug_seq`, `prod_ai`, `start_dt`
- **REAC**：`primaryid`, `pt`, `event_dt`

> **ID統一**：上流で `case_id` を作成（JADER: 識別番号 / FAERS: primaryid）。  
> **薬剤名統一**：`drug_of_interest` 列を用意（`node_003` で表記ゆれ正規化）。

## サブグループ定義（層別）
- **性別**：`Male` / `Female` に正規化（JADER: '男性'→'Male' 等）。
- **年齢帯**：JADERでは「`○○歳代の○○`」等から **正規表現 `([0-9]{2})歳代`** で**十代数値だけ抽出**→  
  - `20–50s`（20,30,40,50）, `60s+`（60 以上）
- **BMI**：`BMI = 体重(kg) / (身長(m))^2`。`node_001` で **体重/身長に+5** の補正後、少数2桁で算出。  
  - BMI のカット：`<25` / `>=25`。

## イベント定義（胆道系）
- **PTリスト（14語）**：`sql/00_conventions.md` の `biliary_pt_list` を**実リスト**に差し替えてください（現在はプレースホルダ）。
- JADERは `有害事象`、FAERSは `pt` 列で一致判定（大文字小文字・全半角差は正規化推奨）。

## 事前前処理の推奨
1. 文字コード変換（Shift_JIS → UTF-8）
2. 列名の統一と**ASCII化**（必要に応じて別名列を追加：`case_id`, `drug_of_interest` など）
3. 日付列の正規化（`YYYY-MM-DD`）と不正値の空欄化
4. FAERS `DEMO` の**デデュープ**：`caseid` ごとに **max(caseversion)** を残す（→ `primaryid` を以降のキーに）
5. 欠損/非数値の明確化（例：年齢は十代抽出、体重/身長は数値抽出+5）

## 整合性チェック（抜粋）
- **キー整合**：`DEMO`, `DRUG`, `REAC` で `case_id` が結合可能か。NULLはないか。
- **一意性**：FAERS `DEMO` は `caseid` 単位で1件に正規化されているか。
- **件数サニティ**：`DRUG` の `drug_seq` 最大値や件数分布が極端でないか。
- **TTO準備**：`投与開始日`/`start_dt` と `有害事象発現日`/`event_dt` の双方が有効な行が十分にあるか。
- **サブグループ空欄**：層別の分母に含める前に NULL を除外できているか。

## 既知の落とし穴
- **ID取り違え**：FAERS は `primaryid`、JADER は `識別番号`。最初に `case_id` に統一してください。
- **FAERSを `caseid` でJOIN**：バージョン違いが混入します。**`primaryid`** を使用。
- **文字化け/全角半角**：UTF-8統一と正規化辞書で回避。
- **負のTTO**：`event < start` は除外（`node_006` で制約可能）。

## 例：ミニマムCSV（ダミー）
```
data/parsed/jader_DRUG.csv
識別番号,医薬品（一般名）,医薬品連番,投与開始日
J001,ペマフィブラート,1,2021-04-01
J001,ベザフィブラート,2,2021-04-10

data/parsed/jader_REAC.csv
識別番号,有害事象,有害事象発現日
J001,胆嚢炎,2021-04-12
```
この2枚だけでも、`node_006`（最初の有効ペア抽出）とTTO変換のテストが可能です。

## 参考：このリポから使うノード
- `scripts/node_002_drug_counts_unified.py`：`num_drugs` と `case_id` を生成（JADER/FAERS両対応）
- `scripts/node_003_normalize_drug_names_simple.py`：`drug_of_interest` 正規化
- `scripts/node_004_metrics.py`：2×2 指標
- `scripts/node_005_ebgm.py`：EBGM（決定化済）
- `scripts/node_006_tto_earliest_pair.py`：最初の有効 `(start,event)` ペア
- `scripts/node_007_faers_demo_dedup.py`：FAERS DEMO のデデュープ

## 免責・配布
- 本リポは**データを配布しません**。FAERS/JADERのライセンスや規約に従ってください。
- プライバシーに配慮し、個人情報・機微な識別子は含めないでください。

