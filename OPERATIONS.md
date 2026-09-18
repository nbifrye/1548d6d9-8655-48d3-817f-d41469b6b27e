# Blog Operations

このリポジトリは、デジタルアイデンティティおよびアクセスコントロールに関する標準仕様を、一次資料に基づいて日本語で整理するために運営します。

## Editorial source policy

記事本文に記載する技術的事実は、原則として標準化団体・仕様策定主体が公開する一次資料で確認します。

対象となる一次資料の例:

- IETF / RFC Editor の RFC、BCP、Internet-Draft、IANA registry
- OpenID Foundation の Final Specification、Implementer's Draft、Working Group 文書
- W3C Recommendation、Candidate Recommendation、Working Draft
- OASIS の標準仕様
- ISO/IEC 等について、公開された公式情報を参照できる場合はその一次資料

二次資料、ベンダーブログ、ニュース記事、個人ブログは、記事本文の技術的事実を確定する根拠として使用しません。

## No-opinion policy

記事には筆者独自の推奨、評価、見解、予測を記載しません。

- 「〜した方がよい」「〜が安全である」「〜が重要である」といった独自判断を追加しない。
- 仕様が MUST / SHOULD / RECOMMENDED 等で要求・推奨している場合のみ、その規範語と出典節を明記して記載する。
- 仕様が選択を deployment / local policy / implementation-specific としている場合、そのまま記載し、一方を推奨しない。
- threat、security property、limitation は、一次資料に記載された範囲で説明する。
- ベンダー固有の実装挙動を標準仕様の事実として一般化しない。

## Article structure

各記事は、対象仕様に応じて次の要素を含めます。

1. 文書名、発行主体、ステータス、発行日
2. 仕様の scope と他仕様との関係
3. terminology / actors
4. protocol または processing model
5. Mermaid による概要フロー
6. request / response または data structure
7. normative requirements
8. validation / error processing
9. security / privacy consideration（仕様に存在する場合）
10. version differences（仕様に明記されている場合）
11. 一次資料へのリンク
12. 参照した主要 section
13. 最終確認日

記事の長さを目的化しませんが、処理手順や規範要件を省略して概要だけで終わらせません。

## Mermaid policy

Protocol、ceremony、resource lifecycle、request / response の順序が存在する記事には Mermaid 図を含めます。

図は仕様本文の処理順序を要約するものであり、仕様に存在しない actor、message、security property を追加しません。図だけで規範要件を表現せず、本文でも該当要件と一次資料の section を記載します。

## Japanese style guide

- 英語の仕様用語は、無理に不自然な日本語へ置き換えない。
- 初出では必要に応じて日本語説明と原語を併記する。
- 主語を明確にし、Authorization Server / Client / Resource Server 等の主体を省略しない。
- 「〜になります」の多用を避け、仕様記述は「〜である」「〜を定義する」「〜を要求する」を基本とする。
- 同一記事内で表記を統一する。
- 原文にない因果関係を補わない。
- RFC の規範語は日本語だけに置換せず、MUST / SHOULD / MAY 等を併記する。

## Weekly editorial loop

1. 一次資料の新規発行・更新を確認する。
2. 文書の status、date、supersedes / updates 関係を確認する。
3. 既存記事との重複と更新要否を確認する。
4. 一次資料の scope、normative section、security/privacy consideration を読み込む。
5. Mermaid の処理フローを仕様本文に沿って作成する。
6. 日本語本文を作成し、すべての技術的主張が一次資料に紐付くことを確認する。
7. 規範語の強度を原文と照合する。
8. 参照した主要 section と最終確認日を付ける。
9. 既存記事に誤りや古い記述があれば同時に修正する。
10. main へ反映する。

## Publication quality gate

公開前に以下を確認します。

- 技術的事実の根拠が一次資料である。
- 文書 status と date が確認されている。
- Draft を Final / RFC / Recommendation と誤認させる表現がない。
- MUST / MUST NOT / SHOULD / SHOULD NOT / MAY の強度が変わっていない。
- 独自の推奨・評価・見解が含まれていない。
- Mermaid 図と本文の処理順序が一致している。
- actor と token / code / assertion / credential / resource の用語が混同されていない。
- 仕様にない security property を断定していない。
- 日本語として不自然な直訳が残っていない。
- 一次資料へのリンク、主要 section、最終確認日がある。

## Update policy

仕様の status、normative requirement、security consideration、processing rule が更新された場合、既存記事を再確認して修正します。旧版との差分を扱う場合は、仕様自身の revision history、changes section、または公式 change log に記載された事実のみを使用します。
