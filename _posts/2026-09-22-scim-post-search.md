---
layout: post
title: "SCIM の POST Search：/.search と SearchRequest の構造"
date: 2026-09-22 08:42:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Flow
- Reader: SCIM 2.0 で query parameter を URL に載せず検索を実行する Client / Service Provider 開発者
- Question: SCIM の HTTP POST query はどの endpoint と JSON body を使い、GET query とどのような関係にあるのか
- Answer: `/.search` の endpoint semantics、SearchRequest schema URI、request body に置ける query parameter、ListResponse との対応を説明できる
- Scope: RFC 7644 §3.4.3 の POST query request と、その response が §3.4.2 の ListResponse に従うこと
- Out of scope: filter expression 自体の評価規則、sorting semantics、index/cursor pagination の詳細、attributes / excludedAttributes の返却規則、authentication / authorization
- Primary sources: RFC 7644 §3.4.2, §3.4.3, §8.2
- Diagram: Client が `/.search` に SearchRequest を POST し Service Provider が ListResponse を返す sequenceDiagram
-->

## この記事について

**記事タイプ:** Flow  
**対象読者:** SCIM 2.0 で query parameter を URL に載せず検索を実行する Client / Service Provider 開発者  
**この記事で伝えること:** `/.search` endpoint、SearchRequest JSON body、ListResponse の関係  
**扱わないこと:** filter expression 自体の評価規則、sorting semantics、pagination の詳細、attribute selection の返却規則、authentication / authorization

RFC 7644 §3.4.3 は、Client が query parameter を URL に渡さず query を実行する方法として、HTTP POST と `/.search` path extension を定義しています。

**POST search changes where the query parameters are carried; the response still follows the SCIM ListResponse rules.**  
（POST search では query parameter の運搬場所が変わりますが、response は引き続き SCIM の ListResponse 規則に従います。）

## 1. POST query は `/.search` を使う

RFC 7644 §3.4.3 により、Client は HTTP POST と `/.search` path extension を組み合わせ、parameter を URL に渡さず query を実行できます（MAY）。有効な SCIM endpoint の末尾に `/.search` を付けることは、その POST が query operation であることを示すために使用されます（SHALL）。

たとえば service root 全体に対する query は `POST /.search`、特定 resource type に対する query はその resource endpoint の末尾に `/.search` を付けます。

## 2. request parameter は JSON body に置く

POST query の body には RFC 7644 §3.4.2 で定義された parameter を含めることができます（MAY）。RFC 7644 §3.4.3 が SearchRequest に定義する member は次のとおりです。

- `schemas`: request を識別する schema URI の配列です。POST query は `urn:ietf:params:scim:api:messages:2.0:SearchRequest` で識別しなければなりません（MUST、§3.4.3）。
- `attributes`: response に含める resource attribute 名の multi-valued list。OPTIONAL です。
- `excludedAttributes`: response から除外する resource attribute 名の multi-valued list。OPTIONAL です。
- `filter`: filter expression を表す string。OPTIONAL です。
- `sortBy`: sorting に用いる attribute path を表す string。OPTIONAL です。
- `sortOrder`: `ascending` または `descending` を表す string。OPTIONAL です。
- `startIndex`: 最初の query result の 1-based index を表す integer。OPTIONAL です。
- `count`: 1 page あたりの希望する最大 result 数を表す integer。OPTIONAL です。

各 parameter の評価規則そのものは、それぞれ RFC 7644 §3.4.2 の該当 subsection で定義されます。この記事では transport と message structure に範囲を限定します。

## 3. 非規範的な POST SearchRequest 例

以下は parameter の配置と JSON structure を示す**非規範的な例**です。host、filter value、count の値に追加の規範的意味はありません。

```http
POST /Users/.search HTTP/1.1
Host: scim.example
Accept: application/scim+json
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:SearchRequest"
  ],
  "filter": "userName sw \"illustrative\"",
  "startIndex": 1,
  "count": 10
}
```

`filter`、`startIndex`、`count` は URL query component ではなく、`application/scim+json` の request body の top-level JSON member として配置されています。

RFC 7644 §3.4.3 自体の例は `POST /.search` を使用しています。ここでは同 section が規定する「desired SCIM resource endpoint ending in `/.search`」という構造を明示するため、`/Users/.search` を illustrative endpoint としています。

## 4. response は ListResponse に従う

RFC 7644 §3.4.3 は、POST request を受信した後の response を §3.4.2 に従って返すと定めています。§3.4.2 では ListResponse を次の schema URI で識別することが MUST です。

```text
urn:ietf:params:scim:api:messages:2.0:ListResponse
```

以下は構造を示す**非規範的な response 例**です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:ListResponse"
  ],
  "totalResults": 1,
  "startIndex": 1,
  "itemsPerPage": 1,
  "Resources": [
    {
      "id": "illustrative-user-id",
      "userName": "illustrative-user"
    }
  ]
}
```

RFC 7644 §3.4.2 では `totalResults` は REQUIRED、`Resources` は `totalResults` が 0 でない場合 REQUIRED です。pagination による partial results の場合、`startIndex` と `itemsPerPage` が REQUIRED です。

一致する resource がない query は error ではありません。RFC 7644 §3.4.2 は、match がない query に HTTP 200 を返し、`totalResults` を 0 にすることを SHALL としています。

## 5. request と response の流れ

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant S as SCIM Service Provider
    C->>S: POST /Users/.search
    Note over C,S: SearchRequest JSON body
    S-->>C: 200 ListResponse
</pre>

この図は RFC 7644 §3.4.3 の request / response relation だけを示します。filter evaluation の内部処理、authorization decision、pagination algorithm は追加していません。

## 6. GET query との仕様上の関係

RFC 7644 §3.4.3 の POST query は、§3.4.2 の query parameter を request body に運ぶ方法です。POST query 専用の別形式の result object を定義するものではなく、response は §3.4.2 の ListResponse に従います。

したがってこの記事の中心は、次の対応関係です。

1. Client は query parameter を URL に載せない場合、POST と `/.search` を使用できます（MAY、§3.4.3）。
2. `/.search` を valid SCIM endpoint の末尾に付けることで POST query operation を示します（SHALL、§3.4.3）。
3. request は SearchRequest schema URI で識別しなければなりません（MUST、§3.4.3）。
4. query parameter は JSON request body に配置できます（MAY、§3.4.3）。
5. response は §3.4.2 の ListResponse に従います（§3.4.3）。

filter の構文、sorting、pagination、partial resource representation はそれぞれ独立した論点であり、ここでは再説明しません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.4.2, §3.4.3, §8.2
