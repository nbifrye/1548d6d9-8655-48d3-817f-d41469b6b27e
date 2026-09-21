---
layout: post
title: "SCIM の partial resource representation：attributes と excludedAttributes"
date: 2026-09-21 11:39:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Feature Deep Dive
- Reader: SCIM 2.0 の response attribute selection を実装またはレビューする Client / Service Provider 開発者
- Question: attributes / excludedAttributes はどこに配置し、schema の returned characteristic と組み合わせたとき response にどの attribute が含まれるのか
- Answer: GET の query parameter と POST /.search の JSON member の形式、両 parameter の排他性、minimum/default attribute set と returned=always/default/request/never の関係を区別できる
- Scope: RFC 7644 §3.4.2.5, §3.4.3, §3.9, §3.10 と RFC 7643 §2.2 に定義された partial resource representation
- Out of scope: filter による resource 選択、sorting、pagination、attribute-level authorization policy、Schema discovery の詳細
- Primary sources: RFC 7644 §3.4.2.5, §3.4.3, §3.9, §3.10; RFC 7643 §2.2
- Diagram: default/minimum set と attributes / excludedAttributes による response attribute set の決定を示す flowchart
-->

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM 2.0 の response attribute selection を実装またはレビューする Client / Service Provider 開発者  
**この記事で伝えること:** `attributes` / `excludedAttributes` の配置と形式、および schema の `returned` characteristic と組み合わせた response attribute set の決まり方  
**扱わないこと:** filter による resource 選択、sorting、pagination、attribute-level authorization policy、Schema discovery の詳細

SCIM では、resource representation を返す operation について、Client が `attributes` または `excludedAttributes` を指定して partial resource representation を要求できます。RFC 7644 §3.9 は、この2つを mutually exclusive な URL query parameter として定義しています。

**Attribute selection changes the representation returned for a resource; it does not select which resources match a query.**  
（attribute selection は resource の response representation を変えるものであり、query に一致する resource 自体を選択するものではありません。）

## 1. 基準になる minimum set と default set

RFC 7644 §3.9 は、resource representation が返る SCIM operation の attribute set を次の2つから構成します。

- minimum attribute set: schema の `returned` characteristic が `always` の attribute
- default attribute set: `returned` characteristic が `default` の attribute

RFC 7643 §2.2 は `returned` の値として `always`、`never`、`default`、`request` を定義しています。

- `always`: 常に返されます。
- `never`: request で指定されても返されません。
- `default`: デフォルトで返されます。
- `request`: `attributes` parameter で明示的に要求された場合に返されます。

`returned` characteristic は schema definition の一部です。この記事では Schema discovery 自体には踏み込みません。

## 2. GET では URL query parameter に置く

RFC 7644 §3.9 では、`attributes` と `excludedAttributes` は mutually exclusive です。GET など URL query parameter として指定する場合、値は standard attribute notation（RFC 7644 §3.10）による attribute name の comma-separated list です。

以下は配置を示す**非規範的な例**です。identifier と attribute value は説明用です。

```http
GET /Users/illustrative-user-id?attributes=userName,name.givenName HTTP/1.1
Host: example.com
Accept: application/scim+json
```

この request では `attributes` は query parameter です。RFC 7644 §3.9 に従い、response は minimum set に加えて、明示的に要求した attribute / sub-attribute を含みます。

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "illustrative-user-id",
  "userName": "illustrative-user",
  "name": {
    "givenName": "Illustrative"
  }
}
```

この JSON は構造を示す非規範的な例です。

## 3. attributes は default set を置き換える

RFC 7644 §3.9 では `attributes` を指定すると default attribute list が上書きされ、各 resource は minimum set と、`attributes` で明示的に要求された attribute / sub-attribute を含まなければなりません（MUST）。

RFC 7644 §3.4.2.5 でも、`attributes` は通常返される attribute set を override する multi-valued list として定義されています。attribute name は standard attribute notation でなければなりません（MUST、§3.4.2.5）。

## 4. excludedAttributes は default set から除外する

`excludedAttributes` を指定した場合、RFC 7644 §3.9 により各 resource は minimum set を含まなければなりません（MUST）。そのうえで、default set から `excludedAttributes` に列挙した attribute を除いたものが返されます。

以下は**非規範的な例**です。

```http
GET /Users/illustrative-user-id?excludedAttributes=emails,phoneNumbers HTTP/1.1
Host: example.com
Accept: application/scim+json
```

RFC 7644 §3.4.2.5 は、`excludedAttributes` が schema の `returned` characteristic が `always` の attribute には影響しないことを SHALL としています。つまり minimum set の attribute をこの parameter で除外することはできません。

## 5. POST /.search では JSON member に置く

RFC 7644 §3.4.3 は、URL に query parameter を渡さず `POST` と `/.search` を使う query operation を定義しています。この場合、`attributes` と `excludedAttributes` は SearchRequest JSON object の OPTIONAL member であり、値は string の配列です。

以下は `attributes` の配置を示す**非規範的な最小例**です。

```http
POST /Users/.search HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:SearchRequest"],
  "attributes": ["userName", "name.givenName"]
}
```

ここでは GET の comma-separated query value とは異なり、`attributes` は JSON member で、値は複数の string を持つ配列です。SearchRequest は `schemas` に `urn:ietf:params:scim:api:messages:2.0:SearchRequest` を指定しなければなりません（MUST、RFC 7644 §3.4.3）。

`excludedAttributes` を使う場合も同じ位置に string array として置きます。

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:SearchRequest"],
  "excludedAttributes": ["emails", "phoneNumbers"]
}
```

この例も非規範的です。

## 6. response attribute set の決まり方

<pre class="mermaid">
flowchart TD
    A[Resource representation を返す] --> B[minimum set: returned=always]
    B --> C{selection parameter}
    C -->|なし| D[minimum + default set]
    C -->|attributes| E[minimum + 明示指定]
    C -->|excludedAttributes| F[minimum + default - 除外指定]
</pre>

この図は RFC 7644 §3.9 の attribute selection を簡略化したものです。resource を query 対象として選択する filter や、attribute-level authorization の判断は追加していません。

## 7. 仕様上の境界

`attributes` / `excludedAttributes` について確認すべき点は次のとおりです。

- SCIM Client は2つの OPTIONAL parameter の一方を使用できます（MAY）。Service Provider はこれらをサポートしなければなりません（MUST、RFC 7644 §3.4.2.5）。
- resource representation を返す operation では `attributes` と `excludedAttributes` は mutually exclusive です（RFC 7644 §3.9）。
- GET の URL query parameter では attribute name を comma-separated list として指定します（RFC 7644 §3.9）。
- POST `/.search` では SearchRequest JSON object の multi-valued string member として指定します（RFC 7644 §3.4.3）。
- attribute name は standard attribute notation でなければなりません（MUST、RFC 7644 §3.4.2.5）。
- `excludedAttributes` は `returned=always` の attribute に影響しません（SHALL、RFC 7644 §3.4.2.5）。
- `returned=never` の attribute は request で指定されても返されません（RFC 7643 §2.2）。

どの Client がどの attribute を参照できるかという access-control policy は、この selection mechanism とは別の論点です。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.4.2.5, §3.4.3, §3.9, §3.10
- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §2.2
