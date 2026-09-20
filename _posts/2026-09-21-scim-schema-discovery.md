---
layout: post
title: "SCIM Schema discovery：/Schemas から attribute definition をどう取得するのか"
date: 2026-09-21 06:44:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7643, RFC7644, Schema]
---

SCIM 2.0 は、Service Provider がサポートする schema と、その schema が定義する attribute の特性を取得するための `/Schemas` discovery endpoint を定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Client を実装し、Service Provider が公開する schema と attribute definition を取得・解釈したい開発者  
**この記事で伝えること:** `/Schemas` から Schema resource を取得し、`id` と `attributes` から resource attribute の定義を確認する方法  
**扱わないこと:** `/ResourceTypes` による resource type discovery、`/ServiceProviderConfig`、User / Group の具体的な attribute semantics、filter・sorting・pagination の利用方法

この記事は `/Schemas` discovery と Schema resource の構造に範囲を限定します。

## Article brief

- **Reader:** SCIM Client の実装者
- **Question:** Service Provider がサポートする schema と、その attribute の型・多値性・mutability などをどこから取得するのか
- **Answer:** `/Schemas` と個別 Schema resource の取得方法、および `attributes` に含まれる attribute definition の構造を理解できる
- **Scope:** RFC 7644 §4 の `/Schemas`、RFC 7643 §7 の Schema Definition
- **Out of scope:** ResourceType、ServiceProviderConfig、個別 resource operation、schema extension を resource instance に配置する方法
- **Primary sources:** RFC 7644 §4、RFC 7643 §2.2, §7, §8.7
- **Diagram:** `/Schemas` から Schema resource を取得し `attributes` を参照する関係

## 1. `/Schemas` はサポートする schema を返す

RFC 7644 §4 は、SCIM Service Provider がサポートする resource schema の情報を取得する endpoint として `/Schemas` を定義しています。

`GET /Schemas` は、サポートするすべての schema を `ListResponse` 形式で返します（SHALL）。個別の schema は、schema URI を `/Schemas` endpoint に付加して取得できます。

<pre class="mermaid">
flowchart TD
    A[SCIM Client] -->|GET /Schemas| B[Service Provider]
    B --> C[ListResponse]
    C --> D[Schema resource]
    D --> E[id]
    D --> F[attributes]
    F --> G[type / multiValued / mutability など]
</pre>

## 2. すべての Schema resource を取得する

次は request / response の配置を示すための**非規範的な例**です。host 名は illustrative value です。response は記事テーマに必要な member だけを示しています。

```http
GET /v2/Schemas HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

response は複数の Schema resource を `ListResponse` の `Resources` JSON member に格納します。

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
      "id": "urn:ietf:params:scim:schemas:core:2.0:User",
      "name": "User",
      "attributes": []
    }
  ]
}
```

RFC 7644 §4 により、複数の Schema resource を返す場合は `ListResponse` 形式を使用します（SHALL）。

## 3. 個別 Schema resource を取得する

RFC 7644 §4 は、schema URI を `/Schemas` に付加して個別 schema definition を取得できることを定義しています。

次は**非規範的な例**です。

```http
GET /v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User HTTP/1.1
Host: scim.example
Accept: application/scim+json
```

特定の Schema を要求した場合、RFC 7644 §4 により、単一 resource の取得と同じ形式で単一 JSON object が返されます。

## 4. Schema resource は attribute definition を保持する

RFC 7643 §7 は、resource object の `schemas` URI ごとに対応する Schema resource が存在することを定義しています。Schema resource は変更できず、その attributes の mutability は `readOnly` です。

Schema resource 自体の schema URI は次の値です。

`urn:ietf:params:scim:schemas:core:2.0:Schema`

Schema resource の `id` は schema URI です。`attributes` は、その schema が定義する attribute と特性を表す multi-valued complex attribute です。

## 5. `attributes` の最小構造

次は Schema resource の構造を示すための**非規範的な例**です。illustrative な attribute を1件だけ示しています。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:Schema"
  ],
  "id": "urn:example:params:scim:schemas:Example",
  "name": "Example",
  "attributes": [
    {
      "name": "exampleName",
      "type": "string",
      "multiValued": false,
      "required": false,
      "caseExact": false,
      "mutability": "readWrite",
      "returned": "default",
      "uniqueness": "none"
    }
  ]
}
```

RFC 7643 §7 が `attributes` に定義する主な sub-attribute は次のとおりです。

- `name`: attribute 名。
- `type`: data type。`string`、`boolean`、`decimal`、`integer`、`dateTime`、`reference`、`complex` が定義されています。
- `multiValued`: attribute が複数値を持つかを示す Boolean。
- `description`: 人が読める説明。該当する場合、Service Provider は指定しなければなりません（MUST）。
- `required`: attribute が required かを示す Boolean。
- `canonicalValues`: suggested canonical values。OPTIONAL です。
- `caseExact`: string attribute の case sensitivity を示す Boolean。
- `mutability`: attribute の変更可能性を表します。
- `returned`: response での返却特性を表します。
- `uniqueness`: uniqueness の特性を表します。
- `referenceTypes`: `reference` type に適用される参照先 type。該当する場合に使用します。

`type` が `complex` の場合、RFC 7643 §7 は対応する `subAttributes` を定義することを SHOULD としています。`subAttributes` は `attributes` と同じ schema sub-attribute を持ちます。

## 6. Schema discovery では filter・sorting・pagination を適用しない

RFC 7644 §4 は、`/Schemas` と `/ResourceTypes` の discovery endpoint に対し、§3.4.2 の filtering、sorting、pagination などの query parameter を無視することを SHALL としています。

`filter` が指定された場合、Service Provider は HTTP 403 (Forbidden) を返すことを SHOULD としています。これは、Client が filter condition に一致した結果だと誤って解釈することを防ぐための仕様上の規定です。

したがって `/Schemas` の一覧取得は、通常の resource collection search と同じ query processing を行う endpoint ではありません。

## 7. `/ResourceTypes` との役割の違い

`/Schemas` が返す Schema resource は attribute definition を記述します。一方、RFC 7643 §6 の ResourceType resource は、resource type の `endpoint`、primary `schema`、`schemaExtensions` を記述します。

この記事では Schema resource の取得と attribute definition の解釈だけを扱います。ResourceType discovery の詳細は別テーマです。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)

参照した主要節: RFC 7644 §4、RFC 7643 §2.2, §7, §8.7  
最終確認: 2026-09-21
