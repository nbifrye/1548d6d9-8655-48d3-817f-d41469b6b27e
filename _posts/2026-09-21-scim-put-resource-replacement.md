---
layout: post
title: "SCIM の PUT：resource replacement と attribute mutability"
date: 2026-09-21 13:39:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Flow
- Reader: SCIM 2.0 の resource replacement を実装またはレビューする Client / Service Provider 開発者
- Question: PUT で既存 resource を置換するとき、各 attribute は mutability に応じてどのように処理され、required attribute や省略された readWrite attribute はどう扱われるのか
- Answer: PUT の対象 URI、create には使えないこと、readWrite/writeOnly/immutable/readOnly の処理、required attribute、省略値、成功 response の規則を区別できる
- Scope: RFC 7644 §3.5.1 の PUT による単一 resource replacement と、RFC 7643 §2.2, §7 の mutability / required characteristics
- Out of scope: PATCH、resource creation、Bulk Operations、conditional request / ETag、個別 User/Group attribute の意味、authorization policy
- Primary sources: RFC 7644 §3.5.1; RFC 7643 §2.2, §7
- Diagram: PUT request から mutability ごとの attribute 処理、replacement、response までを示す flowchart
-->

## この記事について

**記事タイプ:** Flow  
**対象読者:** SCIM 2.0 の resource replacement を実装またはレビューする Client / Service Provider 開発者  
**この記事で伝えること:** `PUT` による既存 resource の置換と、attribute の `mutability` / `required` に応じた処理  
**扱わないこと:** PATCH、resource creation、Bulk Operations、conditional request / ETag、個別 User/Group attribute の意味、authorization policy

SCIM の `PUT` は、既存 resource の attribute を置換するための operation です。RFC 7644 §3.5.1 は、Client が resource 全体を取得して変更した後、その resource を `PUT` で置換する例を示しています。

**PUT is a replacement operation, but replacement is still evaluated attribute by attribute according to the schema.**  
（PUT は置換 operation ですが、置換処理は schema に従って attribute ごとに評価されます。）

## 1. PUT は既存 resource の URI に送る

RFC 7644 §3.5.1 では、SCIM resource identifier は Service Provider が割り当てるため、HTTP `PUT` を新しい resource の作成に使用してはならない（MUST NOT）と定めています。

以下は配置を示す**非規範的な例**です。identifier と attribute value は illustrative value です。

```http
PUT /Users/illustrative-user-id HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "illustrative.user@example.com",
  "displayName": "Illustrative User"
}
```

`PUT` の request body は、置換後の resource を表す JSON object です。SCIM resource representation は `schemas` attribute を含めなければなりません（MUST、RFC 7643 §2.1）。

## 2. mutability ごとに処理が異なる

RFC 7644 §3.5.1 は、PUT の intent が全 attribute の置換であるため、Client が mutability にかかわらずすべての attribute を送ることを MAY としています。そのうえで Service Provider は attribute ごとに次の規則を適用します。

### readWrite / writeOnly

Client が値を指定した `readWrite` または `writeOnly` attribute は、既存値を置換します（SHALL、RFC 7644 §3.5.1）。

`readWrite` attribute が request body から省略された場合、Service Provider はその値が Client から asserted されていないものとして扱うことができます（MAY）。既存値を消去すると仮定することも、最終 representation に default value を割り当てることも MAY です。Service Provider は、Client が resource のすべての attribute に access できるか、または理解しているかを考慮して、省略された attribute を削除するか default にするかを判断できます（MAY、§3.5.1）。

Client が Service Provider の default を上書きして値を明示的に消去したい場合、single-valued attribute には `null`、multi-valued attribute には空配列 `[]` を指定できます（MAY、§3.5.1）。

### immutable

既存値が設定済みの `immutable` attribute に値を指定する場合、その値は既存値と一致しなければなりません（MUST、RFC 7644 §3.5.1）。一致しない場合、Service Provider は HTTP `400` と `scimType` の `mutability` を返すべきです（SHOULD）。

Service Provider に既存値がない場合、新しい値を適用します（SHALL、§3.5.1）。

### readOnly

Client が `readOnly` attribute を送信しても、Service Provider はその値を無視します（SHALL、RFC 7644 §3.5.1）。RFC 7643 §7 も `readOnly` attribute は変更してはならない（SHALL NOT）と定義しています。

## 3. required attribute は PUT request に必要

attribute が `required` の場合、Client は PUT request にその attribute を指定しなければなりません（MUST、RFC 7644 §3.5.1）。

`required` は schema が attribute ごとに定義する characteristic です。RFC 7643 §2.2 では、個別定義で別途指定されない場合の default は `false` です。

## 4. null と空配列で値を明示的に消去できる

以下は、single-valued `displayName` と multi-valued `emails` の値を明示的に消去する配置を示す**非規範的な部分例**です。

```json
{
  "displayName": null,
  "emails": []
}
```

`null` は single-valued attribute、`[]` は multi-valued attribute に対応します。この指定は、RFC 7644 §3.5.1 が Client に認めている、Service Provider の default を上書きして値を clear する方法です。

## 5. 成功時は通常 200 と resource representation を返す

RFC 7644 §3.5.1 は、別途指定がない限り、成功した PUT operation が `200 OK` と response body 内の resource 全体を返すと定めています。これにより Client は、送信した representation と Service Provider が返した representation を対応付けられます。

以下は**非規範的な response 例**です。

```http
HTTP/1.1 200 OK
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "illustrative-user-id",
  "userName": "illustrative.user@example.com",
  "displayName": "Illustrative User"
}
```

`id` は Service Provider が割り当てる `readOnly` attribute であり、Client が指定するものではありません（RFC 7643 §3.1）。ここでは response representation の配置を示すために含めています。

## 6. PUT replacement の処理順序

<pre class="mermaid">
flowchart TD
    A[Client: PUT resource URI] --> B[Service Provider: attribute を評価]
    B --> C[readWrite / writeOnly]
    B --> D[immutable]
    B --> E[readOnly]
    C --> F[指定値で置換 / 省略値を規則に従い処理]
    D --> G[既存値との一致を確認]
    E --> H[Client 指定値を無視]
    F --> I[resource replacement]
    G --> I
    H --> I
    I --> J[通常 200 + resource representation]
</pre>

この図は RFC 7644 §3.5.1 の attribute-by-attribute replacement を整理したものです。storage 内部の処理や追加の actor は表していません。

## 7. 仕様上の境界

PUT replacement の中心となる規範要件は次のとおりです。

- `PUT` は新規 resource の作成に使用してはなりません（MUST NOT、RFC 7644 §3.5.1）。
- 指定された `readWrite` / `writeOnly` の値は既存値を置換します（SHALL、§3.5.1）。
- 設定済みの `immutable` attribute に指定する値は既存値と一致しなければなりません（MUST、§3.5.1）。
- `readOnly` attribute に Client が指定した値は無視します（SHALL、§3.5.1）。
- `required` attribute は PUT request に指定しなければなりません（MUST、§3.5.1）。

省略された `readWrite` attribute を消去するか default value にするかについて、RFC 7644 §3.5.1 は Service Provider に選択肢を認めています。この記事では、そのいずれかを推奨しません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.5.1
- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §2.1, §2.2, §3.1, §7
