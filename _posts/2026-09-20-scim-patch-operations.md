---
layout: post
title: "SCIM 2.0：PATCH の add / remove / replace と path はどう処理されるのか"
date: 2026-09-20 08:42:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM Service Provider を実装し、PATCH request の解釈と適用処理を確認したい開発者  
**この記事で伝えること:** RFC 7644 の SCIM PATCH における `Operations`、`op`、`path`、`value` の配置と、`add` / `remove` / `replace` の処理規則  
**扱わないこと:** Group membership 固有のデータモデル、PUT による resource 全体の置換、Bulk operation、filter grammar 全体、認証・認可方式

## Article brief

- **Reader:** SCIM Service Provider の PATCH 処理を実装する開発者
- **Question:** `add` / `remove` / `replace` は `path` が示す target に対してどのように処理され、複数 operation はどの順序と単位で適用されるのか
- **Answer:** PATCH document の必須構造、`path` の位置と形式、3 operation の target 別 semantics、逐次適用と atomicity を RFC 7644 の規則に沿って判別できる
- **Scope:** RFC 7644 §3.5.2–§3.5.2.3 の PATCH request と処理規則
- **Out of scope:** Group membership の schema semantics、PUT、Bulk、filter grammar の網羅的解説、認証・認可
- **Primary sources:** RFC 7644 §3.5.2–§3.5.2.3、RFC 7643 §2.2–§2.3
- **Diagram:** PATCH document を受け取り `Operations` を配列順に適用し、失敗時に元の resource を復元する処理を示す flowchart

## 1. SCIM PATCH の request 構造

RFC 7644 §3.5.2 では、HTTP PATCH は Service Provider の **OPTIONAL** な機能です。Client は Service Provider Configuration を取得して PATCH の support を確認できます。

PATCH request body は JSON で、`Content-Type` は `application/scim+json` です。request body の `schemas` は `urn:ietf:params:scim:api:messages:2.0:PatchOp` を含まなければなりません（MUST, RFC 7644 §3.5.2）。また `Operations` は1個以上の PATCH operation を含む array でなければならず（MUST）、各 operation object は `op` member をちょうど1個持たなければなりません（MUST）。`op` の値には `add`、`remove`、`replace` を使用できます（MAY）。

次は配置を示す**非規範的な例**です。値は説明用です。

```http
PATCH /Users/illustrative-user HTTP/1.1
Host: scim.example
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "replace",
      "path": "displayName",
      "value": "Illustrative Name"
    }
  ]
}
```

- `schemas`: request body の JSON member。PATCH message schema を示す。
- `Operations`: request body の JSON array。1個以上の operation を含む。
- `op`: operation object の JSON member。operation type を示す。
- `path`: operation object の JSON string。`add` と `replace` では OPTIONAL、`remove` では REQUIRED（RFC 7644 §3.5.2）。
- `value`: operation が適用する値。`add` では REQUIRED（§3.5.2.1）。`replace` でも replacement value を保持する。

## 2. `path` は何を指すのか

RFC 7644 §3.5.2 の ABNF は `path` を次のように定義します。

```text
PATH = attrPath / valuePath [subAttr]
```

`attrPath`、`valuePath`、`subAttr` 自体は RFC 7644 §3.4.2.2 で定義されています。`valuePath` を使うと、complex multi-valued attribute の特定 value を選択できます。

次は仕様で許される形を縮約した**非規範的な例**です。

```text
displayName
name.familyName
emails[type eq "work"]
emails[type eq "work"].value
```

SCIM PATCH は JSON Patch を基礎にしていますが、RFC 7644 §3.5.2 は array index を support せず、`move` のような array element manipulation operation も support しないと定めています。

各 attribute への operation は schema と mutability に適合しなければなりません（MUST, RFC 7644 §3.5.2）。たとえば Client は `readOnly` attribute や、すでに値を持つ `immutable` attribute を変更してはなりません（MUST NOT）。RFC 7643 §2.2 は `readOnly`、`readWrite`、`immutable`、`writeOnly` の mutability を定義しています。

## 3. `add` の処理

RFC 7644 §3.5.2.1 では、`add` operation は既存 resource に新しい attribute value を追加します。`add` operation は `value` member を含まなければなりません（MUST）。

`path` が省略された場合、target は resource 自体です。`value` に、resource に追加する attribute 群を指定します。

`path` が multi-valued attribute を指す場合は新しい value を追加します。single-valued attribute を指し、すでに value が存在する場合は既存 value を置換します。指定した value がすでに target に含まれる場合、resource を変更せず success response を返すべきです（SHOULD）。

次は**非規範的な例**です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "add",
      "path": "emails",
      "value": [
        {
          "value": "illustrative@example.com",
          "type": "work"
        }
      ]
    }
  ]
}
```

ここでは `emails` という multi-valued attribute が target です。

## 4. `remove` の処理

RFC 7644 §3.5.2.2 では、`remove` の `path` は REQUIRED です。`path` がない場合、Service Provider は HTTP 400 と `scimType` `noTarget` を返します。

single-valued attribute を target にすると、その attribute と value が削除され、attribute は unassigned とみなされます。multi-valued attribute を filter なしで target にすると、attribute の全 value が削除されます。value selection filter がある場合は、filter に一致する value が削除されます。

次は multi-valued attribute の特定 value を target にする**非規範的な例**です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "remove",
      "path": "emails[type eq \"work\"]"
    }
  ]
}
```

required attribute や read-only attribute が remove によって unassigned になる場合、Service Provider は RFC 7644 §3.12 の HTTP error response と `scimType` `mutability` を返します（SHALL, §3.5.2.2）。

## 5. `replace` の処理

RFC 7644 §3.5.2.3 の `replace` は target location の value を置換します。

`path` が省略された場合、target は resource 自体となり、`value` は置換する1個以上の attribute を含みます（SHALL）。single-valued attribute を target にするとその value を置換します。filter なしの multi-valued attribute を target にすると、attribute の全 value を置換します。

指定した target attribute が存在しない場合、Service Provider はその operation を `add` として処理します（SHALL）。value selection filter が1個以上の value に一致する場合は、一致した record values がすべて置換されます（SHALL）。filter が1件も一致しない場合は HTTP 400 と `scimType` `noTarget` を返します（SHALL）。

次は**非規範的な例**です。

```json
{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "replace",
      "path": "emails[type eq \"work\"].value",
      "value": "new-illustrative@example.com"
    }
  ]
}
```

## 6. 複数 operation は配列順に適用する

RFC 7644 §3.5.2 では、各 operation は同じ request URI が示す SCIM resource に対する1つの action です。Service Provider は `Operations` array に現れる順序で operation を逐次適用します。ある operation の結果となる resource が、次の operation の target になります。

<pre class="mermaid">
flowchart TD
    A[PATCH request] --> B[Operations を配列順に処理]
    B --> C[operation を target に適用]
    C --> D{成功?}
    D -->|Yes| E{次がある?}
    E -->|Yes| C
    E -->|No| F[PATCH 成功]
    D -->|No| G[元の resource を復元]
    G --> H[error response]
</pre>

PATCH request は operation の個数にかかわらず atomic に扱われます（SHALL, RFC 7644 §3.5.2）。1つの operation で error が発生した場合、元の SCIM resource を復元しなければなりません（MUST）。

成功時、Service Provider は resource 全体を response body に含む `200 OK` を返さなければならないか（MUST）、`204 No Content` と適切な response headers を返すことができます（MAY）。request に `attributes` parameter が指定されている場合は `200 OK` を返さなければなりません（MUST）。

## 7. 3つの operation を区別する要点

- **add:** value を追加する。multi-valued attribute では value を追加し、single-valued attribute の既存 value を target にした場合は置換になる。
- **remove:** `path` が必須。target の value を削除する。filter を使えば multi-valued attribute の一致 value を選択できる。
- **replace:** target の value を置換する。存在しない attribute は `add` として処理される。filter が指定され、target が見つからない場合は `noTarget` となる。

**A SCIM PATCH document is an ordered, atomic sequence of operations against one resource.**  
（SCIM PATCH document は、1つの resource に対して順序付きかつ atomic に適用される operation の列です。）

この性質により、各 operation を独立した request として解釈するのではなく、前の operation の結果を次の operation が受け取る、1つの PATCH request として処理されます。これは RFC 7644 §3.5.2 が定義する処理規則です。

## 一次資料

- RFC 7644, *System for Cross-domain Identity Management: Protocol*, §3.5.2, §3.5.2.1, §3.5.2.2, §3.5.2.3, §3.12  
  https://www.rfc-editor.org/rfc/rfc7644.html
- RFC 7643, *System for Cross-domain Identity Management: Core Schema*, §2.2–§2.3  
  https://www.rfc-editor.org/rfc/rfc7643.html
