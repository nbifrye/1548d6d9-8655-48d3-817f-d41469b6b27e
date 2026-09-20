---
layout: post
title: "RFC 7644：SCIM の sortBy / sortOrder は検索結果をどう並べ替えるのか"
date: 2026-09-21 01:38:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7644, Sorting]
---

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM の検索結果を属性値で並べ替える Client / Service Provider の実装者  
**この記事で伝えること:** RFC 7644 の `sortBy` と `sortOrder` の配置、既定値、属性型ごとの並べ替え規則  
**扱わないこと:** filter expression、index-based / cursor-based pagination、属性選択、Service Provider Configuration 全般

## Article brief

- **Reader:** SCIM の検索結果を属性値で並べ替える Client / Service Provider の実装者
- **Question:** `sortBy` と `sortOrder` はどこに置き、Service Provider はどの値と順序で結果を並べ替えるのか
- **Answer:** GET query と POST `/.search` での parameter 配置、`sortOrder` の既定値、単一値・複数値・complex attribute の評価規則を追える
- **Scope:** RFC 7644 §3.4.2.3 と、POST query における同 parameter の配置
- **Out of scope:** filter、pagination、attribute projection、cursor pagination
- **Primary sources:** RFC 7644 §3.4.2, §3.4.2.3, §3.4.3, §4
- **Diagram:** Client が sorting parameter を送り、Service Provider が attribute value に従って ListResponse を並べる処理

RFC 7644 §3.4.2.3 の sorting は OPTIONAL です。Client は Service Provider Configuration の `sort` attribute によって、Service Provider が sorting をサポートするか確認できます。

## 1. GET query では URL parameter として送る

Sorting は `sortBy` と `sortOrder` の組み合わせで指定します。GET による query では URL query parameter に配置します。

以下は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /Users?sortBy=name.givenName&sortOrder=descending HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

- `sortBy`: 並べ替えに使う attribute を指定します。
- `sortOrder`: `ascending` または `descending` を指定します。

`sortBy` が指定され、`sortOrder` が指定されていない場合、RFC 7644 §3.4.2.3 により `sortOrder` は `ascending` を既定値とします（SHALL）。

## 2. Service Provider がどの値を使うか

`sortBy` が単一値 attribute を示す場合、その attribute value を使って resource を並べます。

複数値 attribute の場合は、primary attribute の value があればそれを使い、なければ list の最初の value を使います。complex attribute を指定する場合は、`name.givenName` のように standard attribute notation で sub-attribute まで示します（RFC 7644 §3.4.2.3）。

指定された `sortBy` attribute の data が resource に存在しない場合、その resource は ascending では後ろ、descending では前に配置されます。

<pre class="mermaid">
flowchart TD
    A[Client query] --> B[sortBy を評価]
    B --> C[並べ替え対象 value を決定]
    C --> D[sortOrder を適用]
    D --> E[ListResponse]
</pre>

## 3. attribute type に従って並べ替える

RFC 7644 §3.4.2.3 は、`sortOrder` が attribute type に従って並べ替えなければならないことを MUST としています。

String attribute は、attribute definition が case-exact string でない限り、既定では case-insensitive です。case-insensitive attribute は locale を特定しない case-insensitive Unicode alphabetic sort order、case-exact attribute は case-sensitive Unicode alphabetic sort order で並べます。

この規則は、特定 locale の照合順序を追加で規定するものではありません。

## 4. POST `/.search` では JSON member として送る

RFC 7644 §3.4.3 は、query parameter を URL に置かず、HTTP POST と `/.search` を使って query する方法も定義しています。この場合、`sortBy` と `sortOrder` は SearchRequest の JSON member です。

以下は配置を示すための**非規範的な例**です。

```http
POST /Users/.search HTTP/1.1
Host: scim.example
Accept: application/scim+json
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:SearchRequest"
  ],
  "sortBy": "name.givenName",
  "sortOrder": "ascending"
}
```

`sortBy` と `sortOrder` の意味は GET query と同じです。`sortBy` は standard attribute notation の attribute name、`sortOrder` は `ascending` または `descending` です。

## 5. response は ListResponse で返る

Sorting は返却 resource の順序を指定する機能です。RFC 7644 §3.4.2 の query response は ListResponse を使用します。

以下は構造を示すための**非規範的な最小例**です。resource の値は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:ListResponse"
  ],
  "totalResults": 2,
  "Resources": [
    { "userName": "illustrative-a" },
    { "userName": "illustrative-b" }
  ]
}
```

この記事では sorting だけを扱います。`startIndex` / `count` による index-based pagination、および RFC 9865 の cursor-based pagination は別のテーマです。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: RFC 7644 §3.4.2, §3.4.2.3, §3.4.3, §4  
最終確認: 2026-09-21
