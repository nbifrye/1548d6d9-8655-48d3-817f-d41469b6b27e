---
layout: post
title: "SCIM bulkId：Bulk request 内で新規 resource を相互参照する"
date: 2026-09-23 09:44:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** SCIM 2.0 の Bulk operation で、同じ request 内に新規 resource の作成とその resource への参照を含める Client / Service Provider の実装者  
**この記事で伝えること:** `bulkId` が新規 resource の一時識別子としてどこに置かれ、別 operation の resource data からどのように参照され、作成後の permanent resource id にどのように置換されるか  
**扱わないこと:** Bulk request 全体の構造と処理上限、`failOnErrors`、Bulk response 全般、circular reference、非同期 response、個々の resource operation の一般的な処理規則

## Article brief

- **Reader:** SCIM 2.0 の1つの Bulk request 内で、まだ permanent id がない新規 resource を別の operation から参照する Client / Service Provider の実装者
- **Question:** 新規 resource の permanent id が未確定の時点で、同じ Bulk request 内の別 operation はその resource をどのように参照するのか
- **Answer:** POST operation の `bulkId`、参照値の `bulkId:` prefix、Service Provider による permanent resource id への置換、response での同じ `bulkId` の返却という対応関係を確認できる
- **Scope:** RFC 7644 §3.7 および §3.7.2 の `bulkId` temporary identifier と cross-reference
- **Out of scope:** RFC 7644 §3.7.1 の circular reference processing、§3.7.3 の response/error handling 全般、§3.7.4 の limits、RFC 9967 の asynchronous response
- **Primary sources:** RFC 7644 §3.7、§3.7.2
- **Diagram:** Client が `bulkId` を付けた POST と、その `bulkId:` reference を含む別 operation を送り、Service Provider が作成後の permanent resource id に置換する flowchart

## 1. `bulkId` は Bulk request 内の transient identifier

RFC 7644 §3.7 は `bulkId` を、Client が作成する transient identifier と定義しています。`method` が `POST` の operation では `bulkId` は REQUIRED です。同じ Bulk request 内で一意であり、新規 resource を response で識別したり、request 内の operation 間で相互参照したりするための surrogate resource id として使われます。

`bulkId` は Service Provider が最終的に割り当てる resource `id` そのものではありません。

## 2. `bulkId` の配置

`bulkId` は BulkRequest の `Operations` 配列に含まれる POST operation object の member として置かれます。

以下は配置と cross-reference を確認するための**非規範的な例**です。host、`bulkId`、`userName`、`displayName` は illustrative value です。

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
      "bulkId": "illustrative-user",
      "data": {
        "schemas": [
          "urn:ietf:params:scim:schemas:core:2.0:User"
        ],
        "userName": "illustrative-user@example.com"
      }
    },
    {
      "method": "POST",
      "path": "/Groups",
      "bulkId": "illustrative-group",
      "data": {
        "schemas": [
          "urn:ietf:params:scim:schemas:core:2.0:Group"
        ],
        "displayName": "Illustrative Group",
        "members": [
          {
            "value": "bulkId:illustrative-user"
          }
        ]
      }
    }
  ]
}
```

この例では、最初の POST operation の `bulkId` は `illustrative-user` です。2つ目の operation は Group の `members[].value` に `bulkId:illustrative-user` を置き、まだ permanent resource id が確定していない User を参照しています。

## 3. 参照値には `bulkId:` を付ける

RFC 7644 §3.7.2 は、新規 resource を参照するための surrogate id value に literal `bulkId:` を前置することを要求しています。たとえば POST operation の `bulkId` が `illustrative-user` なら、別 operation の resource data 内の参照値は `bulkId:illustrative-user` です。

同 section の例では、新規 User を作成し、その User を同じ Bulk request で作成する Group の member に追加するために、この形式を使用しています。

複数の新規 resource を区別する場合、Client は各 request に異なる `bulkId` value を指定します（RFC 7644 §3.7.2）。

## 4. Service Provider は permanent resource id に置換する

RFC 7644 §3.7.2 により、Service Provider は `bulkId:` で表された surrogate reference を、resource が作成された後の permanent resource id に置換しなければなりません（**MUST**）。

RFC 7644 §3.7 は、Service Provider が operation の順序を最適化することを認めています（**MAY**）。ただし最適化する場合、Client の intent を保持し、最適化しない処理と同じ stateful result を達成しなければなりません（**MUST**）。仕様は、User を Group に追加するには User が先に作成される必要がある例を示しています。

内部でどのような依存関係グラフ、queue、transaction を使うかは、これらの要件では規定されていません。

## 5. response でも同じ `bulkId` を対応付ける

RFC 7644 §3.7 は、新規 resource を作成した場合、Service Provider が同じ `bulkId` を作成済み resource とともに返さなければならないことを規定しています（**MUST**）。これにより Client は、自身が付けた transient identifier と Service Provider が割り当てた resource id を対応付けられます。

本記事では BulkResponse の他の member や error handling は扱いません。

## 6. cross-reference の処理関係

<pre class="mermaid">
flowchart TD
    A[POST operation<br/>bulkId: illustrative-user]
    B[Create User]
    C[Permanent User id]
    D[Another operation<br/>bulkId:illustrative-user]
    E[Replace surrogate reference]
    F[Reference permanent id]

    A --> B
    B --> C
    D --> E
    C --> E
    E --> F
</pre>

この図は RFC 7644 §3.7.2 の temporary identifier と replacement の関係だけを示しています。circular cross-reference の解決は §3.7.1 の別論点であり、本記事には含めません。

## 7. 仕様上の境界

`bulkId` は1つの Bulk request 内で新規 resource を識別し、cross-reference するための仕組みです。本記事の範囲の RFC 7644 は、`bulkId` を永続的な resource identifier として使用することや、Service Provider の内部 identifier 設計を定義していません。

また、cross-reference が循環する場合の処理は RFC 7644 §3.7.1 に独立した規則があります。本記事では通常の temporary identifier replacement に範囲を限定します。

## Primary sources

- RFC 7644, §3.7, “Bulk Operations”
- RFC 7644, §3.7.2, “\"bulkId\" Temporary Identifiers”
