---
layout: post
title: "RFC 7644：SCIM PATCH の add / remove / replace はどう処理されるのか"
date: 2026-09-19 05:46:00 +0900
categories: [provisioning, scim]
---

SCIM Protocol の HTTP PATCH は、既存 resource の attribute を部分更新するための操作です。RFC 7644 §3.5.2 は、PATCH request を `add`、`remove`、`replace` の operation sequence として定義しています。

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Service Provider の PATCH 処理を実装・レビューする開発者  
**この記事で伝えること:** PATCH request の構造、`path` の対象指定、`add` / `remove` / `replace` の処理差、および複数 operation の適用方法  
**扱わないこと:** PUT による resource 全体の置換、Bulk operation、filter を使った resource 検索、Group membership のライフサイクル全体

## 1. PATCH request の基本構造

RFC 7644 §3.5.2 では、HTTP PATCH は Service Provider にとって OPTIONAL な機能です。Client は `/ServiceProviderConfig` を使って PATCH のサポートを確認できます。

PATCH request body は `schemas` に `urn:ietf:params:scim:api:messages:2.0:PatchOp` を含めなければなりません（MUST）。また、1個以上の PATCH operation を格納する `Operations` attribute を含めなければなりません（MUST）。

各 operation object は `op` member を正確に1つ持たなければならず（MUST）、その値には `add`、`remove`、`replace` のいずれかを指定できます（MAY）。

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

## 2. path は operation の対象を指定する

`path` は operation の対象となる attribute を示す文字列です。RFC 7644 §3.5.2 では、`path` は `add` と `replace` では OPTIONAL、`remove` では REQUIRED です。

path rule は次の形です。

```text
PATH = attrPath / valuePath [subAttr]
```

そのため、単一 attribute だけでなく、multi-valued attribute のうち filter に一致する値や、その sub-attribute まで対象にできます。RFC 7644 が示す形には `members`、`name.familyName`、`addresses[type eq "work"]` などがあります。

各 operation は RFC 7643 で定義される attribute の mutability と schema に適合しなければなりません（MUST）。たとえば Client は `readOnly` または `immutable` の attribute を変更してはなりません（MUST NOT）。ただし、値を持っていない `immutable` attribute には値を `add` できます（MAY）。

## 3. add

RFC 7644 §3.5.2.1 の `add` operation は、既存 resource に新しい attribute value を追加する操作です。operation は追加する内容を示す `value` member を含めなければなりません（MUST）。

`path` を省略した場合、target は resource 自体となり、`value` に含まれる attribute が resource に追加されます。

`path` が multi-valued attribute を指す場合は新しい value が追加されます。一方、single-valued attribute を指す場合、既存 value は置き換えられます。target attribute がまだ存在しない場合は、その attribute と value が追加されます。

すでに同じ value が存在する場合、resource を変更せず success response を返すべきです（SHOULD）。ほかの operation が resource を変更しない限り、この operation によって modify timestamp を変更してはなりません（SHALL NOT）。

## 4. remove

RFC 7644 §3.5.2.2 の `remove` operation は、必須の `path` が指定する target location の value を削除します。

single-valued attribute を対象にすると、その attribute と value が削除され、attribute は unassigned とみなされます。multi-valued attribute に filter を付けず指定すると、attribute のすべての value が削除されます。

valuePath の filter を使う場合は、一致する value だけを削除できます。complex multi-valued attribute では sub-attribute を条件に matching record を選択することもできます。

`path` がない `remove` は HTTP 400 と `scimType` の `noTarget` で失敗します。また、削除によって required attribute または read-only attribute が unassigned になる場合、Service Provider は §3.12 の error response を返し、`scimType` は `mutability` になります（SHALL）。

## 5. replace

RFC 7644 §3.5.2.3 の `replace` operation は、target location の value を新しい value に置き換えます。

`path` が指定されていない場合、`value` に含まれる attribute が resource 上の対応する attribute を置き換えます。`path` が存在しない target を指す場合、Service Provider は operation を `add` として扱います（SHALL）。

complex attribute を対象にする場合、`value` に指定された sub-attribute が既存値を置き換えるか、存在しなければ追加されます。`value` に指定されていない sub-attribute は変更されません。

multi-valued attribute に valuePath filter を指定し、1個以上の value が一致した場合は、matching record が置き換え対象になります。さらに sub-attribute を指定した path では、一致した record のその sub-attribute が置き換えられます。

valuePath filter が1件も一致しない場合、Service Provider は HTTP 400 と `scimType` の `noTarget` を返さなければなりません（SHALL）。

## 6. Operations は記載順に適用される

1つの PATCH request に複数の operation がある場合、RFC 7644 §3.5.2 はそれらを配列の順序で逐次適用すると定めています。各 operation の結果となる resource が、次の operation の target になります。

<pre class="mermaid">
flowchart TD
    A[PATCH request を受信] --> B[Operations の先頭を取得]
    B --> C[op と path を評価]
    C --> D[add / remove / replace を適用]
    D --> E{operation は成功したか}
    E -->|Yes| F{次の operation があるか}
    F -->|Yes| C
    F -->|No| G[PATCH 成功]
    E -->|No| H[元の resource を復元]
    H --> I[error response]
</pre>

PATCH request は operation 数にかかわらず atomic に扱われます（SHALL）。1つの operation で error が発生した場合、元の SCIM resource を復元しなければならず（MUST）、failure status を返します（SHALL）。

## 7. 成功時の response

すべての operation が成功した場合、Service Provider は resource 全体を response body に含む `200 OK` を返します（MUST）。代わりに、適切な response header とともに `204 No Content` を返すこともできます（MAY）。

ただし request に `attributes` parameter が指定されている場合、Service Provider は `200 OK` を返さなければなりません（MUST）。

## 8. 一次資料

- RFC Editor: [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html)
- RFC Editor: [RFC 7644 with inline errata](https://www.rfc-editor.org/rfc/inline-errata/rfc7644.html)

参照した主要節: §3.4.2.2, §3.5.2, §3.5.2.1, §3.5.2.2, §3.5.2.3, §3.10  
最終確認: 2026-09-19
