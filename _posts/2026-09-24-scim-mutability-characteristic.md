---
layout: post
title: "SCIM の mutability：readOnly / readWrite / immutable / writeOnly の意味"
date: 2026-09-24 22:41:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Requirement
- Reader: SCIM 2.0 の schema を定義・実装・レビューし、attribute の変更可能性を正確に把握したい開発者
- Question: mutability の readOnly / readWrite / immutable / writeOnly はそれぞれ何を意味し、指定がない場合は何になるのか
- Answer: RFC 7643 が定義する4つの mutability keyword、その規範的意味、default の readWrite、Schema resource 内での配置を区別できる
- Scope: RFC 7643 §2.2, §7 の mutability characteristic と Schema resource representation
- Out of scope: PUT / POST / PATCH 各 operation 固有の処理、returned characteristic の全規則、User.password 固有の要件、個別 attribute の mutability、authorization policy
- Primary sources: RFC 7643 §2.2, §7
- Diagram: Schema definition の mutability から4つの keyword とその意味を縦方向に整理する flowchart
-->

## この記事について

**記事タイプ:** Requirement  
**対象読者:** SCIM 2.0 の schema を定義・実装・レビューし、attribute の変更可能性を正確に把握したい開発者  
**この記事で伝えること:** `mutability` の4つの keyword と default、および Schema resource での配置  
**扱わないこと:** PUT / POST / PATCH 各 operation 固有の処理、`returned` characteristic の全規則、`User.password` 固有の要件、個別 attribute の mutability、authorization policy

SCIM の `mutability` は、attribute value をどのような状況で定義または再定義できるかを示す schema characteristic です。RFC 7643 §7 は `readOnly`、`readWrite`、`immutable`、`writeOnly` の4つを定義しています。

**Mutability describes when an attribute value can be defined or redefined; it does not describe the attribute's data type.**  
（mutability は attribute value をいつ定義・再定義できるかを表し、attribute の data type を表すものではありません。）

## 1. mutability は Schema resource の attribute definition に置かれる

RFC 7643 §7 の Schema resource では、`mutability` は各 attribute definition の JSON member です。`mutability` 自体は single-valued string で、canonical values は `readOnly`、`readWrite`、`immutable`、`writeOnly` です。

以下は配置と構造だけを示す**非規範的な例**です。attribute name は illustrative value です。

```json
{
  "name": "illustrativeAttribute",
  "type": "string",
  "multiValued": false,
  "required": false,
  "mutability": "immutable"
}
```

この例では、`mutability` は resource instance の `illustrativeAttribute` の値ではなく、その attribute を記述する schema definition の member です。

## 2. readOnly

RFC 7643 §7 は `readOnly` について、attribute を変更してはならないと定めています（**SHALL NOT**）。

`readOnly` は「Client から送られた値を各 operation で具体的にどう処理するか」という operation 固有の規則そのものではありません。たとえば PUT における処理は RFC 7644 §3.5.1 が別途定めますが、この記事では扱いません。

## 3. readWrite

`readWrite` attribute はいつでも update および read できます（**MAY**、RFC 7643 §7）。

RFC 7643 §2.2 は、別途指定がない場合の `mutability` を `readWrite` としています。RFC 7643 §7 も `readWrite` を default value と明記しています。

**If a schema does not state otherwise, the mutability characteristic is `readWrite`.**  
（schema に別の指定がなければ、mutability characteristic は `readWrite` です。）

## 4. immutable

`immutable` attribute は resource creation、または request による record replacement の際に定義できます（**MAY**、RFC 7643 §7）。一方、定義済みの attribute は update してはなりません（**SHALL NOT**、§7）。

ここでの規則は `immutable` characteristic 自体の意味です。PUT で既存値と異なる値が送られた場合など、個別 operation における validation / error processing はこの記事の Scope に含めません。

## 5. writeOnly

`writeOnly` attribute はいつでも update できます（**MAY**、RFC 7643 §7）。その attribute value を返してはなりません（**SHALL NOT**、§7）。

RFC 7643 §7 は、`writeOnly` attribute は通常 `returned` が `never` でもある、と注記しています。この記述は `writeOnly` の定義に付随する注記であり、この記事では `returned` の4つの keyword 全体には展開しません。

## 6. 4つの keyword の関係

<pre class="mermaid">
flowchart TD
    A[Schema attribute definition] --> B[mutability]
    B --> C[readOnly]
    B --> D[readWrite: default]
    B --> E[immutable]
    B --> F[writeOnly]
    C --> G[変更 SHALL NOT]
    D --> H[update / read MAY]
    E --> I[creation 等で定義 MAY<br/>定義後 update SHALL NOT]
    F --> J[update MAY<br/>value return SHALL NOT]
</pre>

この図は RFC 7643 §2.2 と §7 の定義関係だけを整理したものです。Client / Service Provider 間の operation sequence や、仕様にない actor は追加していません。

## 7. 仕様上の境界

`mutability` characteristic から直接読み取れる要件は次の範囲です。

- `readOnly`: attribute は変更してはならない（**SHALL NOT**、RFC 7643 §7）。
- `readWrite`: attribute はいつでも update / read できる（**MAY**、§7）。default は `readWrite`（§2.2, §7）。
- `immutable`: creation または record replacement で定義できる（**MAY**）が、定義後は update してはならない（**SHALL NOT**、§7）。
- `writeOnly`: attribute はいつでも update できる（**MAY**）が、value を返してはならない（**SHALL NOT**、§7）。

PUT / POST / PATCH がこれらの characteristic をどう適用するかは RFC 7644 の各 operation の規則です。この記事では `mutability` の schema-level definition と混在させません。

## 一次資料

- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §2.2, §7
