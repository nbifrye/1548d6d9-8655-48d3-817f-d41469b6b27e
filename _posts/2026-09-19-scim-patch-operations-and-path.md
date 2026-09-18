---
layout: post
title: "RFC 7644：SCIM PATCH の add / remove / replace と path はどう処理されるか"
date: 2026-09-19 06:41:00 +0900
categories: [SCIM]
tags: [SCIM, RFC7644, PATCH]
---

- **記事タイプ:** Feature Deep Dive
- **対象読者:** SCIM Service Provider / Client 実装者
- **この記事で伝えること:** RFC 7644 の PATCH request が `Operations` をどの順序で適用し、`path` が `add` / `remove` / `replace` の対象をどう指定するか。
- **扱わないこと:** PUT による resource 全体の置換、Bulk、認証方式、個別製品の実装方法。

## Article brief

- **Reader:** SCIM Service Provider / Client 実装者。
- **Question:** `add` / `remove` / `replace` で `path` の必須性と処理結果はどう変わるか。複数 operation はどの順序で評価されるか。
- **Answer:** PATCH request の共通構造、`path` の選択規則、3 operation の意味、逐次適用と atomicity を RFC 7644 の規定に沿って説明する。
- **Scope:** RFC 7644 §3.5.2–§3.5.2.3。
- **Out of scope:** PUT、Bulk、Filter endpoint、認証・認可、deployment 固有の設計。
- **Primary sources:** [RFC 7644 §3.5.2](https://www.rfc-editor.org/rfc/rfc7644.html#section-3.5.2)、§3.5.2.1、§3.5.2.2、§3.5.2.3。
- **Diagram:** PATCH request 内の operation が同一 resource に逐次適用される処理を縦方向の flowchart で示す。

## PATCH request の共通構造

RFC 7644 §3.5.2 では HTTP PATCH を OPTIONAL な server function とし、SCIM resource の1つ以上の attribute を `add`、`remove`、`replace` の operation sequence で部分更新できるものとしています。Service Provider が PATCH をサポートするかどうかは `/ServiceProviderConfig` で discovery できます。

PATCH request body は `schemas` に `urn:ietf:params:scim:api:messages:2.0:PatchOp` を含めなければなりません（MUST）。また、1つ以上の PATCH operation を格納する `Operations` array を含めなければなりません（MUST）。各 operation object は `op` member をちょうど1つ持たなければならず（MUST）、その値には `add`、`remove`、`replace` のいずれかを指定できます（MAY）。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "replace",
      "path": "name.familyName",
      "value": "Jensen"
    }
  ]
}
```

## `path` は更新対象を指定する

RFC 7644 §3.5.2 の `path` は operation の対象 attribute を表す文字列です。構文は次の規則で定義されています。

```text
PATH = attrPath / valuePath [subAttr]
```

`attrPath`、`valuePath`、`subAttr` の規則は RFC 7644 §3.4.2.2 で定義されています。`valuePath` を使うと、complex multi-valued attribute の特定の値を filter で選択できます。

例えば、`members` は attribute 全体、`name.familyName` は complex attribute の sub-attribute、`addresses[type eq "work"]` は filter に一致する multi-valued attribute の値を対象にします。

`path` は `add` と `replace` では OPTIONAL、`remove` では REQUIRED です（RFC 7644 §3.5.2）。

## `add` operation

RFC 7644 §3.5.2.1 では、`add` は既存 resource に新しい attribute value を追加する operation です。operation は追加する値を指定する `value` member を含めなければなりません（MUST）。

`path` を省略した場合、target は resource 自体となり、`value` に resource へ追加する attribute 群を指定します。`path` が multi-valued attribute を指す場合は新しい値が追加されます。single-valued attribute を指す場合は既存値が置換されます。

指定した値が target にすでに存在する場合、resource を変更せず success response を返すべきです（SHOULD）。他の operation による変更がなければ、この operation は resource の modify timestamp を変更してはなりません（SHALL NOT）。

## `remove` operation

RFC 7644 §3.5.2.2 の `remove` は、必須の `path` が示す target location の値を削除します。

single-valued attribute を指定すると、その attribute と値が削除され、attribute は unassigned とみなされます。multi-valued attribute を filter なしで指定すると、その attribute の全値が削除されます。`valuePath` の filter を指定すると、一致した値または complex record が削除対象になります。

`path` を指定しなければ operation は失敗し、Service Provider は HTTP 400 と `scimType` の `noTarget` を返します。

## `replace` operation

RFC 7644 §3.5.2.3 の `replace` は、`path` が示す target location の値を置換します。

`path` を省略すると target は resource 自体となり、`value` は置換対象となる1つ以上の attribute を含みます（SHALL）。single-valued attribute を指定するとその値を置換し、multi-valued attribute を filter なしで指定すると全値を置換します。

指定した target attribute が存在しない場合、Service Provider は operation を `add` として扱います（SHALL）。`valuePath` filter が multi-valued attribute のどの record にも一致しない場合は、HTTP 400 と `scimType` の `noTarget` を返します（SHALL）。

## 複数 operation は順番に適用される

1つの PATCH request に複数の operation がある場合、RFC 7644 §3.5.2 は array に現れる順序で operation を逐次適用すると規定しています。各 operation の結果となる resource が、次の operation の target になります。

<pre class="mermaid">
flowchart TD
    A[PATCH request] --> B[Operations の先頭]
    B --> C[現在の resource に operation を適用]
    C --> D{成功したか}
    D -->|Yes| E{次の operation があるか}
    E -->|Yes| C
    E -->|No| F[PATCH 成功]
    D -->|No| G[元の resource を復元]
    G --> H[Failure response]
</pre>

PATCH request は operation 数にかかわらず atomic に扱われます（SHALL）。1つの operation で error condition が発生した場合、元の SCIM resource を復元しなければならず（MUST）、failure status を返します（SHALL）。

## 成功時の response

すべての operation が成功した場合、Service Provider は resource 全体を response body に含む HTTP 200 を返さなければならない（MUST）か、適切な response header とともに HTTP 204 を返すことができます（MAY）。ただし request に `attributes` parameter が指定されている場合は HTTP 200 を返さなければなりません（MUST）。

## 一次資料

- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
  - §3.5.2 Modifying with PATCH
  - §3.5.2.1 Add Operation
  - §3.5.2.2 Remove Operation
  - §3.5.2.3 Replace Operation
