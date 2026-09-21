---
layout: post
title: "SCIM の resource deletion：DELETE 後に何が保証されるか"
date: 2026-09-21 12:47:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Flow
- Reader: SCIM 2.0 の resource deletion を実装またはレビューする Client / Service Provider 開発者
- Question: DELETE request が成功したとき、response と削除後の resource に対して SCIM は何を要求するのか
- Answer: DELETE の配置、204 response、削除後の operation に対する 404、query result からの除外、conflict calculation の規則を区別できる
- Scope: RFC 7644 §3.2, §3.6 に定義された単一 resource の DELETE と削除後の observable behavior
- Out of scope: Bulk DELETE、/Me alias、authorization policy、resource versioning の一般論、物理削除と論理削除の実装方式
- Primary sources: RFC 7644 §3.2, §3.6
- Diagram: DELETE 成功後の response と、その後の GET / query に対する observable behavior を示す flowchart
-->

## この記事について

**記事タイプ:** Flow  
**対象読者:** SCIM 2.0 の resource deletion を実装またはレビューする Client / Service Provider 開発者  
**この記事で伝えること:** `DELETE` が成功した場合の response と、削除後の resource に対して SCIM が要求する observable behavior  
**扱わないこと:** Bulk DELETE、`/Me` alias、authorization policy、resource versioning の一般論、物理削除と論理削除の実装方式

SCIM では、Client は resource endpoint に対する HTTP `DELETE` で resource の削除を要求します。RFC 7644 §3.6 は、Service Provider が resource を物理的に永久削除すること自体は要求していません。一方、削除後に Client から観測される振る舞いには明示的な要件があります。

**Deletion semantics are defined by observable protocol behavior, not by a required storage strategy.**  
（削除 semantics は、特定の保存方式ではなく、protocol 上観測される振る舞いによって定義されます。）

## 1. DELETE は個別 resource URI に送る

RFC 7644 §3.2 は `DELETE` を resource を削除する HTTP method として定義し、`/Users` と `/Groups` の resource に対する DELETE を §3.6 に対応付けています。

以下は配置を示す**非規範的な例**です。resource identifier は説明用です。

```http
DELETE /Users/illustrative-user-id HTTP/1.1
Host: example.com
Accept: application/scim+json
```

request body はありません。RFC 7644 §3.6 の例には `If-Match` も含まれますが、resource versioning と conditional request の詳細はこの記事では扱いません。

## 2. 成功時は 204 No Content

RFC 7644 §3.6 は、DELETE が成功した場合、Service Provider が HTTP status code `204 No Content` を返すことを SHALL としています。

以下は**非規範的な response 例**です。

```http
HTTP/1.1 204 No Content
```

`204 No Content` であるため、この成功 response に resource representation を示す response body はありません。

## 3. 永久削除しない実装も許される

RFC 7644 §3.6 により、Service Provider は resource を永久削除しないことを MAY とされています。したがって、仕様は storage 上の物理削除、論理削除など特定の実装方式を選択させません。

ただし、永久削除しない場合を含め、削除済み resource に関連するその後の operation には次の protocol behavior が要求されます。

## 4. 削除済み resource への operation は 404

Service Provider は、previously deleted resource に関連するすべての operation に `404 Not Found` を返さなければなりません（MUST、RFC 7644 §3.6）。

以下は削除後の取得を示す**非規範的な例**です。

```http
GET /Users/illustrative-user-id HTTP/1.1
Host: example.com
Accept: application/scim+json
```

```http
HTTP/1.1 404 Not Found
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "detail": "Resource illustrative-user-id not found",
  "status": "404"
}
```

JSON は RFC 7644 §3.6 の構造に沿った非規範的な例です。`detail` の文言と identifier は illustrative value です。

## 5. query result からも除外する

RFC 7644 §3.6 は、Service Provider が削除済み resource を future query results から除外することを MUST としています。

したがって、削除済み resource の URI に対する直接取得だけを 404 にするのではなく、後続の resource query にもその resource を含めないことが protocol 上要求されます。filter、sorting、pagination 自体の処理規則はこの記事の scope 外です。

## 6. conflict calculation での扱い

RFC 7644 §3.6 は、Service Provider が削除済み resource を conflict calculation で考慮しないことを SHOULD NOT としています。

仕様の例では、User resource を削除した後、以前と同じ `userName` を持つ User を CREATE した場合、削除済み resource との `userName` conflict を理由として `409 Conflict` にすべきではない（SHOULD NOT）とされています。

これは削除済み resource と新規 resource の識別子や属性値を再利用する一般的な policy を規定するものではありません。ここでの規範要件は、RFC 7644 §3.6 が示す conflict calculation に関するものです。

## 7. DELETE 後に観測される流れ

<pre class="mermaid">
flowchart TD
    A[Client: DELETE resource URI] --> B[Service Provider: resource removal]
    B --> C[204 No Content]
    C --> D[削除後]
    D --> E[resource への operation: 404]
    D --> F[future query: resource を除外]
    D --> G[conflict calculation: SHOULD NOT 考慮]
</pre>

この図は RFC 7644 §3.6 の DELETE 成功後の observable behavior を整理したものです。storage 内部の削除処理や追加の actor は表していません。

## 8. 仕様上の境界

DELETE について確認すべき規範要件は次のとおりです。

- Client は resource removal を `DELETE` で要求します（RFC 7644 §3.6）。
- Service Provider は resource を永久削除しない実装を選択できます（MAY、§3.6）。
- 成功した DELETE では `204 No Content` を返します（SHALL、§3.6）。
- previously deleted resource に関連するすべての operation には `404 Not Found` を返します（MUST、§3.6）。
- deleted resource は future query results から除外します（MUST、§3.6）。
- deleted resource は conflict calculation で考慮すべきではありません（SHOULD NOT、§3.6）。

SCIM が要求するのはこれらの protocol 上の結果です。Service Provider 内部で resource をどのように保持または削除するかは、RFC 7644 §3.6 が一つの方式に固定していません。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.2, §3.6
