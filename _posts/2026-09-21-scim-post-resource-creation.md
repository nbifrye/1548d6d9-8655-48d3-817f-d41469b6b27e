---
layout: post
title: "SCIM の POST：resource creation と 201 Created response"
date: 2026-09-21 14:45:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Flow
- Reader: SCIM 2.0 の単一 resource creation を実装またはレビューする Client / Service Provider 開発者
- Question: POST で resource を作成するとき、request attribute はどのように処理され、成功時に id / meta / Location と response representation はどう返されるのか
- Answer: resource endpoint への POST、mutability に基づく request 処理、Service Provider による id / meta の割り当て、201 response、Location / meta.location、uniqueness conflict を区別できる
- Scope: RFC 7644 §3.3, §3.3.1 の単一 resource creation と、RFC 7643 §2.1, §3.1 の schemas / common attributes
- Out of scope: Bulk Operations、PUT / PATCH / DELETE、個別 User/Group attribute の詳細、authentication / authorization、ETag による conditional request
- Primary sources: RFC 7644 §3.3, §3.3.1; RFC 7643 §2.1, §3.1
- Diagram: resource endpoint への POST から attribute 処理、resource 作成、201 response までを示す flowchart
-->

## この記事について

**記事タイプ:** Flow  
**対象読者:** SCIM 2.0 の単一 resource creation を実装またはレビューする Client / Service Provider 開発者  
**この記事で伝えること:** `POST` による resource 作成時の request attribute の処理と、`201 Created`、`Location`、`id` / `meta` を含む response の関係  
**扱わないこと:** Bulk Operations、PUT / PATCH / DELETE、個別 User/Group attribute の詳細、authentication / authorization、ETag による conditional request

SCIM で新しい resource を作成する場合、Client は resource endpoint に HTTP `POST` を送ります。RFC 7644 §3.3 は、`/Users` や `/Groups` をその例として示しています。

**Creation is a POST to the resource endpoint; the Service Provider assigns the resource identity and returns the created resource location.**  
（resource 作成は resource endpoint への POST で行い、Service Provider が resource identity を割り当て、作成された resource の location を返します。）

## 1. POST は resource endpoint に送る

RFC 7644 §3.3 では、新しい resource を作成する Client は、対応する resource type の endpoint に HTTP `POST` request を送ります。endpoint は RFC 7644 §4 の ResourceType discovery で定義されます。

以下は配置を示す**非規範的な例**です。attribute value は illustrative value です。

```http
POST /Users HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "illustrative.user@example.com",
  "externalId": "illustrative-client-id"
}
```

request body は SCIM resource representation の JSON object です。RFC 7643 §2.1 により、SCIM resource representation は、その representation に含まれる schema を示す `schemas` attribute を含めなければなりません（MUST）。

## 2. request attribute は mutability に従って処理する

RFC 7644 §3.3 は、Service Provider が作成 request の attribute を mutability に従って処理することを SHALL としています。

`readOnly` attribute が request body に含まれている場合、Service Provider はその値を無視します（SHALL、RFC 7644 §3.3）。したがって、Client が `id` や `meta` を送ったとしても、それを resource identity や metadata の指定として扱うことはできません。RFC 7643 §3.1 では、`id` は Service Provider が発行し、Client が指定してはならない（MUST NOT）と定義されています。また `meta` は `readOnly` で、Client から指定された場合は無視します（SHALL）。

`readWrite` attribute が request body から省略された場合、Service Provider は Client がその attribute を asserted していないものとして扱うことができ（MAY）、最終 resource representation に default value を割り当てることもできます（MAY、RFC 7644 §3.3）。Client がすべての attribute に access できるかどうかを考慮して default の扱いを決めることも MAY です。

## 3. id と meta は Service Provider が割り当てる

RFC 7643 §3.1 は、Service Provider が resource を受け入れた後、`id` と `meta` およびその sub-attribute に値を割り当てなければならない（MUST）と定めています。

`id` は Service Provider が定義する resource の unique identifier です。各 resource representation は空でない `id` を含まなければならず（MUST）、その値は Service Provider 全体の resource set で unique、stable、non-reassignable でなければなりません（MUST、RFC 7643 §3.1）。

RFC 7644 §3.3.1 により、Service Provider は作成先 endpoint に対応する resource type を `meta.resourceType` に設定します（SHALL）。たとえば `/Users` への POST では `User`、`/Groups` への POST では `Group` です。

## 4. 成功時は 201 Created と resource location を返す

resource の作成に成功した場合、Service Provider は HTTP `201 Created` を返さなければなりません（SHALL、RFC 7644 §3.3）。response body には、Service Provider による新しい resource representation を含めるべきです（SHOULD）。

作成された resource の URI は HTTP `Location` header に含めなければなりません（SHALL）。同じ location は response body の `meta.location` にも表されます。RFC 7643 §3.1 は `meta.location` を返される resource の URI とし、`Content-Location` HTTP response header と同じ値でなければならない（MUST）と定義しています。

以下は配置を示す**非規範的な response 例**です。identifier、timestamp、URI は illustrative value です。

```http
HTTP/1.1 201 Created
Content-Type: application/scim+json
Location: https://example.com/Users/illustrative-user-id

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "illustrative-user-id",
  "userName": "illustrative.user@example.com",
  "externalId": "illustrative-client-id",
  "meta": {
    "resourceType": "User",
    "created": "2026-09-21T05:45:00Z",
    "lastModified": "2026-09-21T05:45:00Z",
    "location": "https://example.com/Users/illustrative-user-id"
  }
}
```

RFC 7644 §3.3 は、Service Provider が POST された内容を変更または無視できるため、作成後の full representation を返すことが Client と Service Provider の view を対応付けるうえで有用だと説明しています。ただし response body の resource representation は SHOULD であり、ここでは MUST に読み替えません。

## 5. uniqueness conflict は 409 になる

Service Provider が、作成しようとした resource が既存 resource と conflict すると判断した場合、たとえば `userName` が重複する場合、HTTP `409 Conflict` と `scimType` の `uniqueness` を返さなければなりません（MUST、RFC 7644 §3.3）。

以下は response structure の配置を示す**非規範的な例**です。

```http
HTTP/1.1 409 Conflict
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "409",
  "scimType": "uniqueness"
}
```

この例は conflict 時の protocol structure を示すもので、どの attribute にどの uniqueness constraint を設定するかを追加で定義するものではありません。

## 6. resource creation の流れ

<pre class="mermaid">
flowchart TD
    A[Client: POST resource endpoint] --> B[Service Provider: attribute を評価]
    B --> C[readOnly 指定値を無視]
    B --> D[readWrite 値を処理]
    C --> E[resource を作成]
    D --> E
    E --> F[id / meta を割り当て]
    F --> G[201 Created]
    G --> H[Location + resource representation]
</pre>

この図は RFC 7644 §3.3 と §3.3.1 の creation flow を整理したものです。storage 内部の処理や仕様にない actor は表していません。

## 7. 仕様上の境界

resource creation の中心となる規範要件は次のとおりです。

- Client は新規 resource の作成に resource endpoint への `POST` を使用します（RFC 7644 §3.3）。
- Service Provider は request attribute を mutability に従って処理します（SHALL、§3.3）。
- request body の `readOnly` attribute は無視します（SHALL、§3.3）。
- resource を受け入れた後、Service Provider は `id` と `meta` に値を割り当てます（MUST、RFC 7643 §3.1）。
- 成功時は `201 Created` を返します（SHALL、RFC 7644 §3.3）。
- 作成された resource の URI は `Location` header に含めます（SHALL、§3.3）。
- endpoint に対応する `meta.resourceType` を Service Provider が設定します（SHALL、§3.3.1）。
- uniqueness conflict の場合は `409 Conflict` と `scimType: uniqueness` を返します（MUST、§3.3）。

Service Provider が省略された `readWrite` attribute に default value を割り当てるかどうかについて、RFC 7644 §3.3 は選択肢を認めています。この記事では、その一方を推奨しません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.3, §3.3.1
- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §2.1, §3.1
