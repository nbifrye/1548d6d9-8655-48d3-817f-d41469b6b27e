---
layout: post
title: "SCIM Bulk request：複数の resource operation を1回の request にまとめる"
date: 2026-09-23 08:40:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** SCIM 2.0 の Bulk endpoint を実装する Provisioning Client / Service Provider の実装者  
**この記事で伝えること:** Bulk request の HTTP/JSON 構造、各 operation の required member、`failOnErrors`、Service Provider が公開する処理上限の関係  
**扱わないこと:** `bulkId` による resource 間参照と circular reference、Bulk response の詳細、非同期 response、個々の POST / PUT / PATCH / DELETE の処理規則

## Article brief

- **Reader:** SCIM 2.0 の Bulk endpoint に複数 operation を送る Client / Service Provider の実装者
- **Question:** Bulk request はどのような HTTP request と JSON object で構成され、各 operation には何を配置するのか
- **Answer:** `/Bulk` への POST、BulkRequest schema URI、`Operations`、`method` / `path` / `data` / `version` / `bulkId`、`failOnErrors`、および server の bulk limits の関係を確認できる
- **Scope:** RFC 7644 §3.7 の Bulk request structure と request limits、RFC 7643 §5 の `bulk` capability
- **Out of scope:** RFC 7644 §3.7.1–§3.7.3 の cross-reference / response processing の詳細、RFC 9967 の asynchronous response、各 resource operation の個別 semantics
- **Primary sources:** RFC 7644 §3.7、RFC 7643 §5
- **Diagram:** Client が BulkRequest を POST し、Service Provider が limits を確認して各 operation を処理する flowchart

## 1. Bulk は optional な Service Provider feature

RFC 7644 §3.7 は SCIM Bulk operation を optional server feature として定義しています。Client は複数の resource operation を1つの request に含められます。Bulk support は `/ServiceProviderConfig` から discovery できます。

RFC 7643 §5 の ServiceProviderConfig では `bulk` は REQUIRED な complex attribute で、次の sub-attribute を持ちます。

- `supported`: REQUIRED boolean。Bulk operation の support 有無。
- `maxOperations`: REQUIRED integer。最大 operation 数。
- `maxPayloadSize`: REQUIRED integer。最大 payload size（bytes）。

これらの値について、RFC 7643 §5 は一律の推奨値を定めていません。

## 2. Bulk request の配置

Bulk request は `/Bulk` endpoint に HTTP POST で送ります。request body は `application/scim+json` の JSON object です。

以下は構造と配置を確認するための**非規範的な例**です。host、resource value、`bulkId` は illustrative value です。

```http
POST /Bulk HTTP/1.1
Host: scim.example
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:BulkRequest"
  ],
  "failOnErrors": 2,
  "Operations": [
    {
      "method": "POST",
      "path": "/Users",
      "bulkId": "illustrative-user-1",
      "data": {
        "schemas": [
          "urn:ietf:params:scim:schemas:core:2.0:User"
        ],
        "userName": "illustrative-user@example.com"
      }
    },
    {
      "method": "DELETE",
      "path": "/Users/illustrative-id"
    }
  ]
}
```

RFC 7644 §3.7 は Bulk request の schema URI を `urn:ietf:params:scim:api:messages:2.0:BulkRequest` と定義しています。

## 3. `Operations` と operation object

RFC 7644 §3.7 では `Operations` は REQUIRED で、各要素は1つの resource endpoint に対する HTTP request に対応します。

各 operation で使われる主要 member は次のとおりです。

- `method`: REQUIRED。`POST`、`PUT`、`PATCH`、`DELETE` のいずれか。
- `path`: request では REQUIRED。Service Provider root からの relative path。`POST` では resource type endpoint、その他の method では特定 resource の path を指定します。
- `data`: `POST`、`PUT`、`PATCH` の request では REQUIRED。単独の SCIM operation で送る resource data を配置します。`DELETE` ではこの member は要求されません。
- `bulkId`: `method` が `POST` の場合は REQUIRED。Client が作る、Bulk request 内で一意な transient identifier です。
- `version`: Service Provider が ETag を support し、`method` が `PUT`、`PATCH`、`DELETE` の場合に使用できます（**MAY**）。

`bulkId` を別 operation 内の新規 resource 参照に使用する規則は RFC 7644 §3.7.2 の別論点であるため、本記事では扱いません。

## 4. `failOnErrors` が指定されていない場合と指定された場合

RFC 7644 §3.7 では `failOnErrors` は request で OPTIONAL な integer です。Service Provider が受け入れる error 数を指定し、その数に達した後の残りの operation を停止するために使われます。

`failOnErrors` による override がない場合、Service Provider は可能な限り多くの変更を継続し、partial failure を無視しなければなりません（**MUST**、RFC 7644 §3.7）。Client は `failOnErrors` を指定してこの behavior を override できます（**MAY**、同 section）。

この member は Bulk response では valid ではありません。

## 5. `maxOperations` と `maxPayloadSize` を超えた request

RFC 7644 §3.7 は、Service Provider が Bulk request に対して operation 数と payload size の上限を設けられることを定義しています。これらの limit は ServiceProviderConfig の `bulk.maxOperations` と `bulk.maxPayloadSize` から取得できます。

いずれかの limit を超えた場合、Service Provider は HTTP `413 Payload Too Large` を返さなければなりません（**MUST**、RFC 7644 §3.7）。返す error response body では、超過した limit を示さなければなりません（**MUST**、同 section）。

## 6. request 処理の関係

<pre class="mermaid">
flowchart TD
    A[SCIM Client]
    B[POST /Bulk]
    C[BulkRequest JSON]
    D[Service Provider]
    E{limits exceeded?}
    F[413 Error]
    G[Process Operations]

    A --> B
    B --> C
    C --> D
    D --> E
    E -->|yes| F
    E -->|no| G
</pre>

この図は Bulk request の入口と limits の関係だけを示しています。個々の operation の resource semantics は、それぞれの POST / PUT / PATCH / DELETE の規則に従います。

## 7. 仕様上の境界

RFC 7644 §3.7 は Service Provider が operation の処理順を最適化することを認めています（**MAY**）。ただし、最適化する場合でも Client の intent を保持し、最適化しない処理と同じ stateful result を達成しなければなりません（**MUST**）。

一方、どのような内部 queue、transaction、database 処理で Bulk operation を実現するかは、この section が定める wire format ではありません。本記事では特定の implementation strategy を推奨しません。

## Primary sources

- RFC 7644, §3.7, “Bulk Operations”
- RFC 7643, §5, “Service Provider Configuration Schema”
