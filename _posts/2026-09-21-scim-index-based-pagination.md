---
layout: post
title: "RFC 7644：SCIM の startIndex / count で検索結果をページングする"
date: 2026-09-21 02:43:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7644, Pagination]
---

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM の検索結果を複数ページに分けて取得する Client / Service Provider の実装者  
**この記事で伝えること:** RFC 7644 の index-based pagination で `startIndex` / `count` をどこに置き、`ListResponse` の `startIndex` / `itemsPerPage` / `totalResults` をどう解釈するか  
**扱わないこと:** RFC 9865 の cursor-based pagination、filter、sorting、attribute projection

## Article brief

- **Reader:** SCIM の検索結果を複数ページに分けて取得する Client / Service Provider の実装者
- **Question:** `startIndex` と `count` はどこに指定し、返された `ListResponse` の pagination 情報をどう読めばよいか
- **Answer:** GET query と POST `/.search` での parameter 配置、1-based index、`count` の上限としての意味、partial results の response member、次ページ取得時の位置を追える
- **Scope:** RFC 7644 §3.4.2, §3.4.2.4, §3.4.3 の index-based pagination
- **Out of scope:** RFC 9865 の cursor-based pagination、filter、sorting、attribute projection
- **Primary sources:** RFC 7644 §3.4.2, §3.4.2.4, §3.4.3
- **Diagram:** Client が `startIndex` / `count` を指定し、Service Provider が対応する ListResponse page を返す処理

RFC 7644 §3.4.2.4 は、Client または Service Provider が大量の resource に圧倒されないよう、検索結果をページ単位で取得するための pagination parameter を定義しています。

## 1. `startIndex` と `count`

RFC 7644 §3.4.2.4 の request parameter は次の2つです。

- `startIndex`: 最初に返してほしい query result の **1-based index**。既定値は `1`。`1` 未満の値は `1` として解釈します（SHALL）。
- `count`: 1ページで返してほしい query result の最大数を表す非負整数。指定した場合、Service Provider はその数を超える result を返してはなりません（MUST NOT）が、より少ない数を返すことはできます（MAY）。負数は `0` として解釈します（SHALL）。`0` は resource result を返さず、`totalResults` だけを返す指定です。

`count` を省略した場合に返す最大数は Service Provider が決定します。RFC 7644 は一律の page size を規定していません。

## 2. GET query では URL query parameter に置く

次は parameter の配置を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /Users?startIndex=1&count=10 HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

`startIndex` と `count` は URL query parameter です。この例は先頭の result から最大10件を要求します。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[GET /Users]
    B --> C[startIndex=1]
    C --> D[count=10]
    D --> E[Service Provider]
    E --> F[ListResponse page]
</pre>

## 3. partial results の `ListResponse`

RFC 7644 §3.4.2 は query response を `urn:ietf:params:scim:api:messages:2.0:ListResponse` で識別することを要求しています（MUST）。

Pagination により partial results を返す場合、`startIndex` と `itemsPerPage` は REQUIRED です。`totalResults` は list または query operation の result 総数を表す REQUIRED member です。

以下は構造を示すための**非規範的な例**です。resource identifier と件数は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:ListResponse"
  ],
  "totalResults": 25,
  "itemsPerPage": 10,
  "startIndex": 1,
  "Resources": [
    {
      "id": "illustrative-user-1",
      "userName": "illustrative-user"
    }
  ]
}
```

主要 member の意味は次のとおりです。

- `totalResults`: query に一致する result の総数。
- `itemsPerPage`: 現在の response page で返した resource 数。
- `startIndex`: 現在の result set の最初の result の 1-based index。
- `Resources`: requested resources。pagination 時には全 result の subset になり得ます（MAY）。`totalResults` が 0 でない場合は REQUIRED です。

## 4. 次のページは次の 1-based index から要求する

RFC 7644 §3.4.2.4 の例では、`startIndex=1&count=10` の次に `startIndex=11&count=10` を指定して次ページを取得します。

次は配置を示すための**非規範的な例**です。

```http
GET /Users?startIndex=11&count=10 HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

RFC 7644 の pagination は stateful ではありません。Client は inconsistent results を処理できなければなりません（MUST, §3.4.2.4）。同じ request を繰り返しても、その間に Service Provider 上の resource が変更されれば異なる結果になる場合があります。

## 5. POST `/.search` では JSON member に置く

RFC 7644 §3.4.3 により、Client は URL に query parameter を置かず、HTTP POST と `/.search` を使って query を実行できます（MAY）。この場合、`startIndex` と `count` は SearchRequest の JSON member として request body に配置できます。

以下は**非規範的な例**です。

```http
POST /Users/.search HTTP/1.1
Host: scim.example
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:SearchRequest"
  ],
  "startIndex": 11,
  "count": 10
}
```

`startIndex` と `count` はどちらも OPTIONAL な integer member です。POST query の response は RFC 7644 §3.4.2 の ListResponse として返されます。

## 6. `count=0` は総件数だけを要求する

RFC 7644 §3.4.2.4 は `count=0` を、resource result を返さず `totalResults` のみを返す指定として定義しています。

```http
GET /Users?count=0 HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

この場合も query 自体の結果件数は `totalResults` で表されます。

## 7. cursor-based pagination は別仕様

RFC 9865 は RFC 7644 を更新し、`cursor` と `nextCursor` などを用いる cursor-based pagination を追加しています。本記事は RFC 7644 §3.4.2.4 の `startIndex` / `count` による index-based pagination だけを扱います。

両方式をサポートする Service Provider の選択規則や cursor の semantics は RFC 9865 の別テーマです。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: RFC 7644 §3.4.2, §3.4.2.4, §3.4.3  
最終確認: 2026-09-21
