---
layout: post
title: "SCIM 2.0 の filter 式：属性比較・論理演算・複合属性の評価規則"
date: 2026-09-23 01:38:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** SCIM の検索条件を生成する Client、または filter を評価する Service Provider の実装者  
**この記事で伝えること:** RFC 7644 の `filter` 式について、配置、構文、比較演算子、論理演算子、評価順序、multi-valued / complex attribute の評価規則を確認する  
**扱わないこと:** sorting、pagination、attribute projection、PATCH の `path` filter、認証・認可、RFC 9865 の cursor-based pagination

## Article brief

- **Reader:** SCIM Client / Service Provider の実装者。
- **Question:** `filter` はどこに置き、どの構文と評価規則で resource を絞り込むのか。
- **Answer:** `filter` の query parameter と POST SearchRequest での配置、RFC 7644 §3.4.2.2 の ABNF、演算子、優先順位、multi-valued / complex attribute の評価方法を区別して説明できる。
- **Scope:** RFC 7644 §3.4.2.2 と、POST query での `filter` の配置を確認するための §3.4.3。文字列比較の `caseExact` について RFC 7643 §2.2 を参照する。
- **Out of scope:** sorting、pagination、`attributes` / `excludedAttributes`、PATCH path、実装独自の追加演算子、認証・認可。
- **Primary sources:** RFC 7644 §3.4.2.2, §3.4.3、RFC 7643 §2.2。
- **Diagram:** `filter` 受信から構文確認、式評価、matching resource の返却までを示す `flowchart TD`。

## 1. `filter` は resource の部分集合を要求するための parameter

RFC 7644 §3.4.2.2 では、filtering は SCIM Service Provider にとって **OPTIONAL** です。Client は `/ServiceProviderConfig` の `filter` attribute により、Service Provider の filter capability を確認できます。

Client は `filter` query parameter に filter expression を指定できます（**MAY**）。`filter` が指定された場合、Service Provider は expression に一致する resource だけを返します（**SHALL**）。

次は非規範的な例です。値 `alice` は説明用の illustrative value です。

```http
GET /Users?filter=userName%20eq%20%22alice%22 HTTP/1.1
Host: example.com
Accept: application/scim+json
```

配置は URL の query parameter です。RFC 7644 の例は可読性のため URL encoding を省略していますが、同 RFC §1.2 は URL を RFC 3986 §2.1 に従って percent-encode することを実装者に **MUST** としています。

## 2. POST query では `filter` は JSON member になる

RFC 7644 §3.4.3 は、valid SCIM endpoint の末尾に `/.search` を付けた HTTP POST を query operation として定義しています。この request body では `filter` は OPTIONAL な JSON member であり、存在する場合は §3.4.2.2 の valid filter expression でなければなりません（**MUST**）。

次は非規範的な最小例です。

```http
POST /Users/.search HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:SearchRequest"
  ],
  "filter": "userName eq \"alice\""
}
```

ここでは `filter` は query parameter ではなく、`SearchRequest` JSON object の member です。

## 3. filter expression の基本形

RFC 7644 §3.4.2.2 では、`filter` parameter は少なくとも1つの valid expression を含まなければなりません（**MUST**）。各 expression は attribute name、attribute operator、必要に応じた value から構成されます。

同節の ABNF では、attribute comparison の基本形を次のように定義しています。

```text
attrExp = (attrPath SP "pr") /
          (attrPath SP compareOp SP compValue)
```

`compValue` は JSON の `false`、`null`、`true`、number、string に基づきます。`attrPath` は schema URI を含めることができ、complex attribute の sub-attribute は `name.givenName` のような standard attribute notation で指定します。

**A SCIM filter is an expression language, not an arbitrary server-side search syntax.**  
（SCIM filter は式言語であり、任意のサーバー独自検索構文ではありません。）

## 4. attribute operator

RFC 7644 §3.4.2.2 Table 3 は次の comparison operator を定義しています。

- `eq`: equal。
- `ne`: not equal。
- `co`: attribute value が operator value 全体を substring として含む。
- `sw`: attribute value が operator value で始まる。
- `ew`: attribute value が operator value で終わる。
- `pr`: attribute に non-empty / non-null value が存在する。complex attribute では non-empty node を含む場合に match する。
- `gt`, `ge`, `lt`, `le`: 大小比較。String は lexicographical、DateTime は chronological、Integer は numeric value で比較する。

`gt` / `ge` / `lt` / `le` を Boolean または Binary attribute に適用した場合、Service Provider は HTTP 400 と `scimType` `invalidFilter` で失敗させます（**SHALL**）。

String attribute の比較で case-sensitive かどうかは、RFC 7643 §2.2 の `caseExact` characteristic によって決定します（RFC 7644 §3.4.2.2、**SHALL**）。一方、filter 内の attribute name と operator 自体は case-insensitive です。

## 5. 複数の expression と評価順序

複数の expression は `and` / `or` で結合でき（**MAY**）、`not` で expression を反転できます。丸括弧 `()` により boolean expression を grouping することもできます（**MAY**）。

RFC 7644 §3.4.2.2 は filter の評価順序を次の順に **MUST** としています。

1. grouping operator
2. logical operator（`not`、`and`、`or` の順）
3. attribute operator

次は非規範的な例です。

```text
userType eq "Employee" and (title pr or active eq true)
```

この例の値は説明用です。特定の user type や title を要求するものではありません。

## 6. multi-valued attribute と complex attribute

指定した attribute が multi-valued の場合、その値のいずれか1つが criterion に一致すれば、その resource は filter に一致します。

complex attribute の sub-attribute を直接比較する場合は、standard attribute notation を使います。たとえば `name.givenName` です。

RFC 7644 §3.4.2.2 は square brackets `[]` による valuePath も定義しています。Service Provider は complex attribute filter をサポートできます（**MAY**）。その場合、角括弧内の expression は、直前の parent attribute の**同じ1つの値**に対して適用されなければなりません（**MUST**）。角括弧内も valid filter expression でなければなりません（**MUST**）。

次は RFC 7644 の構造に沿った非規範的な例です。

```text
emails[type eq "work" and value co "@example.com"]
```

この式では `type eq "work"` と `value co "@example.com"` が、`emails` の同じ要素に対して成立するかを評価します。

## 7. Service Provider が filter を評価する流れ

<pre class="mermaid">
flowchart TD
    A[filter を受信] --> B{valid expression?}
    B -->|No| C[400 invalidFilter]
    B -->|Yes| D[優先順位に従って評価]
    D --> E[multi-valued / complex rule を適用]
    E --> F[一致する resource のみ返す]
</pre>

Service Provider が指定された filter operation を認識しない場合、filtering を拒否し、HTTP 400 と `scimType` `invalidFilter` を返さなければなりません（**MUST**、RFC 7644 §3.4.2.2）。Service Provider は追加の filter operation をサポートできます（**MAY**）。

## 8. このテーマで区別する事項

`filter` は resource の集合を条件で絞り込むための expression です。本記事では、結果順を決める `sortBy` / `sortOrder`、結果をページ分割する `startIndex` / `count`、返却 attribute を制御する `attributes` / `excludedAttributes` は扱いません。

また、PATCH operation の `path` でも value selection に filter と共通する構文要素が現れますが、PATCH path の評価は RFC 7644 §3.5.2 の更新処理に属するため、本記事の範囲外です。

## 9. 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)

参照した主要節: RFC 7644 §1.2, §3.4.2.2, §3.4.3 / RFC 7643 §2.2  
最終確認: 2026-09-23
