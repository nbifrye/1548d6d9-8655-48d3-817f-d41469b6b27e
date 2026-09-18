# Blog Operations

このリポジトリは、デジタルアイデンティティおよびアクセスコントロールに関する標準仕様を、一次資料に基づいて日本語で整理するために運営します。

## Editorial source policy

記事本文に記載する技術的事実は、標準化団体・仕様策定主体が公開する一次資料で確認します。

対象となる一次資料の例:

- IETF / RFC Editor の RFC、BCP、Internet-Draft、IANA registry
- OpenID Foundation の Final Specification、Implementer's Draft、Working Group 文書
- W3C Recommendation、Candidate Recommendation、Working Draft
- OASIS の標準仕様
- ISO/IEC 等について公開された公式情報

二次資料、ベンダーブログ、ニュース記事、個人ブログは、標準仕様上の技術的事実を確定する根拠として使用しません。

## One article, one theme

記事は「仕様書1冊を順番に要約する」ことを目的にしません。執筆前に、誰に何を伝える記事なのかを1文で定義します。

各記事には冒頭に次の4項目を明記します。

- **記事タイプ**
- **対象読者**
- **この記事で伝えること**
- **扱わないこと**

「この記事で伝えること」は1つの中心テーマに限定します。本文に含める内容は、そのテーマを理解するために必要な情報に限ります。

### Article types

原則として、次のいずれか1つを選びます。

| Article type | 目的 |
|---|---|
| Overview | 仕様または機能群の全体像と構成要素の関係を理解してもらう |
| Flow | protocol / ceremony / lifecycle の処理順序を理解してもらう |
| Requirement | 特定の適合要件・規範要件を実装者向けに整理する |
| Security Practice | 標準仕様が規定する特定の攻撃対策・Best Current Practice を整理する |
| Feature Deep Dive | extension、token、endpoint、data structure など1要素を詳しく扱う |
| Version Difference | 旧版と新版の差分を、公式 change log / revision history に基づいて整理する |

複数の article type を併記する場合でも、中心テーマは1つにします。

## Article brief

記事本文を書く前に、次の brief を内部的に確定します。

1. **Reader:** 誰が読む記事か
2. **Question:** 読者がこの記事で解決したい疑問は何か
3. **Answer:** 読了後に理解できることは何か
4. **Scope:** どこまで扱うか
5. **Out of scope:** 何を別記事へ分離するか
6. **Primary sources:** どの一次資料・section を根拠にするか
7. **Diagram:** どの処理または関係を Mermaid で図示するか

本文の section がこの brief の Question / Answer に直接寄与しない場合、その section は削除するか別記事に分離します。

## No-opinion policy

記事には筆者独自の推奨、評価、見解、予測を記載しません。

- 「〜した方がよい」「〜が安全である」「〜が重要である」といった独自判断を追加しない。
- 仕様が MUST / SHOULD / RECOMMENDED 等で要求・推奨している場合のみ、その規範語と出典 section を明記して記載する。
- 仕様が deployment / local policy / implementation-specific の判断に委ねている場合、その事実のみを記載し、一方を推奨しない。
- threat、security property、limitation は、一次資料に記載された範囲で説明する。
- ベンダー固有の実装挙動を標準仕様の事実として一般化しない。

## Article structure

記事タイプに応じて構成を変えます。すべての記事を同じ目次にしません。

### Overview

- この記事について
- 対象仕様と scope
- 構成要素と関係
- 全体フローまたは概念図
- 読者が全体像を理解するために必要な主要要素
- out-of-scope の明示
- 一次資料

### Flow

- この記事について
- actors / prerequisites
- Mermaid sequence diagram
- 処理を順番に説明
- 各段階の validation / error processing
- out-of-scope の明示
- 一次資料

### Requirement / Security Practice

- この記事について
- 対象となる threat / requirement の scope
- 基本フロー
- 規範要件
- 要件が適用される主体
- validation / rejection conditions
- out-of-scope の明示
- 一次資料

### Feature Deep Dive

- この記事について
- feature の役割
- data structure / protocol position
- processing rules
- normative requirements
- error / edge cases
- out-of-scope の明示
- 一次資料

## Concrete protocol examples

Protocol parameter、JSON object、JWT claim、HTTP header、request body、response body、data structure を扱う記事では、仕様本文で形式が定義されている場合、読者が配置と構造を確認できる具体例を含めます。

- parameter が query、form body、JSON member、HTTP header のどこに置かれるかを明記する。
- JSON object や token claim set を扱う場合、記事テーマに必要な範囲で最小の構造例を示す。
- request / response を扱う場合、HTTP method、Content-Type、主要 parameter の配置が分かる例を示す。
- 例は **非規範的な例** と明記し、仕様上の MUST / SHOULD / MAY と混同させない。
- 一次資料で定義されていない field、actor、security property を例のために追加しない。
- 値そのものに規範的意味がない場合は illustrative value であることが分かる値を使用する。
- field の型や cardinality が理解に必要な場合は、表ではなく短い箇条書きで説明する。
- 大きな object は記事テーマに必要な member だけを示し、省略した member が存在する場合はその旨を記載する。

## Responsive content policy

記事はスマートフォン表示で横スクロールを必要としない構成にします。

### Tables

表は、項目同士を同じ軸で比較する必要がある場合に限って使用します。

- 原則として2列程度の小さな比較に限定する。
- 行数が多い、説明文が長い、3列以上になる、コードや URI を多く含む場合は、表を使わず見出し付き箇条書きや番号付きリストへ分解する。
- 表を使用する場合も、スマートフォンでは1行をカード状に縦積みして表示し、横スクロールを発生させない。
- 情報密度を下げずに表を分解できる場合は、表より文章構造を優先する。

## Mermaid policy

Protocol、ceremony、resource lifecycle、request / response の順序や構成要素間の関係がある記事には Mermaid 図を含めます。

図は記事テーマに直接関係する情報だけを表示します。仕様本文に存在しない actor、message、security property は追加しません。図だけで規範要件を表現せず、本文でも該当要件と一次資料の section を記載します。

スマートフォンでは Mermaid 図を画面幅内に収め、横スクロールを発生させません。横方向に要素が増える図は、`flowchart TD` の縦方向レイアウトを優先するか、複数の小さな図へ分割します。sequence diagram は participant 数と message label の長さを抑え、1枚で読みづらくなる場合は処理段階ごとに分割します。

## Japanese style guide

- 英語の仕様用語は、無理に不自然な日本語へ置き換えない。
- 初出では必要に応じて日本語説明と原語を併記する。
- 主語を明確にし、Authorization Server / Client / Resource Server 等の主体を省略しない。
- 「〜になります」の多用を避け、仕様記述は「〜である」「〜を定義する」「〜を要求する」を基本とする。
- 同一記事内で表記を統一する。
- 原文にない因果関係を補わない。
- RFC の規範語は日本語だけに置換せず、MUST / SHOULD / MAY 等を併記する。
- section ごとに主題を1つにし、別論点への脱線を避ける。

## Editorial loop

1. 一次資料の新規発行・更新を確認する。
2. 既存記事の title、Reader、Question、Scope、Primary sources を確認し、同一または実質的に同一のテーマがないことを確認する。
3. 読者と記事テーマを決める。
4. Article brief の Reader / Question / Answer / Scope / Out of scope を確定する。
5. 新しい Article brief を既存記事と再比較し、Reader / Question / Scope が大きく重なる場合は新規記事を作らず、必要なら既存記事を更新する。
6. 文書の status、date、supersedes / updates 関係を確認する。
7. 根拠となる一次資料の section を特定する。
8. Mermaid 図を仕様本文に沿って作成する。
9. 本文を作成し、各 section が記事テーマに必要か確認する。
10. すべての技術的主張が一次資料に紐付くことを確認する。
11. 規範語の強度を原文と照合する。
12. 日本語を校正する。
13. main へ反映する。

## Publication quality gate

公開前に以下を確認します。

- 対象読者が明記されている。
- 「この記事で伝えること」が1つの中心テーマとして明記されている。
- 「扱わないこと」が明記されている。
- 既存記事と Reader / Question / Scope が実質的に重複していない。
- すべての section が中心テーマに直接寄与している。
- 技術的事実の根拠が一次資料である。
- 文書 status と date が確認されている。
- Draft を Final / RFC / Recommendation と誤認させる表現がない。
- MUST / MUST NOT / SHOULD / SHOULD NOT / MAY の強度が変わっていない。
- 独自の推奨・評価・見解が含まれていない。
- Protocol parameter や object structure を扱う記事では、配置・形式が分かる非規範的な具体例がある。
- Mermaid 図と本文の処理順序が一致している。
- スマートフォンで表・図の横スクロールが発生しない構成になっている。
- 大きな表を使わず、必要に応じて箇条書きや複数 section に分解している。
- actor と token / code / assertion / credential / resource の用語が混同されていない。
- 仕様にない security property を断定していない。
- 日本語として不自然な直訳が残っていない。
- 一次資料へのリンク、主要 section、最終確認日がある。

## Update policy

仕様の status、normative requirement、security consideration、processing rule が更新された場合、既存記事を再確認して修正します。

更新時にも既存記事へ無制限に内容を追加しません。新しい論点が現在の記事テーマから外れる場合は、既存記事を肥大化させず別記事として扱います。
