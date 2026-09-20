---
layout: post
title: "SCIM ResourceTypes：Service Provider が扱う Resource Type をどう発見するのか"
date: 2026-09-21 05:45:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7643, RFC7644, ResourceTypes]
---

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Client を実装し、Service Provider が扱う Resource Type と endpoint、schema の対応を確認したい開発者  
**この記事で伝えること:** `/ResourceTypes` から ResourceType resource を取得し、`endpoint`、`schema`、`schemaExtensions` によって利用可能な Resource Type の構成を確認する方法  
**扱わないこと:** `/Schemas` による attribute schema の取得、`/ServiceProviderConfig` による protocol capability discovery、User / Group resource の CRUD、schema extension の設計方法

この記事は RFC 7643 §6 と RFC 7644 §4 の **ResourceType discovery** に範囲を限定します。

## Article brief

- **Reader:** SCIM Client の discovery 処理を実装・レビューする開発者。
- **Question:** Service Provider がどの Resource Type を公開し、それぞれがどの endpoint・base schema・schema extension を使うかを Client はどう確認するのか。
- **Answer:** `/ResourceTypes` と個別 ResourceType resource の取得方法、および `name`、`endpoint`、`schema`、`schemaExtensions` の関係を確認できる。
- **Scope:** RFC 7644 §4 の `/ResourceTypes` と RFC 7643 §6 の ResourceType schema。
- **Out of scope:** `/Schemas`、`/ServiceProviderConfig`、各 Resource Type の resource operation、extension schema の attribute definition。
- **Primary sources:** RFC 7644 §4、RFC 7643 §3.2, §6, §8.6。
- **Diagram:** Client が `/ResourceTypes` を取得し、ResourceType の `endpoint` と `schema` を確認する関係。

## 1. ResourceType は Resource の種類と endpoint / schema の対応を記述する

RFC 7643 §3.2 は、新しい種類の SCIM resource を提供する場合、Service Provider が Resource Type を定義するとしています。Resource Type は name、endpoint、base schema、および schema extension を定義します。

RFC 7643 §6 は ResourceType resource を READ-ONLY とし、schema URI を次の値として定義しています。

`urn:ietf:params:scim:schemas:core:2.0:ResourceType`

ResourceType resource の主要 attribute は次のとおりです。

- `id`: Service Provider 内の Resource Type identifier。OPTIONAL。
- `name`: Resource Type name。REQUIRED。該当する場合、Service Provider は `User` や `Group` などの name を指定しなければなりません（MUST, RFC 7643 §6）。
- `description`: human-readable description。OPTIONAL。
- `endpoint`: Service Provider の Base URL に対する HTTP-addressable endpoint。REQUIRED。
- `schema`: primary / base schema URI。REQUIRED。この値は対応する Schema resource の `id` と等しくなければなりません（MUST, RFC 7643 §6）。
- `schemaExtensions`: Resource Type の schema extension のリスト。OPTIONAL。

`schemaExtensions` の各要素には `schema` と `required` が定義されています。`required` が `true` の場合、その Resource Type の resource は当該 schema extension と、その extension で required とされた attribute を含めなければなりません（MUST, RFC 7643 §6）。`false` の場合は、その extension を省略できます（MAY）。

## 2. `/ResourceTypes` で利用可能な Resource Type を取得する

RFC 7644 §4 は、Service Provider で利用可能な Resource Type を発見する endpoint として `/ResourceTypes` を定義しています。

<pre class="mermaid">
flowchart TD
    A[SCIM Client] -->|GET /ResourceTypes| B[Service Provider]
    B --> C[ListResponse]
    C --> D[ResourceType]
    D --> E[endpoint]
    D --> F[base schema]
    D --> G[schema extensions]
</pre>

以下は配置と response structure を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /scim/v2/ResourceTypes HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

複数の ResourceType を返す場合、RFC 7644 §4 は `urn:ietf:params:scim:api:messages:2.0:ListResponse` の形式を使用することを要求しています（SHALL）。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:ListResponse"
  ],
  "totalResults": 1,
  "Resources": [
    {
      "schemas": [
        "urn:ietf:params:scim:schemas:core:2.0:ResourceType"
      ],
      "id": "User",
      "name": "User",
      "endpoint": "/Users",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
    }
  ]
}
```

この例では `Resources` 配列の各要素が ResourceType resource です。`endpoint` は Resource Type の endpoint、`schema` はその Resource Type の primary / base schema URI を表します。

## 3. 個別の ResourceType も取得できる

RFC 7644 §4 は、個別 ResourceType の取得について、単一の User または Group を取得する場合と同様に単一 JSON object を返すと規定しています。

以下は**非規範的な例**です。

```http
GET /scim/v2/ResourceTypes/User HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:ResourceType"
  ],
  "id": "User",
  "name": "User",
  "endpoint": "/Users",
  "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
}
```

ResourceType resource は READ-ONLY です（RFC 7643 §6）。この記事では read operation のみを扱います。

## 4. `schemaExtensions` は Resource Type に追加される schema を示す

ResourceType は primary schema に加えて `schemaExtensions` を持つことができます。

以下は object structure を示すための**非規範的な例**です。URI は RFC 7643 で定義される Enterprise User extension を使用しています。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:ResourceType"
  ],
  "id": "User",
  "name": "User",
  "endpoint": "/Users",
  "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
  "schemaExtensions": [
    {
      "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
      "required": true
    }
  ]
}
```

RFC 7643 §6 では、`schemaExtensions[].schema` は対応する Schema resource の `id` と等しくなければなりません（MUST）。`required` は Boolean で REQUIRED です。

この ResourceType representation は「どの extension schema が Resource Type に関連付けられているか」を示します。extension schema 内の attribute definition 自体は `/Schemas` と RFC 7643 §7 の別テーマです。

## 5. discovery endpoint では通常の collection query parameter を適用しない

RFC 7644 §4 は、複数の ResourceType または Schema を返す場合に ListResponse を使用しますが、通常の resource collection と同じ検索処理を行うとは規定していません。

Section 3.4.2 の filtering、sorting、pagination などの query parameter は無視しなければなりません（SHALL）。`filter` が指定された場合、Service Provider は HTTP 403 (Forbidden) を返すべきです（SHOULD, RFC 7644 §4）。これは Client が filter condition に一致したと誤認しないための規定です。

## 6. `/ServiceProviderConfig` と `/Schemas` との役割の違い

`/ResourceTypes` が示すのは、Service Provider が公開する Resource Type と、その endpoint・base schema・schema extension の対応です。

`/ServiceProviderConfig` は PATCH、Bulk、filter、sort など protocol capability を記述します。これは別記事のテーマです。

`/Schemas` は Service Provider がサポートする schema definition を取得する endpoint です。ResourceType の `schema` / `schemaExtensions[].schema` が参照する schema の attribute definition は `/Schemas` 側のテーマであり、本記事では扱いません。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)

参照した主要節: RFC 7644 §4、RFC 7643 §3.2, §6, §8.6  
最終確認: 2026-09-21
