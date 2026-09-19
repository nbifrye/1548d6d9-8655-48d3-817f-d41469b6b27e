---
layout: post
title: "RFC 7644：SCIM filter はどう書き、どう評価されるのか"
date: 2026-09-19 16:39:00 +0900
categories: [provisioning, scim]
---

SCIM の `filter` は、検索結果を条件で絞り込むための式です。RFC 7644 §3.4.2.2 は、attribute、比較演算子、論理演算子、grouping を組み合わせる filter expression を定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Client / Service Provider の検索処理を実装・レビューする開発者  
**この記事で伝えること:** `filter` parameter の配置、filter expression の構造、比較・論理演算子、multi-valued attribute の評価、および不正な filter の扱い  
**扱わないこと:** sort、pagination、`attributes` / `excludedAttributes`、PATCH の `path` filter、検索全体の認可ポリシー

## Article brief

- **Reader:** SCIM の resource 検索と filter 評価を実装・レビューする開発者
- **Question:** `filter` は HTTP request のどこに指定し、`userName eq "bjensen"` や `emails[type eq "work"]` はどのように解釈されるのか
- **Answer:** RFC 7644 §3.4.2.2 の filter grammar、operator、precedence、multi-valued attribute の評価規則、invalid filter の処理を区別して説明できる
- **Scope:** RFC 7644 §3.4.2、§3.4.2.1、§3.4.2.2、§3.4.3、§3.12
- **Out of scope:** sort、pagination、返却 attribute の選択、PATCH path、deployment 固有の検索制限
- **Primary sources:** RFC 7644
- **Diagram:** HTTP request の `filter` から expression の評価、matching resource の ListResponse までを縦方向に示す

## 1. `filter` は検索条件を表す

RFC 7644 §3.4.2.2 では filtering は Service Provider にとって OPTIONAL です。Client は `/ServiceProviderConfig` の `filter` attribute から filter capability を確認できます。

Client は `filter` query parameter に filter expression を指定できます（MAY）。`filter` が指定された場合、Service Provider は expression に一致する resource だけを返さなければなりません（SHALL）。

最小の expression は、attribute name、attribute operator、必要に応じた comparison value から構成されます。`filter` parameter は少なくとも1つの valid expression を含まなければなりません（MUST）。

## 2. GET では query parameter に指定する

次は RFC 7644 §3.4.2.2 の形式に沿った非規範的な例です。読みやすさのため percent-encoding 前の形を示しています。RFC 7644 §1.2 は、実際の URL では RFC 3986 §2.1 に従って percent-encode することを MUST としています。

```http
GET /Users?filter=userName eq "bjensen" HTTP/1.1
Host: example.com
Accept: application/scim+json
```

この request では、`filter` は JSON member ではなく URL の query parameter です。filter expression は次の3要素に分けられます。

- **attribute:** `userName`
- **operator:** `eq`
- **comparison value:** `"bjensen"`

RFC 7644 §3.4.2.2 では attribute name と attribute operator は case-insensitive です。そのため、`userName Eq "john"` と `Username eq "john"` は同じ logical value に評価されます。

## 3. comparison operator の意味

RFC 7644 §3.4.2.2 は次の attribute operator を定義しています。

- **`eq`:** attribute value と comparison value が等しい場合に match する。
- **`ne`:** 両者が等しくない場合に match する。
- **`co`:** comparison value 全体が attribute value の substring である場合に match する。
- **`sw`:** attribute value が comparison value で始まる場合に match する。
- **`ew`:** attribute value が comparison value で終わる場合に match する。
- **`pr`:** attribute に non-empty / non-null value がある場合に match する。`pr` は comparison value を取らない。
- **`gt` / `ge` / `lt` / `le`:** greater than / greater than or equal / less than / less than or equal を表す。比較方法は attribute type に依存する。

たとえば DateTime attribute には次のように指定できます。

```text
meta.lastModified gt "2011-05-13T04:42:34Z"
```

RFC 7644 §3.4.2.2 では、`gt`、`ge`、`lt`、`le` を Boolean または Binary attribute に適用した場合、Service Provider は HTTP 400 と `scimType: "invalidFilter"` で失敗させなければなりません（SHALL）。

String attribute の比較で大文字・小文字を区別するかどうかは、その attribute の `caseExact` characteristic に従います（SHALL）。

## 4. `and` / `or` / `not` と評価順序

複数 expression は `and` / `or` で組み合わせることができます（MAY）。`not` は expression の logical value を反転します。

```text
title pr and userType eq "Employee"
```

括弧を使って expression を group 化することもできます（MAY）。RFC 7644 §3.4.2.2 が定める precedence は次の順序です。

1. grouping operator
2. logical operator: `not` → `and` → `or`
3. attribute operator

たとえば次の expression では、括弧内を group として評価します。

```text
userType eq "Employee" and (emails co "example.com" or emails.value co "example.org")
```

## 5. multi-valued complex attribute は `[...]` で同じ要素を評価できる

RFC 7644 §3.4.2.2 では、filter 対象が multi-valued attribute の場合、そのうち1つの value が条件に一致すれば resource 全体が match します。

さらに Service Provider は complex attribute filter をサポートできます（MAY）。角括弧 `[...]` 内の expression は、直前に指定した parent attribute の**同じ value** に対して適用されなければなりません（MUST）。

```text
emails[type eq "work" and value co "@example.com"]
```

この例では、`emails` の1つの complex value について `type eq "work"` と `value co "@example.com"` の両方を評価します。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[filter を指定]
    B --> C[Service Provider]
    C --> D[expression を評価]
    D --> E{resource が match?}
    E -->|Yes| F[ListResponse に含める]
    E -->|No| G[結果から除外]
</pre>

## 6. POST `/.search` では JSON member に指定する

RFC 7644 §3.4.3 は、query parameter を URL に渡さず HTTP POST で検索する方法も定義しています。Client は valid SCIM endpoint に `/.search` を付け、`application/scim+json` の request body を送ります。

次は非規範的な最小例です。

```http
POST /Users/.search HTTP/1.1
Host: example.com
Accept: application/scim+json
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:SearchRequest"
  ],
  "filter": "userName eq \"bjensen\""
}
```

この形式では `filter` は URL query parameter ではなく SearchRequest JSON object の top-level member です。`filter` member は OPTIONAL ですが、指定する文字列は valid filter expression でなければなりません（MUST, §3.4.3）。

つまり同じ filter expression を使う場合でも、GET と POST では配置が異なります。

- **GET query:** URL の `filter` query parameter
- **POST query:** SearchRequest JSON object の `filter` member

## 7. 検索結果は ListResponse で返る

RFC 7644 §3.4.2 では query response を `urn:ietf:params:scim:api:messages:2.0:ListResponse` で識別しなければなりません（MUST）。次は構造を示すための非規範的な例です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:ListResponse"
  ],
  "totalResults": 1,
  "Resources": [
    {
      "id": "user-123",
      "userName": "bjensen"
    }
  ]
}
```

`totalResults` は REQUIRED です。`Resources` は `totalResults` が 0 でない場合に REQUIRED です。match が0件の場合、Service Provider は HTTP 200 を返し、`totalResults` を 0 にしなければなりません（SHALL, §3.4.2）。

## 8. invalid filter は HTTP 400 になる

RFC 7644 §3.4.2.2 では、Service Provider が指定された filter operation を認識しない場合、filtering を拒否し、HTTP 400 と `scimType` が `invalidFilter` の error を返さなければなりません（MUST）。

たとえば RFC 7644 が定義していない `regex` operator を Service Provider が認識しない場合が該当します。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:Error"
  ],
  "scimType": "invalidFilter",
  "status": "400"
}
```

この JSON は error object の構造を示す非規範的な例です。RFC 7644 §3.12 の Error response では `status` は REQUIRED で、HTTP status code を JSON string として表します。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: §1.2, §3.4.2, §3.4.2.1, §3.4.2.2, §3.4.3, §3.12  
最終確認: 2026-09-19
