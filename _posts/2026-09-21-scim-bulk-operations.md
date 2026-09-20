---
layout: post
title: "RFC 7644：SCIM Bulk Operations は複数のリソース操作をどう1回の request にまとめるのか"
date: 2026-09-21 00:40:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7644, Bulk]
---

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM 2.0 の Service Provider / Client を実装・レビューし、`/Bulk` request と response の構造を確認したい開発者  
**この記事で伝えること:** RFC 7644 の Bulk Operations で、複数の POST / PUT / PATCH / DELETE を1つの request に格納し、各 operation の結果を response で対応付ける方法  
**扱わないこと:** 個々の User / Group schema、PATCH の add / remove / replace semantics、filter、RFC 9967 の asynchronous request / Security Event Token

## Article brief

- **Reader:** SCIM Bulk Endpoint を実装・レビューする Client / Service Provider 開発者
- **Question:** `/Bulk` にはどの JSON 構造で複数 operation を送り、作成前の resource を `bulkId` でどう参照し、結果をどう受け取るのか
- **Answer:** `BulkRequest` / `BulkResponse`、`Operations`、`method` / `path` / `bulkId` / `data`、`failOnErrors`、response の `status` / `location` の役割と配置を追える
- **Scope:** RFC 7644 §3.7–§3.7.4 の同期 Bulk Operations
- **Out of scope:** 個々の resource operation の詳細 semantics、RFC 9967 の asynchronous Bulk Endpoint request
- **Primary sources:** RFC 7644 §3.7–§3.7.4、RFC 7643 §5
- **Diagram:** Client が `/Bulk` に複数 operation を POST し、Service Provider が operation ごとの結果を返す処理

SCIM Bulk Operations は optional server feature です。RFC 7644 §3.7 は、Client が複数の resource operation を単一 request で送信できる仕組みとして Bulk を定義しています。Service Provider が Bulk をサポートするかどうかは Service Provider Configuration から確認できます。

## 1. Bulk request は `/Bulk` への POST

RFC 7644 §3.7 の Bulk Endpoint は `POST` を使用します。request body は SCIM JSON で、schema URI は `urn:ietf:params:scim:api:messages:2.0:BulkRequest` です。

<pre class="mermaid">
flowchart TD
    C[SCIM Client] -->|POST /Bulk| SP[Service Provider]
    SP --> O1[Operation 1]
    SP --> O2[Operation 2]
    O1 --> R[BulkResponse]
    O2 --> R
    R --> C
</pre>

Bulk request 内の各 operation は、resource endpoint に対する単独の HTTP request に対応します。使用できる method は `POST`、`PUT`、`PATCH`、`DELETE` です。

## 2. `BulkRequest` の最小構造

次は配置と構造を示すための**非規範的な例**です。identifier と値は illustrative value です。

```http
POST /Bulk HTTP/1.1
Host: scim.example
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:BulkRequest"
  ],
  "Operations": [
    {
      "method": "POST",
      "path": "/Users",
      "bulkId": "user-1",
      "data": {
        "schemas": [
          "urn:ietf:params:scim:schemas:core:2.0:User"
        ],
        "userName": "alice@example.test"
      }
    },
    {
      "method": "DELETE",
      "path": "/Users/illustrative-user-id"
    }
  ]
}
```

主要 member は次のとおりです。

- `schemas`: Bulk request の schema URI を含みます。
- `Operations`: REQUIRED の complex multi-valued attribute です。各要素が1つの resource operation を表します。
- `method`: REQUIRED。`POST` / `PUT` / `PATCH` / `DELETE` のいずれかです。
- `path`: operation の対象 resource の relative path です。
- `bulkId`: `POST` operation では REQUIRED です。Client が bulk request 内で新規 resource を識別する transient identifier です。
- `data`: `POST` / `PUT` / `PATCH` で resource data を運びます。

## 3. `bulkId` は作成前の resource を参照する

RFC 7644 §3.7 は、`POST` で新しく作成する resource に Client が `bulkId` を割り当てる仕組みを定義しています。`bulkId` は bulk request 内で一意な surrogate identifier です。

同じ bulk request 内の別 operation から新規 resource を参照する場合、値の先頭に `bulkId:` を付けます。例えば `bulkId` が `user-1` なら、参照値は `bulkId:user-1` です。

Service Provider は resource が作成された後、この参照を permanent resource id に置き換えなければなりません（MUST, RFC 7644 §3.7.2）。また、作成した resource に対応する同じ `bulkId` を response で返さなければなりません（MUST, §3.7）。

## 4. Service Provider は operation の順序を最適化できる

Service Provider は受信した operation の処理順序を最適化してもよい（MAY, RFC 7644 §3.7）とされています。ただし、その場合も Client の intent を保持し、最適化しなかった場合と同じ stateful result を実現しなければなりません（MUST）。

RFC 7644 §3.7.1 は circular cross-reference について、Service Provider が解決を試みなければならない（MUST）と規定しています。解決に失敗した後は処理を停止し、HTTP 409 Conflict を返してもよい（MAY）としています。

## 5. `failOnErrors` は停止までに許容する error 数を示す

`failOnErrors` は request では OPTIONAL の integer です。Service Provider が operation の処理を終了して error response を返すまでに受け入れる error 数を指定します。response では有効ではありません。

次は member の配置だけを示す非規範的な断片です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:BulkRequest"
  ],
  "failOnErrors": 1,
  "Operations": []
}
```

この例の `1` は illustrative value です。

## 6. `BulkResponse` は処理した operation ごとの結果を返す

RFC 7644 §3.7.3 により、Service Provider の response は処理済みのすべての operation の結果を含めなければなりません（MUST）。Bulk response の schema URI は `urn:ietf:params:scim:api:messages:2.0:BulkResponse` です。

次は response structure を示す**非規範的な例**です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:BulkResponse"
  ],
  "Operations": [
    {
      "method": "POST",
      "bulkId": "user-1",
      "location": "https://scim.example/Users/illustrative-id",
      "status": "201"
    },
    {
      "method": "DELETE",
      "location": "https://scim.example/Users/illustrative-user-id",
      "status": "204"
    }
  ]
}
```

RFC 7644 §3.7.3 は、failed POST を除く operation について resource endpoint を含む `location` を返すことを MUST としています。`status` は、その operation を単独の HTTP request として実行した場合に返される HTTP response code を含みます。error の場合、status に加えて error response information が返されます。

## 7. operation 数と payload size には Service Provider の上限がある

RFC 7644 §3.7.4 は、Service Provider が単一 Bulk request で Client が送信できる maximum operations と maximum payload size を定義しなければならない（MUST）と規定しています。これらの limit は Service Provider Configuration から取得できる場合があります（MAY）。

Client がどちらかの limit を超えた場合、Service Provider は HTTP 413 Payload Too Large を返さなければなりません（MUST）。response body では、超過した limit を示さなければなりません（MUST）。

## 8. Service Provider Configuration との関係

RFC 7643 §5 の Service Provider Configuration Resource には `bulk` complex attribute があり、Bulk Operations の support と上限を公開できます。

この metadata は Client が Bulk support と limits を確認するためのものです。本記事では `/ServiceProviderConfig` 自体の取得・検証を独立テーマとして展開せず、Bulk Operations に直接必要な関係だけを扱います。

## 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)

参照した主要節: RFC 7644 §3.7, §3.7.1, §3.7.2, §3.7.3, §3.7.4; RFC 7643 §5  
最終確認: 2026-09-21
