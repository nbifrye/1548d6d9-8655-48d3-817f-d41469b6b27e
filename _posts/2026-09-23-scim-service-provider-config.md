---
layout: post
title: "SCIM ServiceProviderConfig：サーバーが公開する機能を確認する"
date: 2026-09-23 05:46:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM 2.0 Service Provider が公開する機能を標準の discovery endpoint から確認したい Provisioning Client / Service Provider の実装者  
**この記事で伝えること:** `/ServiceProviderConfig` の取得方法と、RFC 7643 が定義する ServiceProviderConfig resource の構造  
**扱わないこと:** `/ResourceTypes`、`/Schemas`、各機能の request 処理、authentication scheme の選定・推奨、RFC 9865 / RFC 9967 で追加された機能

## Article brief

- **Reader:** SCIM 2.0 の標準 discovery endpoint から Service Provider の機能情報を取得する実装者
- **Question:** `/ServiceProviderConfig` から何を取得でき、response の各 member はどのような構造か
- **Answer:** GET endpoint、schema URI、required / optional member、および `supported` や上限値の配置を確認できる
- **Scope:** RFC 7644 §4 の `/ServiceProviderConfig` と RFC 7643 §5 の Service Provider Configuration Schema
- **Out of scope:** `/ResourceTypes`、`/Schemas`、PATCH / Bulk / filter / sort の個別処理、認証方式の評価、拡張仕様
- **Primary sources:** RFC 7644 §4、RFC 7643 §5・§8.5
- **Diagram:** Client が `/ServiceProviderConfig` を GET し、Service Provider が configuration resource を返す flowchart

## 1. `/ServiceProviderConfig` は discovery endpoint

RFC 7644 §4 は、SCIM Service Provider の feature と schema を discovery するための3つの endpoint を定義しています。本記事が扱うのは `/ServiceProviderConfig` だけです。

Client は HTTP GET で configuration resource を取得します。

以下は配置を示す**非規範的な例**です。host 名は illustrative value です。

```http
GET /ServiceProviderConfig HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

RFC 7644 §4 により、この endpoint の response は `schemas` に次の URI を持つ JSON object を返さなければなりません（**SHALL**）。

```text
urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig
```

## 2. ServiceProviderConfig resource の構造

RFC 7643 §5 は Service Provider Configuration Schema を定義しています。この resource のすべての attribute は `readOnly` です。また、他の core resource と異なり `id` は required ではありません。

以下は構造と配置を確認するための**非規範的な最小例**です。値は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"
  ],
  "patch": {
    "supported": true
  },
  "bulk": {
    "supported": false,
    "maxOperations": 0,
    "maxPayloadSize": 0
  },
  "filter": {
    "supported": true,
    "maxResults": 100
  },
  "changePassword": {
    "supported": false
  },
  "sort": {
    "supported": true
  },
  "etag": {
    "supported": true
  },
  "authenticationSchemes": []
}
```

この例の boolean や integer は特定 deployment の推奨値を示すものではありません。

## 3. required な capability member

RFC 7643 §5 では、次の complex attribute が REQUIRED です。

- **`patch`**: `supported` は required boolean。PATCH operation の support 有無を表します。
- **`bulk`**: `supported`、`maxOperations`、`maxPayloadSize` は required。後者2つは integer です。
- **`filter`**: `supported` と `maxResults` は required。`maxResults` は integer です。
- **`changePassword`**: `supported` は required boolean。
- **`sort`**: `supported` は required boolean。
- **`etag`**: `supported` は required boolean。
- **`authenticationSchemes`**: required かつ multi-valued の complex attribute です。

`documentationUri` は OPTIONAL です。HTTP-addressable URL として、Service Provider の human-consumable help documentation を指します。

## 4. `authenticationSchemes` が表す情報

RFC 7643 §5 の `authenticationSchemes` は、Service Provider がサポートする authentication scheme の property を表す multi-valued complex attribute です。

各要素では、次の sub-attribute が定義されています。

- `name`: REQUIRED string
- `description`: REQUIRED string
- `specUri`: OPTIONAL reference
- `documentationUri`: OPTIONAL reference
- `type`: REQUIRED string
- `primary`: REQUIRED boolean

`type` の値は RFC 7643 §5 に列挙された authentication scheme type を表します。本記事では、どの scheme を採用すべきかという評価は行いません。

## 5. discovery の関係

<pre class="mermaid">
flowchart TD
    A[SCIM Client]
    B[GET /ServiceProviderConfig]
    C[SCIM Service Provider]
    D[ServiceProviderConfig JSON]

    A --> B
    B --> C
    C --> D
    D --> A
</pre>

この flow で Client が取得するのは、Service Provider が標準 schema で公開する configuration information です。PATCH、Bulk、filter など各 operation の具体的な処理規則は、それぞれ RFC 7644 の該当 section で定義されています。

## 6. 仕様上の境界

`ServiceProviderConfig` は feature discovery のための resource です。RFC 7643 §5 は capability と implementation detail を標準化された形式で Client に提供するための schema として定義しています。

したがって、本記事では `supported` の値や上限値について特定の設定を推奨しません。実際に Service Provider がどの機能を提供するか、また上限値をいくつにするかは、本記事が扱う RFC 7643 §5 / RFC 7644 §4 の範囲では一律の値として規定されていません。

## Primary sources

- RFC 7644, §4, “Service Provider Configuration Endpoints”
- RFC 7643, §5, “Service Provider Configuration Schema”
- RFC 7643, §8.5, Service Provider Configuration representation example
