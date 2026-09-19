---
layout: post
title: "SCIM 2.0：Group membership はどのように表現・更新されるのか"
date: 2026-09-20 07:45:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Client / Service Provider 実装者  
**この記事で伝えること:** SCIM 2.0 の Group membership が `Group.members` と `User.groups` でどう表現され、Client が membership を変更するときにどの resource を PATCH するのか  
**扱わないこと:** membership によって付与される権限、Service Provider 固有の group semantics、Bulk operation、PATCH 全般の網羅的解説

SCIM 2.0 では、Group membership の更新点は `Group` resource です。`User.groups` は membership を参照する read-only attribute であり、membership の変更には使用しません。

> **Article brief**
> - **Reader:** SCIM Client / Service Provider 実装者
> - **Question:** Group membership はどの JSON attribute で表現され、追加・削除するときはどの resource をどう更新するのか。
> - **Answer:** `Group.members` が更新可能な membership list であり、`User.groups` は read-only の参照であること、RFC 7644 の PATCH で member を追加・削除する構造を理解できる。
> - **Scope:** RFC 7643 の `Group.members` / `User.groups` と、RFC 7644 §3.5.2 の PATCH による membership 更新。
> - **Out of scope:** membership の authorization semantics、Bulk、filter grammar 一般、認証方式。
> - **Primary sources:** RFC 7643 §4.1.2 / §4.2、RFC 7644 §3.5.2。
> - **Diagram:** Group resource を更新点として示す flowchart。

## 1. Group membership の更新点は Group resource

RFC 7643 §4.1.2 は `User.groups` を、User が属する group の一覧として定義しています。direct membership、nested group による membership、動的に計算された membership を表現できます。

ただし `User.groups` の mutability は `readOnly` です。RFC 7643 §4.1.2 は、group membership の変更を **Group Resource に対して適用しなければならない（MUST）** と定めています。

一方、RFC 7643 §4.2 の `Group.members` は Group の member list です。member value は追加・削除できます（MAY）。各 member の sub-attribute 自体は `immutable` です。

<pre class="mermaid">
flowchart TD
    A[SCIM Client] -->|PATCH membership| B[Group resource]
    B --> C[Group.members]
    B --> D[User.groups に membership が反映され得る]
    D --> E[User.groups は readOnly]
</pre>

この図は仕様上の resource と attribute の関係を簡略化したものです。`User.groups` の値をどのように算出するかという Service Provider 内部処理を規定するものではありません。

## 2. `Group.members` の構造

RFC 7643 §4.2 では `members` を multi-valued complex attribute として定義します。各 member には、SCIM resource を指す sub-attribute を含められます。

- **`value`:** member となる SCIM resource の `id` の値。
- **`$ref`:** member となる SCIM resource の URI。`User` または `Group` などの SCIM resource を参照します。
- **`type`:** resource type を示す label。RFC 7643 の schema representation では canonical value として `User` と `Group` が定義されています。

`members` は 0..n 個の値を持つ multi-valued attribute です。`members` 自体の mutability は `readWrite`、その `value` / `$ref` / `type` sub-attribute は `immutable` と定義されています（RFC 7643 §4.2、§8.7.1）。

次は構造だけを示す**非規範的な例**です。値は説明用です。

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Example Group",
  "members": [
    {
      "value": "user-123",
      "$ref": "https://example.com/v2/Users/user-123",
      "type": "User"
    }
  ]
}
```

RFC 7643 §4.2 は nested group を表現できるよう、`$ref` が `Group` resource を指す場合も想定しています。ただし、membership がどのような権限や動作を生じさせるかは Service Provider が定義する事項であり、RFC 7643 の scope 外です。

## 3. `User.groups` は参照用の read-only attribute

RFC 7643 §4.1.2 の `User.groups` も multi-valued complex attribute です。Service Provider が `Group` resource を公開する場合、`value` は対応する Group resource の `id` でなければなりません（MUST）。`$ref` は対応する Group resource の URI です。

次は**非規範的な最小例**です。

```json
{
  "groups": [
    {
      "value": "group-456",
      "$ref": "https://example.com/v2/Groups/group-456",
      "type": "direct"
    }
  ]
}
```

`User.groups.type` には canonical type として `direct` と `indirect` が定義されています。RFC 7643 §4.1.2 は、direct membership は Client が Group resource を通じて変更できることを示すべき（SHOULD）とし、indirect membership は transitive または dynamic な membership を示します。

## 4. member を追加する PATCH

RFC 7644 §3.5.2 は resource の部分更新に HTTP PATCH を使用します。PATCH request body の media type は `application/scim+json` です。

次は member を1件追加する**非規範的な例**です。

```http
PATCH /v2/Groups/group-456 HTTP/1.1
Host: example.com
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "add",
      "path": "members",
      "value": [
        {
          "value": "user-123",
          "$ref": "https://example.com/v2/Users/user-123",
          "type": "User"
        }
      ]
    }
  ]
}
```

配置は次のとおりです。

- HTTP method: `PATCH`
- request target: 更新対象の `/Groups/{id}`
- `Content-Type`: `application/scim+json`
- request body: JSON object
- `schemas`: PATCH message schema URI を持つ JSON member
- `Operations`: operation object の array
- `op`: この例では `add`
- `path`: この例では `members`
- `value`: 追加する member object の array

RFC 7644 §3.5.2.1 では、target が multi-valued attribute の場合、`add` で指定された値を既存値の集合へ追加します。指定値がすでに存在する場合は変更を行わず、成功 response を返すべきです（SHOULD）。他の operation による変更がなければ、その operation は resource の modify timestamp を変更してはなりません（SHALL NOT）。

## 5. member を1件削除する PATCH

RFC 7644 §3.5.2 では `remove` operation の `path` は REQUIRED です。multi-valued complex attribute では value filter を使って対象 member を選択できます。

次は `value` が `user-123` の member を削除する**非規範的な例**です。

```http
PATCH /v2/Groups/group-456 HTTP/1.1
Host: example.com
Content-Type: application/scim+json

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "remove",
      "path": "members[value eq \"user-123\"]"
    }
  ]
}
```

RFC 7644 §3.5.2.2 は、value filter が multi-valued attribute の値に一致した場合、その一致した値を削除するよう定めています。RFC 7644 の Group member 削除例では、対象 User がその Group の member でなかった場合、resource を変更せず success response を返すべき（SHOULD）としています。

`"path": "members"` とすれば、RFC 7644 §3.5.2.2 の例のように Group の全 member を削除する操作も表現できます。

## 6. `replace` で member list 全体を置き換える場合

RFC 7644 §3.5.2.3 は `replace` operation を定義しています。`path` が `members` を指し、`value` に member array を指定すれば、`members` attribute の値を置き換えられます。

次は**非規範的な例**です。

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "members",
      "value": [
        {
          "value": "user-789",
          "$ref": "https://example.com/v2/Users/user-789",
          "type": "User"
        }
      ]
    }
  ]
}
```

ここでも更新対象は Group resource です。`User.groups` を PATCH して membership を変更するものではありません。

## 7. SCIM は membership の authorization semantics を定義しない

RFC 7643 §4.2 は Group resource が group-based / role-based access control model を表現するためのものだと説明していますが、明示的な authorization model は定義していません。membership の意味や、それによってどの behavior / authorization が与えられるかは Service Provider が定義する事項です。

したがって、SCIM の Group membership の仕様から「この Group に所属すれば特定の権限を得る」といった authorization rule を導くことはできません。

## まとめ

SCIM 2.0 の Group membership では、更新可能な中心データは `Group.members` です。`members` は multi-valued complex attribute で、member の SCIM resource `id` を `value` に、resource URI を `$ref` に表現できます。

一方、`User.groups` は read-only です。RFC 7643 §4.1.2 に従い、membership の変更は Group resource に対して行います。RFC 7644 §3.5.2 の PATCH では、`add`、`remove`、`replace` を使って `members` を部分更新できます。

**The writable membership edge is represented on the Group resource; `User.groups` is a read-only view of group membership.**  
（更新可能な membership の関係は Group resource 上で表現され、`User.groups` は group membership の read-only な表現です。）

## 一次資料

- RFC 7643, *System for Cross-domain Identity Management: Core Schema*, §4.1.2, §4.2, §8.4, §8.7.1
- RFC 7644, *System for Cross-domain Identity Management: Protocol*, §3.5.2, §3.5.2.1, §3.5.2.2, §3.5.2.3
