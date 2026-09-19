---
layout: post
title: "RFC 9396：authorization_details は認可要求をどう表現するのか"
date: 2026-09-19 02:47:00 +0900
categories: [authorization, oauth]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth 2.0 の Authorization Server / Client で Rich Authorization Requests を実装・レビューする開発者  
**この記事で伝えること:** RFC 9396 の `authorization_details` が JSON object の配列として細粒度の authorization requirements を表し、`type` が各 object の意味と許可される field を決めること、および OAuth Authorization Request での配置  
**扱わないこと:** Token Request / Token Response での `authorization_details`、JWT Access Token や Token Introspection への伝達、個別 API の authorization details type の設計、PAR や JAR の詳細、特定業界の authorization model

## 1. `authorization_details` は authorization requirements を JSON で表す

RFC 9396 §2 は、`authorization_details` request parameter を JSON object の配列として定義しています。各 object は、ある resource type に対する authorization requirements を表します。

各 object の `type` field は、その object が表す resource type または access requirement の識別子です。`type` は string であり REQUIRED です（RFC 9396 §2）。`type` の値によって、その object で許可される内容が決まります。

`authorization_details` array には、同じ `type` の entry を複数含めてもかまいません（MAY, §2）。

RFC 9396 §2.1 では、`type` value の解釈と、その `type` の object で許可する field を Authorization Server が制御するとしています。RFC 9396 自体が、すべての API に共通する個別の authorization model を定義するわけではありません。

## 2. 共通 field は再利用可能な構成要素として定義されている

RFC 9396 §2.2 は、API type をまたいで利用できる common data field を定義しています。ただし、API definition にこれらの field の使用を要求してはいません。許容される値は、保護対象 API と `type` の定義によって決まります。

- **`locations`:** resource または Resource Server の location を表す string の array。
- **`actions`:** resource に対して行う action の種類を表す string の array。
- **`datatypes`:** resource に要求する data の種類を表す string の array。
- **`identifier`:** API で利用可能な特定 resource を示す string identifier。
- **`privileges`:** resource に要求する privilege の種類または level を表す string の array。

次は RFC 9396 §2.2 の構造に沿った非規範的な例です。値は構造を示すための illustrative value です。

```json
[
  {
    "type": "customer_information",
    "locations": ["https://example.com/customers"],
    "actions": ["read"],
    "datatypes": ["contacts"]
  }
]
```

この例では、`authorization_details` の値そのものが array であり、その中に1つの authorization details object があります。`type` は object の意味を識別し、`locations`、`actions`、`datatypes` は §2.2 の common data field です。

RFC 9396 §2.2 では、複数の common data field を組み合わせた場合、object が表す permission はそれらの値の積として解釈されます。たとえば複数の `actions`、`locations`、`datatypes` を1つの object に含める場合、その object は列挙されたすべての組み合わせを要求します。

## 3. Authorization Request では form encoding された request parameter として送る

RFC 9396 §3 は、RFC 6749 の Authorization Request で `authorization_details` を使用する場合、serialized JSON を `application/x-www-form-urlencoded` 形式で encode して request parameter として送ることを定義しています。

次は配置を確認するための非規範的な例です。まず、form encoding 前の JSON value は次の形です。

```json
[
  {
    "type": "customer_information",
    "actions": ["read"],
    "locations": ["https://example.com/customers"]
  }
]
```

実際の Authorization Request では、この JSON serialization を form encoding した値が query parameter の `authorization_details` に置かれます。

```http
GET /authorize?response_type=code&client_id=illustrative-client&authorization_details=%5B%7B%22type%22%3A%22customer_information%22%2C%22actions%22%3A%5B%22read%22%5D%2C%22locations%22%3A%5B%22https%3A%2F%2Fexample.com%2Fcustomers%22%5D%7D%5D HTTP/1.1
Host: authorization.example
```

この HTTP example は非規範的です。`illustrative-client` などの値に規範的意味はありません。ここで確認する点は、`authorization_details` が JSON request body の member ではなく、RFC 6749 の Authorization Request の文脈では serialized JSON を form encoding した request parameter であることです（RFC 9396 §3）。

<pre class="mermaid">
flowchart TD
    A[Client が authorization details を構成]
    B[JSON array に serialize]
    C[form encoding]
    D[Authorization Request の parameter]
    E[AS が type と内容を処理]
    A --> B
    B --> C
    C --> D
    D --> E
</pre>

## 4. `scope` と同時に使う場合は両方を処理する

RFC 9396 §3.1 は、`authorization_details` と `scope` を同じ Authorization Request で独立した authorization requirements のために使用できるとしています。

同じ request に両方がある場合、Authorization Server は両方の requirements を組み合わせて処理しなければなりません（MUST, §3.1）。どのように組み合わせるかは保護対象 API 固有であり、RFC 9396 の scope 外です。

Resource Owner から consent を取得する場合、Authorization Server は request が表す requirements の統合された集合を提示しなければなりません（MUST, §3.1）。

RFC 9396 §3.1 は、1つの API について requirement specification の形式を1つだけ使用することを RECOMMENDED としています。これは `authorization_details` と `scope` を同一 request で併用できないという意味ではありません。

## 5. 不明または不正な authorization details は拒否する

RFC 9396 §5 は、Authorization Server が unknown authorization details type、またはその type definition に適合しない authorization details の処理を拒否しなければならない（MUST）と規定しています。

次のいずれかに該当する場合、Authorization Server は処理を中止し、`invalid_authorization_details` error を Client に返さなければなりません（MUST, §5）。

- unknown な `type` value を含む。
- known type だが unknown field を含む。
- field の型がその authorization details type に対して誤っている。
- field value がその authorization details type に対して invalid である。
- その authorization details type で required とされた field が欠けている。

したがって、`type` は単なる表示用 label ではありません。Authorization Server が object の許容構造と意味を判断する基点になります。

## 6. Authorization Response 自体には extension を追加しない

RFC 9396 §4 は Authorization Response に extension を定義していません。この記事のテーマは Authorization Request で `authorization_details` が何を表し、どのように配置されるかまでです。

Token Request での authorization details の指定、Token Response で granted authorization details を返す規則、Resource Server への伝達方法は RFC 9396 §6–§9 の別の処理であり、ここでは扱いません。

## 一次資料

- RFC Editor: [RFC 9396 — OAuth 2.0 Rich Authorization Requests](https://www.rfc-editor.org/rfc/rfc9396.html)

参照した主要節: §1, §2, §2.1, §2.2, §3, §3.1, §4, §5  
最終確認: 2026-09-19
