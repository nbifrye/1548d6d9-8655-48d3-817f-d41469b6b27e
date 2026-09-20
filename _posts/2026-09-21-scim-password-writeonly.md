---
layout: post
title: "SCIM password 属性：writeOnly と returned=never をどう扱うか"
date: 2026-09-21 08:39:00 +0900
categories: [provisioning, scim]
---

<!--
Article brief
- Type: Feature Deep Dive
- Reader: SCIM 2.0 の User provisioning を実装する Client / Service Provider の開発者
- Question: User.password を request に含めたとき、Service Provider はその値をどう扱い、response ではどう扱うのか
- Answer: password は optional / single-valued string / writeOnly / returned=never であり、設定・変更時の処理、保存・転送時の要件、response に返さない規則を区別できる
- Scope: RFC 7643 §4.1.1, §5, §8.7.1, §9.2 と RFC 7644 §3.5.2, §5, §7.2 に基づく User.password の representation と処理
- Out of scope: password policy の内容、認証方式、password strength の評価、credential recovery、SCIM 以外の password reset protocol
- Primary sources: RFC 7643; RFC 7643 Verified Erratum 8450; RFC 7644
- Diagram: Client が password を送信し、Service Provider が処理した後、password を含めず resource representation を返す flowchart
-->

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** SCIM 2.0 の User provisioning を実装する Client / Service Provider の開発者  
**この記事で伝えること:** `password` 属性の `writeOnly` / `returned=never` の意味と、Client が値を設定・変更したときに Service Provider が従う処理規則  
**扱わないこと:** password policy の具体的内容、認証方式、password strength の評価、credential recovery、SCIM 以外の password reset protocol

SCIM の `password` は User resource に定義された単一値の string 属性です。Client は初期 password の設定や既存 password の reset に使用できますが、Service Provider はその値を resource representation として返しません。

この記事では RFC 7643 §4.1.1 の `password` と、その schema representation、保存・転送時の規則に範囲を限定します。

## 1. password は writeOnly で returned=never

RFC 7643 §4.1.1 と §8.7.1 では、`password` の主要な attribute characteristic は次のように定義されています。

- `type`: `string`
- `multiValued`: `false`
- `required`: `false`
- `caseExact`: `false`
- `mutability`: `writeOnly`
- `returned`: `never`
- `uniqueness`: `none`

RFC 7643 §2.2 の `writeOnly` は、値を更新できる一方で、その値を返さない mutability です。`returned=never` は GET だけでなく、PUT、POST、PATCH の response でも属性値を返さないことを表します。

RFC 7643 §4.1.1 は、cleartext value と hashed value のどちらも Service Provider が返してはならない（SHALL NOT）と規定しています。また、`password` の mutability が `writeOnly` であるため、Service Provider は値をいかなる形式でも返してはなりません（MUST NOT）。

<pre class="mermaid">
flowchart TD
    A[Client が password を送信] --> B[Service Provider が値を処理]
    B --> C[User resource を更新]
    C --> D[password を含めず response]
</pre>

## 2. Client が password を設定する JSON の位置

`password` は User resource の JSON member です。初期値を設定する場合、RFC 7644 §3.3 の resource creation として `/Users` に POST する User representation に含められます。

以下は構造を示す**非規範的な例**です。`illustrative-password-value` は説明用の値であり、password policy 上の意味を持ちません。

```http
POST /Users HTTP/1.1
Host: example.com
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User"
  ],
  "userName": "illustrative-user",
  "password": "illustrative-password-value"
}
```

`password` は OPTIONAL なので、User creation request に常に含める必要はありません。

## 3. PATCH で password を変更する場合

RFC 7643 §5 の `ServiceProviderConfig.changePassword.supported` は、Service Provider が password change operation をサポートするかを示します。PATCH 自体の support は `ServiceProviderConfig.patch.supported` で示されます。

Service Provider が該当機能をサポートする場合、RFC 7644 §3.5.2 の PATCH request で `password` を対象にできます。以下は配置を示す**非規範的な例**です。

```http
PATCH /Users/illustrative-user-id HTTP/1.1
Host: example.com
Content-Type: application/scim+json

{
  "schemas": [
    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
  ],
  "Operations": [
    {
      "op": "replace",
      "path": "password",
      "value": "illustrative-new-password-value"
    }
  ]
}
```

RFC 7644 §3.5.2 は PATCH request body の `schemas` に `urn:ietf:params:scim:api:messages:2.0:PatchOp` を含めることを MUST とし、`Operations` を1件以上含む array とすることを MUST としています。各 operation object は `op` member をちょうど1つ持たなければなりません（MUST）。

## 4. 設定・変更された password を Service Provider が処理する規則

RFC 7643 §4.1.1 は、Client が cleartext password を設定または変更した場合、Service Provider が次の処理を行うことを SHOULD としています。

1. international language comparison のために値を prepare する。
2. server password policy に対して値を validate する。
3. 値が hashed または encrypted されるようにする。

3点目は RFC 7643 の Verified Erratum 8450 を反映した表現です。元の RFC 本文にある `encrypted (e.g., hashed)` という表現は、Verified Erratum 8450 で `hashed or encrypted` に訂正されています。

password policy の定義と enforcement は RFC 7643 の scope 外です。そのため、この仕様から特定の長さ、文字種、entropy、rotation rule を導くことはできません。

## 5. 保存する場合と別システムへ渡す場合

RFC 7643 §4.1.1 は、Service Provider が password value をローカルに保持する場合、その値を hash することを SHOULD としています。

Service Provider が cleartext value を直ちに別システムまたは programming interface に渡す場合、secured connection 上で直接渡さなければなりません（MUST）。また、provisioning workflow などのために一時的に persist する必要がある場合、その値を encryption などの方法で保護しなければなりません（MUST）。詳細な password と sensitive security data の扱いは RFC 7643 §9.2 に記載されています。

SCIM resource には password を含む sensitive information があり、RFC 7644 §7.2 は SCIM Client と Service Provider に transport-layer security mechanism の使用を要求しています（MUST）。

## 6. response では password を返さない

Client が password を送ったことと、Service Provider がその値を response に返すことは別です。`returned=never` なので、作成・更新後の User representation に `password` member を含めません。

以下は POST 後の構造を簡略化した**非規範的な例**です。

```http
HTTP/1.1 201 Created
Content-Type: application/scim+json
Location: https://example.com/Users/illustrative-user-id

{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User"
  ],
  "id": "illustrative-user-id",
  "userName": "illustrative-user"
}
```

ここで `password` がないことは、値が設定されなかったことを意味しません。SCIM representation 上、`password` は返されない属性だからです。

## 7. equality comparison は MAY

RFC 7643 §4.1.1 は、既存の stored hashed value がある場合に password の equality match をサポートしてもよい（MAY）としています。サポートする場合、Service Provider は比較対象を international language comparison 用に prepare し、filter value の salted hash を生成してローカルの値と比較します。

この MAY は、すべての Service Provider に password filter を実装することを要求するものではありません。

## まとめ

SCIM User の `password` は Client から設定・変更できる `writeOnly` 属性ですが、Service Provider から読み戻す属性ではありません。RFC 7643 は `returned=never` とし、cleartext value と hashed value の返却を禁止しています。

設定・変更時の処理、ローカル保持、別システムへの転送にはそれぞれ RFC 7643 §4.1.1 / §9.2 の規則が適用されます。password policy の具体的内容は仕様の scope 外です。

## 一次資料

- [RFC 7643 — System for Cross-domain Identity Management: Core Schema](https://www.rfc-editor.org/rfc/rfc7643.html) §2.2, §4.1.1, §5, §8.7.1, §9.2
- [RFC 7643 Inline Errata](https://www.rfc-editor.org/rfc/inline-errata/rfc7643.html) — Verified Erratum 8450
- [RFC 7644 — System for Cross-domain Identity Management: Protocol](https://www.rfc-editor.org/rfc/rfc7644.html) §3.3, §3.5.2, §5, §7.2
