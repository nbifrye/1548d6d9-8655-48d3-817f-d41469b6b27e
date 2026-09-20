---
layout: post
title: "SCIM ServiceProviderConfig：Service Provider の対応機能をどう取得するのか"
date: 2026-09-21 04:45:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7643, RFC7644]
---

RFC 7644 §4 は、SCIM Service Provider が対応する機能と構成を取得するための `/ServiceProviderConfig` discovery endpoint を定義しています。返される JSON object の属性は RFC 7643 §5 で定義されています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Client を実装・接続し、接続先 Service Provider が対応する protocol feature を確認したい開発者  
**この記事で伝えること:** `/ServiceProviderConfig` への GET と、その response に含まれる capability configuration の構造  
**扱わないこと:** `/ResourceTypes`、`/Schemas`、各 feature の具体的な利用手順、authentication scheme の選択、RFC 9865 の cursor pagination metadata

### Article brief

- **Reader:** SCIM Client の実装・接続担当者
- **Question:** Service Provider が PATCH、Bulk、filter、sort などに対応しているかを、標準化された endpoint と JSON structure からどう確認するか
- **Answer:** `/ServiceProviderConfig` を GET し、RFC 7643 §5 が定義する read-only configuration attributes を確認する処理と構造を理解できる
- **Scope:** RFC 7644 §4 の `/ServiceProviderConfig` と RFC 7643 §5 の ServiceProviderConfig schema
- **Out of scope:** 他の discovery endpoint、各 feature の protocol semantics、cursor-based pagination extension
- **Primary sources:** RFC 7644 §4、RFC 7643 §5, §8.5
- **Diagram:** Client が `/ServiceProviderConfig` を GET し、Service Provider が configuration JSON を返す関係

## 1. `/ServiceProviderConfig` は discovery endpoint である

RFC 7644 §4 は、SCIM Service Provider の feature と schema を discovery するための3つの endpoint を定義しています。そのうち `/ServiceProviderConfig` は、Service Provider で利用可能な SCIM specification feature を記述する JSON structure を返します。

RFC 7644 §4 は、この endpoint への HTTP `GET` に対して、`schemas` attribute に次の schema URI を持つ JSON object を返すことを SHALL としています。

`urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig`

<pre class="mermaid">
flowchart TD
    C[SCIM Client] -->|GET /ServiceProviderConfig| SP[Service Provider]
    SP -->|ServiceProviderConfig JSON| C
</pre>

この図は configuration discovery の request / response だけを示します。個々の feature を使用する後続処理は含めていません。

## 2. GET request と response の配置

以下は配置と構造を示すための**非規範的な例**です。host name は illustrative value です。

```http
GET /v2/ServiceProviderConfig HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

RFC 7644 §4 で定義される操作は HTTP `GET` です。この request には ServiceProviderConfig 固有の query parameter や request body はありません。

以下は response object の最小構造を把握するための**非規範的な例**です。値は illustrative value であり、RFC 7643 §5 が定義する attribute のうち主要な capability を示しています。

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
    "supported": false
  },
  "authenticationSchemes": []
}
```

この例は feature の優劣や選択方針を示すものではありません。

## 3. capability attributes は read-only configuration である

RFC 7643 §5 の ServiceProviderConfig schema は、Service Provider の configuration を表す attributes を定義します。`patch`、`bulk`、`filter`、`changePassword`、`sort`、`etag` は REQUIRED の complex attributes で、それぞれ `supported` Boolean sub-attribute を持ちます。

`bulk` には、さらに `maxOperations` と `maxPayloadSize` が定義されています。これらは integer であり、Service Provider が Bulk operation をサポートする場合に REQUIRED です。

`filter` の `maxResults` は integer で、Service Provider が filtering をサポートする場合に REQUIRED です。

これらの configuration attributes は RFC 7643 §5 の schema definition で `readOnly` とされています。本記事では各 feature 自体の request / response semantics は扱いません。

## 4. `authenticationSchemes` は対応する authentication scheme を記述する

RFC 7643 §5 は `authenticationSchemes` を multi-valued complex attribute として定義しています。Service Provider が対応する authentication scheme を記述するための属性です。

各要素には `type`、`name`、`description`、`specUri`、`documentationUri`、`primary` が定義されています。`type`、`name`、`description` は REQUIRED、その他は OPTIONAL です。

RFC 7643 §5 は、複数の authentication scheme がある場合、`primary` が `true` の scheme を1つだけ指定できるとしています。この属性は対応方式を記述するものであり、本記事では Client がどの方式を選択するかという policy は扱いません。

## 5. `documentationUri` は protocol capability とは別の情報である

RFC 7643 §5 は optional な `documentationUri` attribute も定義しています。これは Service Provider の human-consumable help documentation を指す HTTP-addressable URL です。

`documentationUri` は `patch.supported` や `sort.supported` のような protocol capability flag ではありません。ServiceProviderConfig object の一部として、Service Provider の documentation location を表します。

## 6. 他の discovery endpoint とは役割が異なる

RFC 7644 §4 には `/ServiceProviderConfig` のほかに `/ResourceTypes` と `/Schemas` があります。

`/ServiceProviderConfig` が返すのは Service Provider の feature configuration です。利用可能な resource type の定義や schema definition 自体を取得する処理は本記事の scope 外です。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)

参照した主要節: RFC 7644 §4、RFC 7643 §5, §8.5  
最終確認: 2026-09-21
