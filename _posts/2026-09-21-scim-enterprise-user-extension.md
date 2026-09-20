---
layout: post
title: "SCIM Enterprise User extension：組織属性と manager をどう表現するのか"
date: 2026-09-21 07:38:00 +0900
categories: [provisioning, scim]
tags: [SCIM, RFC7643, EnterpriseUser]
---

SCIM 2.0 の RFC 7643 は、企業や組織に属する User を表すための標準 schema extension として Enterprise User Schema Extension を定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM User resource に employee number、cost center、organization、manager などの企業向け属性を含める実装者  
**この記事で伝えること:** Enterprise User extension の schema URI、User resource 内での配置、定義済み attribute と `manager` の構造  
**扱わないこと:** Core User schema 全体、Group membership、独自 schema extension の設計方法、SCIM の HTTP operation や PATCH 処理

この記事は RFC 7643 §3.3 と §4.3 に基づき、Enterprise User extension の resource representation に範囲を限定します。

## Article brief

- **Reader:** SCIM Client / Service Provider で企業向け User attribute を交換する実装者
- **Question:** Enterprise User extension はどの schema URI を使い、User JSON のどこにどの attribute を配置するのか
- **Answer:** extension schema URI を `schemas` に示し、その URI を JSON container として企業向け attribute と `manager` を配置する構造を理解できる
- **Scope:** RFC 7643 §3.3, §4.3, §8.3 の Enterprise User Schema Extension と JSON representation
- **Out of scope:** Core User attribute の網羅、Group resource、独自 extension の登録、HTTP request / response operation、PATCH path
- **Primary sources:** RFC 7643 §3.3, §4.3, §8.3, §8.7.1
- **Diagram:** Core User schema に Enterprise User extension が additive に加わる JSON 構造

## 1. Enterprise User extension の schema URI

RFC 7643 §4.3 は、企業や組織に属する、またはそれらを代表して行動する User を表すための extension を定義しています。schema URI は次の値です。

`urn:ietf:params:scim:schemas:extension:enterprise:2.0:User`

RFC 7643 §3.3 では、SCIM resource type は core schema に加えて extension を持つことができます。extension は additive であり、継承モデルではありません。

Enterprise User extension を使用する User resource では、`schemas` に Core User schema と Enterprise User extension schema を含めます。

<pre class="mermaid">
flowchart TD
    A[User resource] --> B[Core User schema]
    A --> C[Enterprise User extension]
    C --> D[employeeNumber など]
    C --> E[manager]
</pre>

## 2. extension attribute は schema URI の JSON container に置く

RFC 7643 §3.3 は、base object schema を除く schema extension について、extension schema URI を JSON container として使用することを SHALL としています。

次は配置と構造を示すための**非規範的な例**です。値は illustrative value です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
  ],
  "userName": "user@example.com",
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "employeeNumber": "E-12345",
    "department": "Example Department"
  }
}
```

この例では、`schemas` は resource が使用する schema を示す JSON member です。Enterprise User の `employeeNumber` と `department` は、extension schema URI を名前とする JSON object の member として配置しています。

## 3. 定義されている singular attribute

RFC 7643 §4.3 は Enterprise User extension に次の singular attribute を定義しています。

- `employeeNumber`: 人に割り当てられる string identifier。通常は numeric または alphanumeric です。
- `costCenter`: cost center の名前を識別します。
- `organization`: organization の名前を識別します。
- `division`: division の名前を識別します。
- `department`: department の名前を識別します。
- `manager`: User の manager を表す complex attribute です。

RFC 7643 §8.7.1 の schema representation では、これらは `required: false`、`multiValued: false` と定義されています。`manager` 以外の5属性は `string`、`manager` は `complex` です。

## 4. `manager` は別の User resource を参照できる complex attribute

RFC 7643 §4.3 の `manager` は、別の User resource を参照して組織階層を表現できる complex attribute です。

`manager` には次の sub-attribute が定義されています。

- `value`: manager を表す SCIM User resource の `id`。RECOMMENDED です。
- `$ref`: manager を表す User resource の URI。RECOMMENDED です。
- `displayName`: manager の表示名。OPTIONAL で、mutability は `readOnly` です。

次は `manager` の配置を示すための**非規範的な例**です。identifier と URI は illustrative value です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
  ],
  "userName": "user@example.com",
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "manager": {
      "value": "manager-123",
      "$ref": "https://scim.example/v2/Users/manager-123"
    }
  }
}
```

この例では `displayName` を省略しています。RFC 7643 §4.3 で OPTIONAL とされているためです。

## 5. `schemas` と extension container の関係

RFC 7643 §3.3 により、`schemas` attribute は少なくとも1つの値を含み、そのうち1つは resource の base schema でなければなりません（SHALL）。追加の値として、使用中の extended schema を含めることができます（MAY）。

Enterprise User extension を resource representation に含める場合、extension の attribute は Core User の top-level member として混在させず、Enterprise User schema URI の JSON container の中に置かれます。

RFC 7643 §8.3 の非規範的な Enterprise User representation も、Core User schema と Enterprise User extension schema の両方を `schemas` に含め、企業向け attribute を extension URI の object に格納しています。

## 6. この extension が定義しないこと

Enterprise User extension は、企業向け User attribute の schema を定義します。User resource を作成・取得・更新する HTTP method や endpoint の処理は RFC 7644 の protocol scope であり、RFC 7643 §4.3 が別の operation semantics を定義するものではありません。

また、RFC 7643 §3.3 は一般的な schema extension mechanism も定義していますが、この記事では Enterprise User extension に定義済みの attribute と JSON representation だけを扱います。

## 一次資料

- RFC Editor: [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html)

参照した主要節: RFC 7643 §3.3, §4.3, §8.3, §8.7.1  
最終確認: 2026-09-21
