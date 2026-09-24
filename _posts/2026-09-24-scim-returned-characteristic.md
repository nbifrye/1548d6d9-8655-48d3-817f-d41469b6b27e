---
layout: post
title: "SCIM の returned：always / never / default / request の意味"
date: 2026-09-24 23:46:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Requirement
- Reader: SCIM 2.0 の schema を定義・実装・レビューし、attribute が response に含まれる条件を正確に把握したい開発者
- Question: returned の always / never / default / request はそれぞれ何を意味し、attributes parameter とどう関係するのか
- Answer: RFC 7643 が定義する4つの returned keyword と default、RFC 7644 が定義する partial representation との関係を区別できる
- Scope: RFC 7643 §2.2, §7 の returned characteristic、RFC 7644 §3.9 の attributes / excludedAttributes との関係
- Out of scope: mutability、User.password 固有の要件、filter semantics、各 resource attribute 固有の returned 設定、authorization policy
- Primary sources: RFC 7643 §2.2, §7; RFC 7644 §3.9
- Diagram: returned keyword と response inclusion rule の関係を縦方向に整理する flowchart
-->

## この記事について

**記事タイプ:** Requirement  
**対象読者:** SCIM 2.0 の schema を定義・実装・レビューし、attribute が response に含まれる条件を正確に把握したい開発者  
**この記事で伝えること:** `returned` の4つの keyword、default、および `attributes` / `excludedAttributes` との関係  
**扱わないこと:** `mutability`、`User.password` 固有の要件、filter semantics、各 resource attribute 固有の `returned` 設定、authorization policy

SCIM の `returned` は、attribute とその value が GET response、または PUT / POST / PATCH response にいつ含まれるかを示す schema characteristic です。RFC 7643 §7 は `always`、`never`、`default`、`request` の4つを定義しています。

**The `returned` characteristic controls response inclusion; it does not define whether the attribute can be modified.**  
（`returned` characteristic は response への包含条件を定めるものであり、attribute を変更できるかどうかを定めるものではありません。）

## 1. returned は Schema resource の attribute definition に置かれる

RFC 7643 §7 の Schema resource では、`returned` は各 attribute definition の JSON member です。値は single-valued string で、canonical values は `always`、`never`、`default`、`request` です。

以下は配置と構造だけを示す**非規範的な例**です。attribute name は illustrative value です。

```json
{
  "name": "illustrativeAttribute",
  "type": "string",
  "multiValued": false,
  "required": false,
  "returned": "request"
}
```

この `returned` は resource instance の attribute value ではなく、その attribute の response inclusion behavior を記述する schema definition の member です。

RFC 7643 §2.2 は、別途指定がない場合の `returned` を `default` としています。

## 2. always

RFC 7643 §7 では、`always` の attribute は `attributes` parameter の内容にかかわらず常に返されます。`id` が例として示されています。

RFC 7644 §3.9 は、`returned` が `always` の attribute を minimum attribute set と定義しています。`excludedAttributes` を指定した場合も、minimum set は response に含まれます。

## 3. never

`never` の attribute は返されません（RFC 7643 §7）。仕様は、その理由の例として、元の attribute value が service provider に保持されていない場合を挙げています。

RFC 7643 §7 は、service provider が `never` の attribute を search filter で使用できるようにしてもよいとしています（**MAY**）。これは response への返却とは別の規則です。

## 4. default

`default` の attribute は、attribute value を返す SCIM operation response で default として返されます（RFC 7643 §7）。RFC 7644 §3.9 は、この集合を default attribute set としています。

GET request で `attributes` parameter が指定された場合、`default` の attribute value は、その attribute が `attributes` に指定されている場合にのみ返されます（RFC 7643 §7）。

RFC 7644 §3.9 では、`attributes` が指定されると default list が置き換えられ、各 resource は minimum set と明示的に要求された attribute / sub-attribute を含まなければなりません（**SHALL** / **MUST**）。

## 5. request

`request` の attribute は、PUT / POST / PATCH operation で client がその attribute を指定した場合に response に含まれます（RFC 7643 §7）。SCIM query operation では、`attributes` parameter に指定された場合にのみ返されます。

**`request` ties return behavior to client selection or submission; it is distinct from the default attribute set.**  
（`request` は client による選択または送信に返却条件を結び付けるもので、default attribute set とは別です。）

## 6. GET の attributes / excludedAttributes との関係

以下は parameter の配置を確認するための**非規範的な例**です。RFC 7644 §3.9 に従い、`attributes` は URL query parameter に置かれます。

```http
GET /Users/2819c223-7f76-453a-919d-413861904646?attributes=userName
Host: example.com
Accept: application/scim+json
```

この例で `attributes=userName` は、default list を置き換える selection です。RFC 7644 §3.9 により、response の各 resource は minimum set と、明示的に要求された `userName` を含みます。

`excludedAttributes` も URL query parameter です。指定した場合、response は minimum set に加え、default set から指定された attribute を除いた集合を返します。RFC 7644 §3.9 は `attributes` と `excludedAttributes` を mutually exclusive としています。

## 7. 4つの keyword の関係

<pre class="mermaid">
flowchart TD
    A[Schema attribute definition] --> B[returned]
    B --> C[always]
    B --> D[never]
    B --> E[default: default]
    B --> F[request]
    C --> G[minimum set]
    D --> H[返さない]
    E --> I[default set]
    F --> J[client の指定に応じて返す]
</pre>

この図は RFC 7643 §2.2, §7 と RFC 7644 §3.9 の関係だけを整理したものです。

## 8. 仕様上の境界

- `always`: `attributes` parameter の内容にかかわらず返される（RFC 7643 §7）。RFC 7644 §3.9 では minimum set を構成します。
- `never`: attribute value は返されません（RFC 7643 §7）。search filter での使用を service provider が許可してもよい（**MAY**、§7）。
- `default`: attribute value を返す operation response で default として返されます。GET の `attributes` 指定時は、明示的に指定された場合に返されます（RFC 7643 §7）。
- `request`: PUT / POST / PATCH では client が指定した場合、query operation では `attributes` に指定した場合に返されます（RFC 7643 §7）。

これらは attribute の returnability の規則です。変更可能性を定める `mutability` や、個別 attribute の意味とは混在させません。

## 一次資料

- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §2.2, §7
- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.9
