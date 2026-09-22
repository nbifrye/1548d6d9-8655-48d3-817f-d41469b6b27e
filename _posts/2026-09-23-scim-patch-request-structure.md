---
layout: post
title: "SCIM PATCH の request 構造：Operations と path を RFC 7644 で読む"
date: 2026-09-23 00:44:00 +0900
categories: [provisioning, scim]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** SCIM 2.0 の partial update を実装する Provisioning Client / Service Provider の開発者  
**この記事で伝えること:** RFC 7644 の PATCH request body の必須構造、`Operations` の処理順序、`op` / `path` / `value` の配置と、request 全体の atomicity  
**扱わないこと:** filter grammar の一般解説、PUT との比較、Bulk operation、認証方式、個別 schema の属性設計

## Article brief

- **Reader:** SCIM 2.0 の PATCH request を生成または処理する実装者
- **Question:** PATCH request body はどのような JSON 構造を持ち、複数 operation はどの順序と単位で適用されるのか
- **Answer:** `PatchOp` schema、`Operations` array、各 operation の `op` / `path` / `value`、逐次適用と atomicity を RFC 7644 の規定に沿って確認できる
- **Scope:** RFC 7644 §3.5.2 と §3.5.2.1–3.5.2.3 に定義された PATCH request と処理規則
- **Out of scope:** filter expression 全般、resource schema の詳細、PUT、Bulk、認証・認可
- **Primary sources:** RFC 7644 §3.5.2、§3.5.2.1、§3.5.2.2、§3.5.2.3。attribute mutability との関係について RFC 7643 §2.2、§2.3
- **Diagram:** Client から Service Provider への PATCH と、`Operations` の逐次適用・失敗時 rollback を示す flowchart

SCIM の PATCH は、1つの resource に対して複数の部分変更を1 request で表現します。RFC 7644 §3.5.2 では PATCH support 自体は Service Provider の OPTIONAL function です。Client は `/ServiceProviderConfig` の `patch` capability によって support を確認できます。

## 1. PATCH request body の最上位構造

RFC 7644 §3.5.2 により、request body は `schemas` と `Operations` を持ちます。

- `schemas`: `urn:ietf:params:scim:api:messages:2.0:PatchOp` を含めなければなりません（MUST）。
- `Operations`: 1個以上の PATCH operation を含む array でなければなりません（MUST）。
- 各 operation object: `op` member を正確に1個持たなければなりません（MUST）。`op` の値は `add`、`remove`、`replace` のいずれかです（MAY）。

以下は配置と構造を示す**非規範的な例**です。値は説明用です。

```http
PATCH /Users/2819c223-7f76-453a-919d-413861904646 HTTP/1.1
Host: example.com
Content-Type: application/scim+json
Accept: application/scim+json

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

`schemas` と `Operations` は JSON request body の member です。`op`、`path`、`value` は `Operations` array 内の各 operation object の member です。

## 2. `path` は operation の対象を指定する

RFC 7644 §3.5.2 では `path` は String であり、operation の対象となる attribute path を表します。`path` は `add` と `replace` では OPTIONAL、`remove` では REQUIRED です。

RFC 7644 の PATH rule は次の形です。

```text
PATH = attrPath / valuePath [subAttr]
```

`attrPath`、`valuePath`、`subAttr` の grammar は RFC 7644 §3.4.2.2 で定義されています。`valuePath` を使うと、complex multi-valued attribute の特定の値を対象にできます。

以下は RFC 7644 §3.5.2 の形式に沿った説明用の例です。

```json
{
  "op": "remove",
  "path": "emails[type eq \"work\"]"
}
```

この例では `path` が `remove` operation object の JSON member として置かれています。filter grammar 自体の詳細は本記事では扱いません。

## 3. `add` / `remove` / `replace` の構造上の違い

### `add`

RFC 7644 §3.5.2.1 の `add` は、既存 resource に新しい attribute value を追加します。`path` を省略した場合、`value` は追加する1個以上の attribute を含む object です。`path` を指定した場合、`value` はその target に追加する値です。

### `remove`

RFC 7644 §3.5.2.2 の `remove` では `path` が REQUIRED です。`path` が示す target の値を削除します。

### `replace`

RFC 7644 §3.5.2.3 の `replace` では `path` は OPTIONAL です。`path` を省略した場合、target は resource 自体であり、`value` は置換対象となる1個以上の attribute を含みます。指定した target attribute が存在しない場合、Service Provider はその operation を `add` として扱います（SHALL）。

## 4. Operations は array の順番に適用する

RFC 7644 §3.5.2 では、各 operation は request URI が示す同じ SCIM resource に対する1つの action です。operation は `Operations` array に現れる順番で逐次適用されます。ある operation の結果となる resource が、次の operation の target になります。

<pre class="mermaid">
flowchart TD
    A[Client: PATCH request] --> B[Service Provider]
    B --> C[Operation 1 を適用]
    C --> D[結果を次の target にする]
    D --> E[Operation 2 を適用]
    E --> F{すべて成功?}
    F -->|Yes| G[成功 response]
    F -->|No| H[元の resource を復元]
    H --> I[失敗 response]
</pre>

## 5. PATCH request 全体は atomic に扱う

RFC 7644 §3.5.2 は、operation 数にかかわらず PATCH request を atomic に扱うことを規定しています（SHALL）。1つの operation が error condition に遭遇した場合、元の SCIM resource を復元しなければなりません（MUST）。Service Provider は failure status と RFC 7644 §3.12 の JSON detail error response を返します（SHALL）。

成功時は、Service Provider は `200 OK` と resource 全体を response body に返す（MUST）か、適切な response headers とともに `204 No Content` を返すことができます（MAY）。ただし request に `attributes` parameter が指定されている場合は `200 OK` を返さなければなりません（MUST）。

## 6. schema と mutability の制約は各 operation に適用される

RFC 7644 §3.5.2 により、attribute に対する各 PATCH operation は RFC 7643 §2.2、§2.3 の mutability と schema に適合しなければなりません（MUST）。たとえば Client は `readOnly` または `immutable` attribute を変更してはなりません（MUST NOT）。ただし、値がまだ存在しない `immutable` attribute には値を `add` できます（MAY）。

この規則は PATCH の JSON 構造とは別に、operation を対象 resource に適用するときの schema constraint です。

## まとめ

SCIM PATCH の request body は `PatchOp` schema と1個以上の `Operations` で構成されます。各 operation は `op` を持ち、必要に応じて `path` と `value` を配置します。複数 operation は array の順序で同じ resource に逐次適用されますが、request 全体は atomic です。途中で1 operation が失敗した場合、Service Provider は元の resource を復元します。

## Primary sources

- RFC 7644, §3.5.2 “Modifying with PATCH”
- RFC 7644, §3.5.2.1 “Add Operation”
- RFC 7644, §3.5.2.2 “Remove Operation”
- RFC 7644, §3.5.2.3 “Replace Operation”
- RFC 7643, §2.2 “Attribute Data Types” and §2.3 “Attribute Characteristics”
