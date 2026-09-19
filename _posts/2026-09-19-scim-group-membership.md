---
layout: post
title: "RFC 7643 / 7644：SCIM Group membership はどこに表現し、どう更新するのか"
date: 2026-09-19 20:42:00 +0900
categories: [provisioning, scim]
---

SCIM 2.0 では、Group membership は Group resource の `members` と User resource の `groups` の両方に現れます。ただし、両者の mutability は同じではありません。RFC 7643 は、membership の変更を Group resource に適用するモデルを定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Client / Service Provider で Group membership の同期を実装・レビューする開発者  
**この記事で伝えること:** Group resource の `members` と User resource の `groups` の役割、member の参照構造、および Group resource に対する PATCH で membership を追加・削除する位置  
**扱わないこと:** Group membership が認可に与える意味、Service Provider 固有の role / entitlement、SCIM PATCH 全般の網羅的解説、resource 検索の filter grammar、Bulk operation

## 1. membership は Group resource の `members` で更新する

RFC 7643 §4.2 は Group resource を `urn:ietf:params:scim:schemas:core:2.0:Group` で識別し、`members` を multi-valued attribute として定義しています。

`members` の各値は complex value です。この記事のテーマに必要な sub-attribute は次のとおりです。

- **`value`:** member となる SCIM resource の `id`。RFC 7643 §4.2 は、`members.value` が SCIM resource の `id` の値を含むと定義しています。
- **`$ref`:** member となる SCIM resource の URI。User だけでなく Group を参照することもできます。
- **`display`:** human-readable な表示値。membership を識別する主体は `value` / `$ref` であり、RFC 7644 の Group PATCH 例では `display` は optional とされています。

RFC 7643 §4.2 では、`members` の値は追加または削除できます（MAY）が、member value の sub-attributes は `immutable` です。また Group resource は nested group を Service Provider がサポートできるように設計されており、member の `$ref` は User または Group などの SCIM resource を参照できます。

次は構造を示すための**非規範的な例**です。値は illustrative value です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:Group"
  ],
  "id": "group-001",
  "displayName": "Example Team",
  "members": [
    {
      "value": "user-001",
      "$ref": "https://example.com/scim/v2/Users/user-001",
      "display": "Example User"
    }
  ]
}
```

## 2. User resource の `groups` は更新先ではない

RFC 7643 §4.1 は User resource に `groups` attribute を定義しています。これは、その User が直接 membership、nested group、または動的計算によって属する Group の一覧を表します。

一方、`groups` の mutability は `readOnly` です。RFC 7643 §4.1 は、Group membership の変更を Group resource に適用しなければならない（MUST）と規定しています。

Service Provider が Group resource を公開している場合、User の `groups` に含まれる `value` は対応する Group resource の `id` でなければならず（MUST）、`$ref` は対応する Group resource の URI でなければなりません（MUST）。

RFC 7643 §4.1 は `groups.type` の canonical value として `direct` と `indirect` を定義しています。direct は User が Group に直接関連付けられている membership、indirect は transitive または dynamically calculated な membership を表します。direct membership は Client が Group resource を通じて変更できることを示すべきです（SHOULD）。indirect membership は Group resource を通じて直接変更できないことを示しますが、direct membership の変更が indirect membership に影響する場合があります。

次は User 側の表現を示すための**非規範的な例**です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User"
  ],
  "id": "user-001",
  "userName": "user001@example.com",
  "groups": [
    {
      "value": "group-001",
      "$ref": "https://example.com/scim/v2/Groups/group-001",
      "display": "Example Team",
      "type": "direct"
    }
  ]
}
```

この `groups` object は membership の参照を表しますが、Client が User resource の `groups` を書き換えて membership を変更する構造ではありません。

## 3. Group と User の関係

<pre class="mermaid">
flowchart TD
    U[User resource]
    UG[groups: readOnly]
    G[Group resource]
    GM[members]
    P[PATCH Group]

    U --> UG
    UG --> G
    G --> GM
    P --> GM
    GM --> U
</pre>

図の `User.groups` は membership の User 側の表現です。変更操作は Group resource の `members` に対して行います。

## 4. member を追加する PATCH

RFC 7644 §3.5.2 は Group に member を追加する PATCH の例を示しています。HTTP method は `PATCH`、request の `Content-Type` は `application/scim+json`、request body は `PatchOp` schema の JSON object です。

次は配置と構造を示すための**非規範的な例**です。URI、resource ID、表示名は illustrative value です。

```http
PATCH /scim/v2/Groups/group-001 HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "add",
      "path": "members",
      "value": [
        {
          "value": "user-002",
          "$ref": "https://example.com/scim/v2/Users/user-002",
          "display": "Another User"
        }
      ]
    }
  ]
}
```

ここでは `members` が JSON request body の PATCH operation にある `path` です。追加する member は同じ operation の `value` array に置かれます。

RFC 7644 §3.5.2.1 では、multi-valued attribute に値を追加するとき、新しい値は既存 resource の値へ追加されます。target location に指定した値がすでに存在する場合は resource を変更せず、success response を返すべきです（SHOULD）。他の operation による変更がない限り、その operation は modify timestamp を変更してはなりません（SHALL NOT）。

## 5. 特定の member を削除する PATCH

RFC 7644 §3.5.2.2 は、value selection filter を含む `path` を使って Group から特定 member を削除する例を示しています。

次も**非規範的な例**です。

```http
PATCH /scim/v2/Groups/group-001 HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "remove",
      "path": "members[value eq \"user-002\"]"
    }
  ]
}
```

この request では、削除対象を `members` の `value` sub-attribute で選択しています。RFC 7644 §3.5.2.2 によれば、multi-valued attribute に complex filter を指定した場合、sub-attribute に基づいて一致した record が削除されます。

RFC 7644 の Group member 削除例は、指定した User がその Group の member でなかった場合、resource を変更せず success response を返すべきである（SHOULD）としています。

## 6. membership の意味は Service Provider が定義する

RFC 7643 §4.2 は、Group resource が一般的な group-based または role-based access control model を表現できるようにする一方、明示的な authorization model 自体は定義していません。membership の意味や、membership によってどの behavior / authorization が与えられるかは Service Provider が定義する事項であり、RFC 7643 の scope 外です。

したがって SCIM の標準仕様から確認できるのは、membership の resource representation と protocol operation です。特定の Group membership がどの permission を付与するかは、この仕様からは決まりません。

## まとめ

SCIM の Group membership では、表現と更新先を分けて読む必要があります。

- Group resource の `members` は member の一覧で、各 member は `value` に SCIM resource ID、`$ref` に resource URI を持てます。
- User resource の `groups` は `readOnly` です。membership の変更は Group resource に適用しなければなりません（MUST、RFC 7643 §4.1）。
- direct / indirect は User の membership がどのように導出されたかを表します。
- member の追加・削除は Group resource に対する PATCH で表現できます。RFC 7644 §3.5.2 は `members` を対象にした具体例を定義しています。
- Group membership が authorization 上で何を意味するかは SCIM 2.0 の仕様では定義されません。

## 一次資料

- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)
- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)

参照した主要節: RFC 7643 §4.1, §4.2, §8.4 / RFC 7644 §3.5.2, §3.5.2.1, §3.5.2.2  
最終確認: 2026-09-19
