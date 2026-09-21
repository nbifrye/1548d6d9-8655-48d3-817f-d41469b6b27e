---
layout: post
title: "SCIM の Error Response：status / scimType / detail の構造"
date: 2026-09-22 07:46:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Feature Deep Dive
- Reader: SCIM 2.0 の error response を実装またはレビューする Client / Service Provider 開発者
- Question: SCIM operation が失敗したとき、HTTP status と JSON error body はどのような構造で返され、status / scimType / detail は何を表すのか
- Answer: HTTP status と SCIM Error message の関係、Error schema URI、status / scimType / detail の型・必須性、代表的な scimType の意味を区別できる
- Scope: RFC 7644 §3.12 の HTTP status と SCIM Error response、および Table 9 の scimType
- Out of scope: 各 CRUD operation 固有の成功 response、BulkResponse 内の operation error、authentication / authorization の方式、Client の retry policy
- Primary sources: RFC 7644 §3.12, §8.2; RFC Editor verified erratum 7898
- Diagram: operation failure から HTTP status と SCIM Error JSON body を返すまでの関係を示す flowchart
-->

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM 2.0 の error response を実装またはレビューする Client / Service Provider 開発者  
**この記事で伝えること:** HTTP error status と SCIM Error JSON body の関係、および `status` / `scimType` / `detail` の構造  
**扱わないこと:** 各 CRUD operation 固有の成功 response、BulkResponse 内の operation error、authentication / authorization の方式、Client の retry policy

SCIM operation の失敗は HTTP status code だけでは表現されません。RFC 7644 §3.12 は、HTTP response code に加えて、error を JSON response body で返すことを要求しています。

**A SCIM error response combines an HTTP status code with a SCIM Error JSON message.**  
（SCIM の error response は、HTTP status code と SCIM Error JSON message を組み合わせて表現します。）

## 1. error は HTTP status と JSON body で返す

RFC 7644 §3.12 により、SCIM protocol は operation の成功または失敗を示すために HTTP response status code を使用します。error の場合、実装は HTTP response code に加えて、同 section で定義された attribute を使用する JSON body を返さなければなりません（MUST）。

SCIM Error message は次の schema URI で識別されます。

```text
urn:ietf:params:scim:api:messages:2.0:Error
```

この URI は RFC 7644 §8.2 でも Error Response の SCIM protocol message schema URI として登録されています。

## 2. Error JSON object の最小構造

以下は配置と構造を示す**非規範的な例**です。`detail` の文言は illustrative value です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "400",
  "scimType": "invalidSyntax",
  "detail": "Illustrative request syntax error."
}
```

RFC 7644 §3.12 が Error response に定義する attribute は次のとおりです。

- `status`: HTTP response status code を JSON **string** として表します。REQUIRED です。
- `scimType`: SCIM の detail error keyword です。OPTIONAL です。値は §3.12 Table 9 で定義されます。
- `detail`: human-readable な詳細 message です。OPTIONAL です。
- `schemas`: SCIM message を識別する schema URI の配列です。Error response では `urn:ietf:params:scim:api:messages:2.0:Error` を使用します。

したがって HTTP status line の `400` と JSON member の `"status": "400"` は配置も JSON 上の型も異なります。後者は number ではなく string です。

## 3. scimType は SCIM 固有の error keyword

`scimType` は HTTP status code を置き換えるものではなく、SCIM protocol 上の詳細な error condition を表す OPTIONAL member です。RFC 7644 §3.12 Table 9 は次の keyword を定義しています。

- `invalidFilter`: filter syntax が無効、または指定 filter が認識できない場合。
- `tooMany`: filter に一致する resource が多すぎて処理できない場合。
- `uniqueness`: attribute value が uniqueness requirement に違反する場合。
- `mutability`: immutable / readOnly attribute の変更など、mutability rule に違反する場合。
- `invalidSyntax`: request body の parse、syntax、schema に関する error。
- `invalidPath`: PATCH の path が無効、または対象 attribute path が存在しない場合。
- `noTarget`: PATCH path filter が対象を選択しない場合。
- `invalidValue`: value が不適切、または attribute の type / schema に適合しない場合。
- `invalidVers`: request された protocol version を Service Provider がサポートしない場合。
- `sensitive`: request が password など sensitive attribute の返却を要求した場合。

Table 9 は各 `scimType` に適用される HTTP status も示します。たとえば `uniqueness` は `400` または `409`、`mutability` は `400`、`invalidVers` は `400`、`sensitive` は `400` とされています。個別 operation がさらに具体的な status / scimType を規定する場合、その operation の規定も適用されます。

## 4. scimType と detail は常に必須ではない

RFC 7644 §3.12 では `status` は REQUIRED ですが、`scimType` と `detail` は OPTIONAL です。そのため、すべての SCIM error response に `scimType` や human-readable `detail` が存在すると仮定することは仕様上できません。

以下も構造上可能な**非規範的な最小例**です。

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "500"
}
```

この例は response structure だけを示しており、特定の failure cause や retry behavior を追加で定義するものではありません。

## 5. mutability error の例

RFC 7644 §3.12 には、readOnly の `id` を変更しようとした PUT request に対する `mutability` error の例があります。RFC Editor の verified erratum 7898 は、公開テキストの例で `"scimType":"mutability"` の後に comma が欠けていた点を訂正しています。

以下は、その構造を最小化した**非規範的な例**です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "scimType": "mutability",
  "detail": "Illustrative mutability error.",
  "status": "400"
}
```

`detail` は human-readable message であり、この例の文言自体に規範的意味はありません。

## 6. response の構成

<pre class="mermaid">
flowchart TD
    A[SCIM operation] --> B{成功か}
    B -->|失敗| C[HTTP error status]
    C --> D[SCIM Error JSON body]
    D --> E[status: REQUIRED]
    D --> F[scimType: OPTIONAL]
    D --> G[detail: OPTIONAL]
</pre>

この図は RFC 7644 §3.12 の error response structure を整理したものです。内部処理、retry、logging など仕様にない要素は表していません。

## 7. 仕様上の境界

SCIM Error response の中心となる要件は次のとおりです。

- operation の成功・失敗は HTTP response status code で示します（RFC 7644 §3.12）。
- error では HTTP response code に加え、定義された attribute を使用する JSON body を返します（MUST、§3.12）。
- `status` は HTTP status code を JSON string として表し、REQUIRED です（§3.12）。
- `scimType` は SCIM detail error keyword で、OPTIONAL です（§3.12）。
- `detail` は human-readable message で、OPTIONAL です（§3.12）。
- Error response は `urn:ietf:params:scim:api:messages:2.0:Error` で識別されます（§3.12、§8.2）。

どの failure に対してどの HTTP status や `scimType` を返すかについて個別 operation が規定している場合は、その規定を確認する必要があります。この記事では、Client の retry policy や運用上の error message 設計を推奨しません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.12, §8.2
- [RFC Editor Errata ID 7898 — RFC 7644 §3.12](https://www.rfc-editor.org/errata/eid7898)
